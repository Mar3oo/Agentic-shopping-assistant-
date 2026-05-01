import { useState } from 'react';
import { motion } from 'framer-motion';
import { Sparkles, LayoutGrid, Star, Send, MessageSquare } from 'lucide-react';
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
  const [query,    setQuery]    = useState('');
  const [loading,  setLoading]  = useState(false);
  const [chatLoad, setChatLoad] = useState(false);
  const [error,    setError]    = useState('');
  const [selComp,  setSelComp]  = useState<string[]>([]);
  const [selRev,   setSelRev]   = useState('');

  const applyResp = (prompt: string, res: any, reset = false) => {
    if (res.session_id) dispatch({ type:'SET_RECOMMENDATION', payload:{ recommendationSessionId: res.session_id }});
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

  const handleStart = async () => {
    if (!query.trim()) return;
    setLoading(true); setError('');
    ['recommendation','comparison','review'].forEach(a => dispatch({ type:'RESET_AGENT', payload:a as any }));
    try {
      const res: any = await startRecommendation(state.userId!, query);
      if (res.status !== 'success') throw new ApiClientError(res.message || 'Failed');
      applyResp(query, res, true); setQuery('');
    } catch(e) { setError(e instanceof ApiClientError ? e.message : String(e)); }
    finally { setLoading(false); }
  };

  const handleChat = async (msg: string) => {
    if (!state.recommendationSessionId) return;
    setChatLoad(true);
    try {
      const res: any = await chatRecommendation(state.userId!, state.recommendationSessionId, msg);
      if (res.status !== 'success') throw new ApiClientError(res.message || 'Failed');
      applyResp(msg, res);
    } catch(e) { setError(e instanceof ApiClientError ? e.message : String(e)); }
    finally { setChatLoad(false); }
  };

  const handleCompare = async () => {
    if (selComp.length !== 2) return;
    const q = `compare ${extractShortName(selComp[0])} vs ${extractShortName(selComp[1])}`;
    try {
      const res: any = await startComparison(state.userId!, q);
      if (res.status !== 'success') throw new ApiClientError(res.message || 'Failed');
      dispatch({ type:'SET_COMPARISON', payload:{
        comparisonSessionId: res.session_id, comparisonResult: res.data,
        comparisonMessages: [{ role:'user', content:q },{ role:'assistant', content:res.message||'', payload:res }],
      }});
      dispatch({ type:'SET_PAGE', payload:'comparison' });
    } catch(e) { setError(e instanceof ApiClientError ? e.message : String(e)); }
  };

  const handleReview = async () => {
    const product = selRev || state.recommendationProducts[0]?.title;
    if (!product) return;
    const q = `${product} reviews`;
    try {
      const res: any = await startReview(state.userId!, q);
      if (res.status !== 'success') throw new ApiClientError(res.message || 'Failed');
      dispatch({ type:'SET_REVIEW', payload:{
        reviewSessionId: res.session_id, reviewResult: res.data,
        reviewMessages: [{ role:'user', content:q },{ role:'assistant', content:res.message||'', payload:res }],
      }});
      dispatch({ type:'SET_PAGE', payload:'review' });
    } catch(e) { setError(e instanceof ApiClientError ? e.message : String(e)); }
  };

  const products = state.recommendationProducts;
  const titles   = products.map(p => p.title || '');

  return (
    <div className="page-wrapper">
      {/* Header */}
      <motion.div className="page-header-row" initial={{ opacity:0, y:-12 }} animate={{ opacity:1, y:0 }} transition={{ duration:.4 }}>
        <div>
          <div className="page-eyebrow"><Sparkles size={11} /> AI Assistant</div>
          <h1 className="page-title">{t('aiShoppingAssistant')}</h1>
          <p className="page-subtitle">{t('chatWith')} <strong style={{ color:'var(--c-primary-600)' }}>RECO</strong> {t('toFind')}</p>
        </div>
        <div className="page-title-icon"><Sparkles size={22} /></div>
      </motion.div>

      {/* Prompt */}
      <motion.div className="glass-card prompt-card" initial={{ opacity:0, y:8 }} animate={{ opacity:1, y:0 }} transition={{ delay:.1 }}>
        <div className="prompt-row">
          <input className="prompt-input" placeholder={t('whatLookingForPlaceholder')} value={query}
            onChange={e=>setQuery(e.target.value)} onKeyDown={e=>e.key==='Enter'&&handleStart()} disabled={loading} />
          <motion.button className="btn btn-primary btn-lg" onClick={handleStart} disabled={loading||!query.trim()}
            whileHover={{ scale:1.02 }} whileTap={{ scale:.97 }}>
            {loading ? <span className="spinner" /> : <><Send size={15} /> {t('getRecommendations')}</>}
          </motion.button>
        </div>
      </motion.div>

      {error && <motion.div className="alert-error" initial={{ opacity:0 }} animate={{ opacity:1 }}>{error}</motion.div>}

      {/* Products */}
      {products.length > 0 && (
        <motion.div initial={{ opacity:0, y:16 }} animate={{ opacity:1, y:0 }} transition={{ delay:.15 }}>
          <ProductCards products={products} title={t('recommendedProducts')} />
        </motion.div>
      )}

      {/* Actions */}
      {products.length >= 2 && (
        <motion.div className="actions-two-col" initial={{ opacity:0, y:12 }} animate={{ opacity:1, y:0 }} transition={{ delay:.2 }}>
          {/* Compare */}
          <div className="glass-card action-card">
            <div className="action-card-header">
              <div className="action-icon-box"><LayoutGrid size={18} /></div>
              <div>
                <div className="action-card-title">{t('compareProducts')}</div>
                <div className="action-card-desc">{t('selectToCompare')}</div>
              </div>
            </div>
            <div className="pick-list">
              {titles.map(title => {
                const sel = selComp.includes(title);
                return (
                  <div key={title} className={`pick-item ${sel?'sel':''}`}
                    onClick={() => setSelComp(prev => sel ? prev.filter(t=>t!==title) : prev.length<2 ? [...prev,title] : prev)}>
                    <span className="pick-box">{sel && <svg width="9" height="8" viewBox="0 0 9 8"><polyline points="1,4 3.5,6.5 8,1" fill="none" stroke="#fff" strokeWidth="1.5" strokeLinecap="round"/></svg>}</span>
                    <span className="pick-label">{title}</span>
                  </div>
                );
              })}
            </div>
            {selComp.length === 2
              ? <motion.button className="btn btn-primary btn-full" onClick={handleCompare} whileTap={{ scale:.97 }}>
                  <LayoutGrid size={14} /> {t('compareSelected')}
                </motion.button>
              : <p className="hint-text">{t('atLeast2')}</p>
            }
          </div>

          {/* Review */}
          <div className="glass-card action-card">
            <div className="action-card-header">
              <div className="action-icon-box"><Star size={18} /></div>
              <div>
                <div className="action-card-title">{t('reviewProduct')}</div>
                <div className="action-card-desc">{t('pickToReview')}</div>
              </div>
            </div>
            <div className="pick-list">
              {titles.map(title => {
                const sel = (selRev || titles[0]) === title;
                return (
                  <div key={title} className={`pick-item ${sel?'sel':''}`} onClick={() => setSelRev(title)}>
                    <span className="pick-radio-btn" />
                    <span className="pick-label">{title}</span>
                  </div>
                );
              })}
            </div>
            <motion.button className="btn btn-primary btn-full" onClick={handleReview} whileTap={{ scale:.97 }}>
              <Star size={14} /> {t('startReview')}
            </motion.button>
          </div>
        </motion.div>
      )}

      {/* Chat */}
      <motion.div className="glass-card chat-section" initial={{ opacity:0, y:8 }} animate={{ opacity:1, y:0 }} transition={{ delay:.25 }}>
        <div className="chat-section-title"><MessageSquare size={15} /> {t('chatHistory')}</div>
        <ChatBox messages={state.recommendationMessages} onSend={handleChat}
          placeholder={t('askRefinements')} loading={chatLoad}
          emptyText={t('noConversation')} disabled={!state.recommendationSessionId} />
      </motion.div>
    </div>
  );
}
