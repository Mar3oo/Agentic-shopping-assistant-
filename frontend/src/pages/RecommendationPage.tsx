import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, LayoutGrid, Star, MessageSquare, X } from 'lucide-react';
import { useApp, useDispatch } from '../store/AppContext';
import { useT } from '../i18n/translations';
import { startRecommendation, chatRecommendation, startComparison, startReview, ApiClientError } from '../services/api';
import ProductCards from '../components/ProductCards';
import ChatBox from '../components/ChatBox';

function extractShortName(title: string): string {
  let s = (title || '').trim();
  for (const sep of ['|', ' - ', ' -', '- ']) {
    if (s.includes(sep)) { s = s.split(sep)[0].trim(); break; }
  }
  return s.split(' ').slice(0, 5).join(' ') || title;
}

export default function RecommendationPage() {
  const { state } = useApp();
  const dispatch  = useDispatch();
  const t = useT(state.lang);
  const [chatLoad, setChatLoad] = useState(false);
  const [error,    setError]    = useState('');
  const [selComp,  setSelComp]  = useState<string[]>([]);
  const [selRev,   setSelRev]   = useState('');
  const [showCompareModal, setShowCompareModal] = useState(false);
  const [showReviewModal, setShowReviewModal] = useState(false);

  const closeModals = () => {
    setShowCompareModal(false);
    setShowReviewModal(false);
  };

  const applyResp = (prompt: string, res: any, reset = false) => {
    if (res.session_id) {
      dispatch({ type:'SET_RECOMMENDATION', payload:{ recommendationSessionId: res.session_id }});
      dispatch({ type:'SET_ACTIVE_SESSION', payload: res.session_id });
    }
    const base = reset ? [] : state.recommendationMessages;
    let products = state.recommendationProducts;
    let suggestions = state.recommendationSuggestions;
    if (res.type === 'recommendations') {
      products = res.data?.products || [];
      suggestions = res.data?.suggestions || [];
    } else if (res.type === 'reset') { products = []; suggestions = []; }
    dispatch({ type:'SET_RECOMMENDATION', payload:{
      recommendationMessages: [...base, { role:'user', content:prompt }, { role:'assistant', content: res.message||'', payload:res }],
      recommendationProducts: products, recommendationSuggestions: suggestions,
    }});
  };

  const handleChat = async (msg: string) => {
    setChatLoad(true); setError('');
    try {
      if (!state.recommendationSessionId) {
        ['recommendation','comparison','review'].forEach(a => dispatch({ type:'RESET_AGENT', payload:a as any }));
        const res: any = await startRecommendation(state.userId!, msg, state.lang);
        if (res.status !== 'success') throw new ApiClientError(res.message || 'Failed');
        applyResp(msg, res, true);
      } else {
        const res: any = await chatRecommendation(state.userId!, state.recommendationSessionId, msg, state.lang);
        if (res.status !== 'success') throw new ApiClientError(res.message || 'Failed');
        applyResp(msg, res);
      }
    } catch(e) { setError(e instanceof ApiClientError ? e.message : String(e)); }
    finally { setChatLoad(false); }
  };

  const handleCompare = async () => {
    if (selComp.length !== 2) return;
    const q = `compare ${extractShortName(selComp[0])} vs ${extractShortName(selComp[1])}`;
    try {
      const res: any = await startComparison(state.userId!, q, state.lang);
      if (res.status !== 'success') throw new ApiClientError(res.message || 'Failed');
      dispatch({ type:'SET_COMPARISON', payload:{
        comparisonSessionId: res.session_id, comparisonResult: res.data,
        comparisonMessages: [{ role:'user', content:q },{ role:'assistant', content:res.message||'', payload:res }],
      }});
      dispatch({ type:'SET_ACTIVE_SESSION', payload: res.session_id });
      dispatch({ type:'SET_PAGE', payload:'comparison' });
    } catch(e) { setError(e instanceof ApiClientError ? e.message : String(e)); }
  };

  const handleReview = async () => {
    const product = selRev || state.recommendationProducts[0]?.title;
    if (!product) return;
    const q = `${product} reviews`;
    try {
      const res: any = await startReview(state.userId!, q, state.lang);
      if (res.status !== 'success') throw new ApiClientError(res.message || 'Failed');
      dispatch({ type:'SET_REVIEW', payload:{
        reviewSessionId: res.session_id, reviewResult: res.data,
        reviewMessages: [{ role:'user', content:q },{ role:'assistant', content:res.message||'', payload:res }],
      }});
      dispatch({ type:'SET_ACTIVE_SESSION', payload: res.session_id });
      dispatch({ type:'SET_PAGE', payload:'review' });
    } catch(e) { setError(e instanceof ApiClientError ? e.message : String(e)); }
  };

  const products = state.recommendationProducts;
  const titles   = products.map(p => p.title || '');

  const renderRecommendationPayload = (payload: any) => {
    if (payload.type === 'recommendations' && payload.data?.products) {
      return (
        <div className="inline-payload-wrapper">
          <ProductCards products={payload.data.products} />
          
          <div className="payload-actions-row mt-4">
            <button className="btn btn-sm btn-outline" onClick={() => setShowCompareModal(true)}>
              <LayoutGrid size={13} /> {t('compareProducts')}
            </button>
            <button className="btn btn-sm btn-outline" onClick={() => setShowReviewModal(true)}>
              <Star size={13} /> {t('reviewProduct')}
            </button>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="page-wrapper conversational-page">
      {/* Header */}
      <motion.div className="page-header-row" initial={{ opacity:0, y:-12 }} animate={{ opacity:1, y:0 }} transition={{ duration:.4 }}>
        <div>
          <div className="page-eyebrow"><Sparkles size={11} /> AI Assistant</div>
          <h1 className="page-title">{t('aiShoppingAssistant')}</h1>
          <p className="page-subtitle">{t('chatWith')} <strong style={{ color:'var(--c-primary-600)' }}>RECO</strong> {t('toFind')}</p>
        </div>
        <div className="page-title-icon"><Sparkles size={22} /></div>
      </motion.div>

      {error && <motion.div className="alert-error" initial={{ opacity:0 }} animate={{ opacity:1 }}>{error}</motion.div>}

      {/* Chat Flow */}
      <div className="conversational-chat-container">
        <ChatBox 
          messages={state.recommendationMessages} 
          onSend={handleChat}
          placeholder={state.recommendationSessionId ? t('askRefinements') : t('whatLookingForPlaceholder')} 
          loading={chatLoad}
          renderPayload={renderRecommendationPayload}
        />
      </div>

      {/* Modals for actions inside payload */}
      <AnimatePresence>
        {showCompareModal && (
          <motion.div className="modal-backdrop" style={{ position:'fixed', inset:0, zIndex:250, background:'rgba(0,0,0,0.45)', display:'grid', placeItems:'center', padding:20 }}
            initial={{ opacity:0 }} animate={{ opacity:1 }} exit={{ opacity:0 }} onClick={closeModals}>
            <motion.div className="glass-card" style={{ width:'min(760px,100%)', maxHeight:'calc(100vh - 80px)', overflowY:'auto', padding:24, position:'relative' }}
              initial={{ scale:0.98, y:16, opacity:0 }} animate={{ scale:1, y:0, opacity:1 }} exit={{ scale:0.96, y:12, opacity:0 }} onClick={e => e.stopPropagation()}>
              <div className="modal-header" style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:16 }}>
                <div>
                  <div className="action-card-title">{t('compareProducts')}</div>
                  <div className="action-card-desc" style={{ marginTop:6 }}>{t('selectToCompare')}</div>
                </div>
                <button className="btn-icon" onClick={closeModals}><X size={16} /></button>
              </div>
              <div className="pick-list" style={{ maxHeight:320, overflowY:'auto', marginBottom:18 }}>
                {titles.map(title => {
                  const sel = selComp.includes(title);
                  return (
                    <div key={title} className={`pick-item ${sel ? 'sel' : ''}`}
                      onClick={() => setSelComp(prev => sel ? prev.filter(t => t !== title) : prev.length < 2 ? [...prev, title] : prev)}>
                      <span className="pick-box">{sel && <svg width="9" height="8" viewBox="0 0 9 8"><polyline points="1,4 3.5,6.5 8,1" fill="none" stroke="#fff" strokeWidth="1.5" strokeLinecap="round"/></svg>}</span>
                      <span className="pick-label">{title}</span>
                    </div>
                  );
                })}
              </div>
              <div style={{ display:'flex', gap:12, flexWrap:'wrap', alignItems:'center' }}>
                <button className="btn btn-primary btn-full" type="button" onClick={() => { handleCompare(); closeModals(); }} disabled={selComp.length !== 2}>
                  <LayoutGrid size={14} /> {t('compareSelected')}
                </button>
                {selComp.length !== 2 && <div style={{ color:'var(--c-text-5)' }}>{t('selectExactly2')}</div>}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {showReviewModal && (
          <motion.div className="modal-backdrop" style={{ position:'fixed', inset:0, zIndex:250, background:'rgba(0,0,0,0.45)', display:'grid', placeItems:'center', padding:20 }}
            initial={{ opacity:0 }} animate={{ opacity:1 }} exit={{ opacity:0 }} onClick={closeModals}>
            <motion.div className="glass-card" style={{ width:'min(760px,100%)', maxHeight:'calc(100vh - 80px)', overflowY:'auto', padding:24, position:'relative' }}
              initial={{ scale:0.98, y:16, opacity:0 }} animate={{ scale:1, y:0, opacity:1 }} exit={{ scale:0.96, y:12, opacity:0 }} onClick={e => e.stopPropagation()}>
              <div className="modal-header" style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:16 }}>
                <div>
                  <div className="action-card-title">{t('reviewProduct')}</div>
                  <div className="action-card-desc" style={{ marginTop:6 }}>{t('pickToReview')}</div>
                </div>
                <button className="btn-icon" onClick={closeModals}><X size={16} /></button>
              </div>
              <div className="pick-list" style={{ maxHeight:320, overflowY:'auto', marginBottom:18 }}>
                {titles.map(title => {
                  const sel = (selRev || titles[0]) === title;
                  return (
                    <div key={title} className={`pick-item ${sel ? 'sel' : ''}`} onClick={() => setSelRev(title)}>
                      <span className="pick-radio-btn" />
                      <span className="pick-label">{title}</span>
                    </div>
                  );
                })}
              </div>
              <div style={{ display:'flex', gap:12, alignItems:'center' }}>
                <button className="btn btn-primary btn-full" type="button" onClick={() => { handleReview(); closeModals(); }}>
                  <Star size={14} /> {t('startReview')}
                </button>
                {!selRev && <div style={{ color:'var(--c-text-5)' }}>{t('pickToReview')}</div>}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

