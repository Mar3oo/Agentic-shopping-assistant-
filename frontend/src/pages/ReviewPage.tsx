import { useState } from 'react';
import { motion } from 'framer-motion';
import { Star, ThumbsUp, ThumbsDown, Lightbulb, Target, Link, TrendingUp } from 'lucide-react';
import { useApp, useDispatch } from '../store/AppContext';
import { useT } from '../i18n/translations';
import { startReview, chatReview, ApiClientError } from '../services/api';
import ChatBox from '../components/ChatBox';

function ReviewResult({ result }: { result: any }) {
  const { state } = useApp();
  const t = useT(state.lang);

  if (!result) return <div className="no-data">{t('noReviewData')}</div>;
  if (typeof result === 'string') return <p className="result-summary" style={{ fontSize:'var(--text-sm)' }}>{result}</p>;

  // data might be nested or direct
  const data = result.data || result;
  const { 
    summary, sentiment_score, value_for_money, 
    pros, cons, insights, best_for, sources 
  } = data;

  return (
    <div className="review-result-inline">
      {(sentiment_score || value_for_money) && (
        <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:12, marginBottom:20 }}>
          {sentiment_score && (
            <div className="sentiment-row" style={{ marginBottom:0, padding:'10px 14px' }}>
              <span className="sentiment-label" style={{ fontSize:'11px' }}><TrendingUp size={12} style={{ display:'inline', marginRight:6 }}/>{t('sentiment')}</span>
              <span className="sentiment-value" style={{ fontSize:'16px' }}>{sentiment_score}</span>
            </div>
          )}
          {value_for_money && (
            <div className="sentiment-row" style={{ marginBottom:0, padding:'10px 14px', '--c-primary-50':'var(--c-success-bg)', '--c-primary-200':'rgba(5,150,105,.2)', '--c-primary-600':'var(--c-success)' } as any}>
              <span className="sentiment-label" style={{ fontSize:'11px' }}>💰 {t('valueForMoney')}</span>
              <span className="sentiment-value" style={{ fontSize:'16px' }}>{value_for_money}</span>
            </div>
          )}
        </div>
      )}

      {summary && <p className="result-summary" style={{ fontSize: 'var(--text-sm)', marginBottom: 20 }}>{summary}</p>}

      {(Array.isArray(pros) && pros.length > 0 || Array.isArray(cons) && cons.length > 0) && (
        <div className="pros-cons-grid" style={{ marginBottom: 20 }}>
          {Array.isArray(pros) && pros.length > 0 && (
            <div className="pros-box" style={{ padding: '12px' }}>
              <div className="result-box-title" style={{ fontSize: '11px' }}><ThumbsUp size={12} /> {t('pros')}</div>
              <div className="result-list">{pros.map((p:string,i:number)=><div key={i} className="result-list-item" style={{ fontSize:'11px' }}>{p}</div>)}</div>
            </div>
          )}
          {Array.isArray(cons) && cons.length > 0 && (
            <div className="cons-box" style={{ padding: '12px' }}>
              <div className="result-box-title" style={{ fontSize: '11px' }}><ThumbsDown size={12} /> {t('cons')}</div>
              <div className="result-list">{cons.map((c:string,i:number)=><div key={i} className="result-list-item" style={{ fontSize:'11px' }}>{c}</div>)}</div>
            </div>
          )}
        </div>
      )}

      {Array.isArray(insights) && insights.length > 0 && (
        <div className="result-section">
          <div className="result-section-title" style={{ fontSize: '12px' }}><Lightbulb size={12} /> {t('insights')}</div>
          <div className="result-list">{insights.map((x:string,i:number)=>(
            <div key={i} className="result-list-item" style={{ fontSize:'11px' }}>{x}</div>
          ))}</div>
        </div>
      )}

      {Array.isArray(best_for) && best_for.length > 0 && (
        <div className="result-section">
          <div className="result-section-title" style={{ fontSize: '12px' }}><Target size={12} /> {t('bestFor')}</div>
          <div className="result-list">{best_for.map((x:string,i:number)=>(
            <div key={i} className="result-list-item" style={{ fontSize:'11px' }}>{x}</div>
          ))}</div>
        </div>
      )}

      {Array.isArray(sources) && sources.length > 0 && (
        <div className="result-section">
          <div className="result-section-title" style={{ fontSize: '12px' }}><Link size={12} /> {t('videoSources')}</div>
          <div className="source-chips">
            {sources.map((s:any,i:number)=>s.url
              ? <a key={i} href={s.url} target="_blank" rel="noopener noreferrer" className="source-chip" style={{ fontSize:'10px', padding:'4px 10px' }}><Link size={8} />{(s.title||`Source ${i+1}`).slice(0,30)}</a>
              : <span key={i} className="source-chip" style={{ fontSize:'10px', padding:'4px 10px' }}>{String(s.title||s).slice(0,30)}</span>)}
          </div>
        </div>
      )}
    </div>
  );
}

export default function ReviewPage() {
  const { state } = useApp();
  const dispatch  = useDispatch();
  const t = useT(state.lang);
  const [chatLoad, setChatLoad] = useState(false);
  const [error,    setError]    = useState('');

  const handleChat = async (msg: string) => {
    setChatLoad(true); setError('');
    try {
      if (!state.reviewSessionId) {
        dispatch({ type:'RESET_AGENT', payload:'review' });
        const res: any = await startReview(state.userId!, msg, state.lang);
        if (res.status !== 'success') throw new ApiClientError(res.message || 'Failed');
        dispatch({ type:'SET_REVIEW', payload:{
          reviewSessionId: res.session_id,
          reviewMessages: [{ role:'user', content:msg },{ role:'assistant', content:res.message||'', payload:res }],
        }});
        dispatch({ type:'SET_ACTIVE_SESSION', payload: res.session_id });
      } else {
        const res: any = await chatReview(state.userId!, state.reviewSessionId, msg, state.lang);
        if (res.status !== 'success') throw new ApiClientError(res.message || 'Failed');
        dispatch({ type:'APPEND_MSG', payload:{ agent:'review', msg:{ role:'assistant', content:res.message||'', payload:res }}});
        if (res.session_id) dispatch({ type:'SET_ACTIVE_SESSION', payload: res.session_id });
      }
    } catch(e) { setError(e instanceof ApiClientError ? e.message : String(e)); }
    finally { setChatLoad(false); }
  };

  const renderReviewPayload = (payload: any) => {
    if (payload.type === 'review' || payload.type === 'answer') {
      return (
        <div className="inline-payload-wrapper glass-card p-4 md:p-6 mt-2 overflow-hidden">
          <ReviewResult result={payload.data || payload} />
        </div>
      );
    }
    return null;
  };

  return (
    <div className="page-wrapper conversational-page">
      <motion.div className="page-header-row" initial={{ opacity:0, y:-12 }} animate={{ opacity:1, y:0 }} transition={{ duration:.4 }}>
        <div>
          <div className="page-eyebrow"><Star size={11} /> {t('review')}</div>
          <h1 className="page-title">{t('reviewTitle')}</h1>
          <p className="page-subtitle">{t('reviewDesc')}</p>
        </div>
        <div className="page-title-icon"><Star size={22} /></div>
      </motion.div>

      {error && <div className="alert-error" style={{ marginBottom: 20 }}>{error}</div>}

      <div className="conversational-chat-container">
        <ChatBox 
          messages={state.reviewMessages} 
          onSend={handleChat}
          placeholder={state.reviewSessionId ? t('followUpReview') : t('reviewPlaceholder')} 
          loading={chatLoad}
          renderPayload={renderReviewPayload}
          emptyText={t('noReviewData')} 
        />
      </div>
    </div>
  );
}
