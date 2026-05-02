import { useState } from 'react';
import { motion } from 'framer-motion';
import { Star, Send, MessageSquare, ThumbsUp, ThumbsDown, Lightbulb, Target, ChevronDown, ChevronUp, Link, TrendingUp } from 'lucide-react';
import { useApp, useDispatch } from '../store/AppContext';
import { useT } from '../i18n/translations';
import { startReview, chatReview, ApiClientError } from '../services/api';
import ChatBox from '../components/ChatBox';

function ReviewResult({ result }: { result: any }) {
  const { state } = useApp();
  const t = useT(state.lang);
  const [expanded, setExpanded] = useState(false);
  if (!result) return <div className="no-data">{t('noReviewData')}</div>;
  const { summary, sentiment_score, value_for_money, pros, cons, insights, best_for, sources } = result;
  return (
    <div>
      {(sentiment_score || value_for_money) && (
        <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:12, marginBottom:20 }}>
          {sentiment_score && (
            <div className="sentiment-row">
              <span className="sentiment-label"><TrendingUp size={14} style={{ display:'inline', marginRight:6 }}/>{t('sentiment')}</span>
              <span className="sentiment-value">{sentiment_score}</span>
            </div>
          )}
          {value_for_money && (
            <div className="sentiment-row" style={{ '--c-primary-50':'var(--c-success-bg)', '--c-primary-200':'rgba(5,150,105,.2)', '--c-primary-600':'var(--c-success)' } as any}>
              <span className="sentiment-label">💰 {t('valueForMoney')}</span>
              <span className="sentiment-value">{value_for_money}</span>
            </div>
          )}
        </div>
      )}
      {summary && <p className="result-summary">{summary}</p>}
      {(Array.isArray(pros) && pros.length > 0 || Array.isArray(cons) && cons.length > 0) && (
        <div className="pros-cons-grid">
          {Array.isArray(pros) && pros.length > 0 && (
            <div className="pros-box">
              <div className="result-box-title"><ThumbsUp size={14} /> {t('pros')}</div>
              <div className="result-list">{pros.map((p:string,i:number)=><div key={i} className="result-list-item">{p}</div>)}</div>
            </div>
          )}
          {Array.isArray(cons) && cons.length > 0 && (
            <div className="cons-box">
              <div className="result-box-title"><ThumbsDown size={14} /> {t('cons')}</div>
              <div className="result-list">{cons.map((c:string,i:number)=><div key={i} className="result-list-item">{c}</div>)}</div>
            </div>
          )}
        </div>
      )}
      {Array.isArray(insights) && insights.length > 0 && (
        <div className="result-section">
          <div className="result-section-title"><Lightbulb size={14} /> {t('insights')}</div>
          <div className="result-list">{insights.map((x:string,i:number)=><div key={i} className="result-list-item">{x}</div>)}</div>
        </div>
      )}
      {Array.isArray(best_for) && best_for.length > 0 && (
        <div className="result-section">
          <div className="result-section-title"><Target size={14} /> {t('bestFor')}</div>
          <div className="result-list">{best_for.map((x:string,i:number)=><div key={i} className="result-list-item">{x}</div>)}</div>
        </div>
      )}
      {Array.isArray(sources) && sources.length > 0 && (
        <div className="result-section">
          <div className="result-section-title"><Link size={14} /> {t('videoSources')}</div>
          <div className="source-chips">{sources.map((s:any,i:number)=>s.url
            ? <a key={i} href={s.url} target="_blank" rel="noopener noreferrer" className="source-chip"><Link size={10} />{(s.title||`Source ${i+1}`).slice(0,30)}</a>
            : <span key={i} className="source-chip">{String(s.title||s).slice(0,30)}</span>)}</div>
        </div>
      )}
      <button className="expand-toggle" onClick={()=>setExpanded(!expanded)}>
        {expanded?<ChevronUp size={13}/>:<ChevronDown size={13}/>} {t('rawPayload')}
      </button>
      {expanded && <pre className="raw-json">{JSON.stringify(result,null,2)}</pre>}
    </div>
  );
}

export default function ReviewPage() {
  const { state } = useApp();
  const dispatch  = useDispatch();
  const t = useT(state.lang);
  const [query,    setQuery]    = useState('');
  const [loading,  setLoading]  = useState(false);
  const [chatLoad, setChatLoad] = useState(false);
  const [error,    setError]    = useState('');

  const handleStart = async () => {
    if (!query.trim()) return;
    setLoading(true); setError('');
    try {
      const res: any = await startReview(state.userId!, query);
      if (res.status !== 'success') throw new ApiClientError(res.message || 'Failed');
      dispatch({ type:'SET_REVIEW', payload:{
        reviewSessionId: res.session_id, reviewResult: res.data,
        reviewMessages: [{ role:'user', content:query },{ role:'assistant', content:res.message||'', payload:res }],
      }});
      setQuery('');
    } catch(e) { setError(e instanceof ApiClientError ? e.message : String(e)); }
    finally { setLoading(false); }
  };

  const handleChat = async (msg: string) => {
    if (!state.reviewSessionId) return;
    setChatLoad(true);
    try {
      dispatch({ type:'APPEND_MSG', payload:{ agent:'review', msg:{ role:'user', content:msg }}});
      const res: any = await chatReview(state.userId!, state.reviewSessionId, msg);
      if (res.status !== 'success') throw new ApiClientError(res.message || 'Failed');
      dispatch({ type:'APPEND_MSG', payload:{ agent:'review', msg:{ role:'assistant', content:res.message||'', payload:res }}});
      dispatch({ type:'SET_REVIEW', payload:{ reviewResult: res.data }});
    } catch(e) { setError(e instanceof ApiClientError ? e.message : String(e)); }
    finally { setChatLoad(false); }
  };

  return (
    <div className="page-wrapper">
      <motion.div className="page-header-row" initial={{ opacity:0, y:-12 }} animate={{ opacity:1, y:0 }} transition={{ duration:.4 }}>
        <div>
          <div className="page-eyebrow"><Star size={11} /> Reviews</div>
          <h1 className="page-title">{t('reviewTitle')}</h1>
          <p className="page-subtitle">{t('reviewDesc')}</p>
        </div>
        <div className="page-title-icon"><Star size={22} /></div>
      </motion.div>

      <motion.div className="glass-card prompt-card" initial={{ opacity:0, y:8 }} animate={{ opacity:1, y:0 }} transition={{ delay:.1 }}>
        <div className="prompt-row">
          <input className="prompt-input" placeholder={t('reviewPlaceholder')} value={query}
            onChange={e=>setQuery(e.target.value)} onKeyDown={e=>e.key==='Enter'&&handleStart()} disabled={loading} />
          <motion.button className="btn btn-primary btn-lg" onClick={handleStart} disabled={loading||!query.trim()} whileTap={{ scale:.97 }}>
            {loading ? <span className="spinner" /> : <><Send size={15} /> {t('startReview')}</>}
          </motion.button>
        </div>
      </motion.div>

      {error && <div className="alert-error">{error}</div>}

      {state.reviewResult && (
        <motion.div className="glass-card result-card" initial={{ opacity:0, y:12 }} animate={{ opacity:1, y:0 }}>
          <ReviewResult result={state.reviewResult} />
        </motion.div>
      )}

      <motion.div className="glass-card chat-section" initial={{ opacity:0, y:8 }} animate={{ opacity:1, y:0 }} transition={{ delay:.2 }}>
        <div className="chat-section-title"><MessageSquare size={15} /> {t('chatHistory')}</div>
        <ChatBox messages={state.reviewMessages} onSend={handleChat}
          placeholder={t('followUpReview')} loading={chatLoad}
          emptyText={t('noReviewData')} disabled={!state.reviewSessionId} />
      </motion.div>
    </div>
  );
}
