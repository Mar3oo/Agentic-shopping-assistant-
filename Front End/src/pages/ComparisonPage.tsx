import { useState } from 'react';
import { motion } from 'framer-motion';
import { LayoutGrid, Send, MessageSquare, ChevronDown, ChevronUp, Link } from 'lucide-react';
import { useApp, useDispatch } from '../store/AppContext';
import { useT } from '../i18n/translations';
import { startComparison, chatComparison, ApiClientError } from '../services/api';
import ChatBox from '../components/ChatBox';

function CompResult({ result }: { result: Record<string, unknown> | null }) {
  const { state } = useApp();
  const t = useT(state.lang);
  const [expanded, setExpanded] = useState(false);
  if (!result) return <div className="no-data">{t('noComparisonData')}</div>;
  const { summary, comparison_table, key_differences, recommendation, sources } = result as any;
  return (
    <div>
      {summary && <p className="result-summary">{summary}</p>}
      {Array.isArray(comparison_table) && comparison_table.length > 0 && (
        <div className="comp-table-wrap">
          <table className="comp-table">
            <thead><tr>{Object.keys(comparison_table[0]).map(k=><th key={k}>{k}</th>)}</tr></thead>
            <tbody>{comparison_table.map((row:any,i:number)=>(
              <tr key={i}>{Object.values(row).map((v:any,j:number)=><td key={j}>{String(v)}</td>)}</tr>
            ))}</tbody>
          </table>
        </div>
      )}
      {Array.isArray(key_differences) && key_differences.length > 0 && (
        <div className="result-section">
          <div className="result-section-title">🔀 {t('keyDifferences')}</div>
          <div className="result-list">{key_differences.map((d:string,i:number)=>(
            <div key={i} className="result-list-item">{d}</div>
          ))}</div>
        </div>
      )}
      {recommendation && (
        <div className="result-section">
          <div className="result-section-title">🏆 {t('recommendation')}</div>
          {Object.entries(recommendation).map(([k,v])=>(
            <div key={k} style={{ marginBottom:8 }}>
              <strong style={{ fontSize:'var(--text-sm)', textTransform:'capitalize' }}>{k.replace(/_/g,' ')}</strong>
              {Array.isArray(v) ? <div className="result-list" style={{ marginTop:4 }}>{(v as string[]).map((x,i)=><div key={i} className="result-list-item">{x}</div>)}</div>
              : <p style={{ fontSize:'var(--text-sm)', color:'var(--c-text-2)', marginTop:4 }}>{String(v)}</p>}
            </div>
          ))}
        </div>
      )}
      {Array.isArray(sources) && sources.length > 0 && (
        <div className="result-section">
          <div className="result-section-title"><Link size={14} /> {t('sources')}</div>
          <div className="source-chips">{sources.map((s:any,i:number)=>s.url
            ? <a key={i} href={s.url} target="_blank" rel="noopener noreferrer" className="source-chip"><Link size={10} />Source {i+1}</a>
            : null)}</div>
        </div>
      )}
      <button className="expand-toggle" onClick={()=>setExpanded(!expanded)}>
        {expanded ? <ChevronUp size={13}/> : <ChevronDown size={13}/>} {t('rawPayload')}
      </button>
      {expanded && <pre className="raw-json">{JSON.stringify(result,null,2)}</pre>}
    </div>
  );
}

export default function ComparisonPage() {
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
      const res: any = await startComparison(state.userId!, query);
      if (res.status !== 'success') throw new ApiClientError(res.message || 'Failed');
      dispatch({ type:'SET_COMPARISON', payload:{
        comparisonSessionId: res.session_id, comparisonResult: res.data,
        comparisonMessages: [{ role:'user', content:query },{ role:'assistant', content:res.message||'', payload:res }],
      }});
      setQuery('');
    } catch(e) { setError(e instanceof ApiClientError ? e.message : String(e)); }
    finally { setLoading(false); }
  };

  const handleChat = async (msg: string) => {
    if (!state.comparisonSessionId) return;
    setChatLoad(true);
    try {
      dispatch({ type:'APPEND_MSG', payload:{ agent:'comparison', msg:{ role:'user', content:msg }}});
      const res: any = await chatComparison(state.userId!, state.comparisonSessionId, msg);
      if (res.status !== 'success') throw new ApiClientError(res.message || 'Failed');
      dispatch({ type:'APPEND_MSG', payload:{ agent:'comparison', msg:{ role:'assistant', content:res.message||'', payload:res }}});
      dispatch({ type:'SET_COMPARISON', payload:{ comparisonResult: res.data }});
    } catch(e) { setError(e instanceof ApiClientError ? e.message : String(e)); }
    finally { setChatLoad(false); }
  };

  return (
    <div className="page-wrapper">
      <motion.div className="page-header-row" initial={{ opacity:0, y:-12 }} animate={{ opacity:1, y:0 }} transition={{ duration:.4 }}>
        <div>
          <div className="page-eyebrow"><LayoutGrid size={11} /> Compare</div>
          <h1 className="page-title">{t('compareTitle')}</h1>
          <p className="page-subtitle">{t('comparisonDesc')}</p>
        </div>
        <div className="page-title-icon"><LayoutGrid size={22} /></div>
      </motion.div>

      <motion.div className="glass-card prompt-card" initial={{ opacity:0, y:8 }} animate={{ opacity:1, y:0 }} transition={{ delay:.1 }}>
        <div className="prompt-row">
          <input className="prompt-input" placeholder={t('comparisonPlaceholder')} value={query}
            onChange={e=>setQuery(e.target.value)} onKeyDown={e=>e.key==='Enter'&&handleStart()} disabled={loading} />
          <motion.button className="btn btn-primary btn-lg" onClick={handleStart} disabled={loading||!query.trim()} whileTap={{ scale:.97 }}>
            {loading ? <span className="spinner" /> : <><Send size={15} /> {t('startComparison')}</>}
          </motion.button>
        </div>
      </motion.div>

      {error && <div className="alert-error">{error}</div>}

      {state.comparisonResult && (
        <motion.div className="glass-card result-card" initial={{ opacity:0, y:12 }} animate={{ opacity:1, y:0 }}>
          <CompResult result={state.comparisonResult} />
        </motion.div>
      )}

      <motion.div className="glass-card chat-section" initial={{ opacity:0, y:8 }} animate={{ opacity:1, y:0 }} transition={{ delay:.2 }}>
        <div className="chat-section-title"><MessageSquare size={15} /> {t('chatHistory')}</div>
        <ChatBox messages={state.comparisonMessages} onSend={handleChat}
          placeholder={t('followUpComparison')} loading={chatLoad}
          emptyText={t('noComparisonData')} disabled={!state.comparisonSessionId} />
      </motion.div>
    </div>
  );
}
