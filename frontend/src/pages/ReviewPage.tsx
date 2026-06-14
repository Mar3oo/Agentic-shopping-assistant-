import { useState } from 'react';
import { motion } from 'framer-motion';
import { Star, ThumbsUp, ThumbsDown, Lightbulb, Target, Link, TrendingUp, Smile, Coins } from 'lucide-react';
import { useApp, useDispatch } from '../store/AppContext';
import { useT } from '../i18n/translations';
import { startReview, chatReview, ApiClientError } from '../services/api';
import ChatBox from '../components/ChatBox';

function ReviewResult({ result }: { result: any }) {
  const { state } = useApp();
  const t = useT(state.lang);

  if (!result) return <div className="no-data">{t('noReviewData')}</div>;
  if (typeof result === 'string') {
    return (
      <div className="review-summary-container">
        <p className="review-summary-text">{result}</p>
      </div>
    );
  }

  // Robustly extract data - might be wrapped in .data or direct
  const data = (result.data || result) as any;
  const { 
    summary, sentiment_score, value_for_money, 
    pros, cons, insights, best_for, sources,
    product_display_name
  } = data;


  const sentimentClass = (score: string) => {
    const s = score?.toLowerCase() || '';
    if (s.includes('positive') || s.includes('good') || s.includes('great')) return 'sentiment-positive';
    if (s.includes('negative') || s.includes('bad') || s.includes('poor')) return 'sentiment-negative';
    return 'sentiment-neutral';
  };

  return (
    <div className="review-result-inline">
      {product_display_name && (
        <div className="review-product-header">
          <h2 className="review-product-name">{product_display_name}</h2>
        </div>
      )}

      {(sentiment_score || value_for_money) && (
        <div className="review-metrics-grid">
          {sentiment_score && (
            <div className={`review-metric-card sentiment-card ${sentimentClass(sentiment_score)}`}>
              <div className="metric-label-row">
                <Smile size={14} className="metric-icon" />
                <span className="metric-label">{t('sentiment')}</span>
              </div>
              <span className="metric-value">{sentiment_score}</span>
            </div>
          )}
          {value_for_money && (
            <div className="review-metric-card value-card">
              <div className="metric-label-row">
                <Coins size={14} className="metric-icon" />
                <span className="metric-label">{t('valueForMoney')}</span>
              </div>
              <span className="metric-value">{value_for_money}</span>
            </div>
          )}
        </div>
      )}


      {(Array.isArray(pros) && pros.length > 0 || Array.isArray(cons) && cons.length > 0) && (
        <div className="pros-cons-grid">
          {Array.isArray(pros) && pros.length > 0 && (
            <div className="pros-box shadow-sm">
              <div className="result-box-title"><ThumbsUp size={16} /> {t('pros')}</div>
              <div className="result-list mt-1">
                {pros.map((p:string, i:number) => (
                  <div key={i} className="result-list-item">{p}</div>
                ))}
              </div>
            </div>
          )}
          {Array.isArray(cons) && cons.length > 0 && (
            <div className="cons-box shadow-sm">
              <div className="result-box-title"><ThumbsDown size={16} /> {t('cons')}</div>
              <div className="result-list mt-1">
                {cons.map((c:string, i:number) => (
                  <div key={i} className="result-list-item">{c}</div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {Array.isArray(insights) && insights.length > 0 && (
        <div className="result-section">
          <div className="result-section-title text-[var(--c-accent-2)]"><Lightbulb size={16} /> {t('insights')}</div>
          <div className="result-list mt-3 gap-3">
            {insights.map((x:string, i:number) => (
              <div key={i} className="tapped-list-item">
                {x}
              </div>
            ))}
          </div>
        </div>
      )}

      {Array.isArray(best_for) && best_for.length > 0 && (
        <div className="result-section">
          <div className="result-section-title text-[var(--c-primary-500)]"><Target size={16} /> {t('bestFor')}</div>
          <div className="result-list mt-3 gap-3">
            {best_for.map((x:string, i:number) => (
              <div key={i} className="tapped-list-item">
                {x}
              </div>
            ))}
          </div>
        </div>
      )}


      {Array.isArray(sources) && sources.length > 0 && (
        <div className="review-sources-section">
          <div className="result-section-title opacity-60"><Link size={14} /> {t('videoSources')}</div>
          <div className="source-chips mt-4">
            {sources.map((s:any, i:number) => (
              <a key={i} href={s.url} target="_blank" rel="noopener noreferrer" className="source-chip transition-all hover:scale-[1.02]">
                <Link size={10} /> {(s.title || `Source ${i+1}`).slice(0, 45)}...
              </a>
            ))}
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
    const userMsg: ChatMessage = { role: 'user', content: msg };
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
        // Immediate feedback: append user message locally
        dispatch({ type: 'APPEND_MSG', payload: { agent: 'review', msg: userMsg } });
        
        const res: any = await chatReview(state.userId!, state.reviewSessionId, msg, state.lang);
        if (res.status !== 'success') throw new ApiClientError(res.message || 'Failed');
        
        // Append assistant response
        dispatch({ type:'APPEND_MSG', payload:{ agent:'review', msg:{ role:'assistant', content:res.message||'', payload:res }}});
        if (res.session_id) dispatch({ type:'SET_ACTIVE_SESSION', payload: res.session_id });
      }
    } catch(e) { setError(e instanceof ApiClientError ? e.message : String(e)); }
    finally { setChatLoad(false); }
  };


  const renderReviewPayload = (payload: any) => {
    if (payload.type === 'review') {
      return (
        <div className="inline-payload-wrapper glass-card p-6 md:p-10 mt-4 overflow-hidden">
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
