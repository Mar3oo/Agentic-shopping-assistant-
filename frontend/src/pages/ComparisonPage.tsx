import { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { LayoutGrid, MessageSquare, Link } from 'lucide-react';
import { useApp, useDispatch } from '../store/AppContext';
import { useT } from '../i18n/translations';
import { startComparison, chatComparison, ApiClientError } from '../services/api';
import ChatBox from '../components/ChatBox';

function CompResult({ result }: { result: Record<string, unknown> | null }) {
  const { state } = useApp();
  const t = useT(state.lang);

  const headerText = (key: string) => {
    if (key === 'product_1') return t('productOne');
    if (key === 'product_2') return t('productTwo');
    if (key === 'feature') return t('feature');
    return key.replace(/_/g, ' ');
  };

  const recommendationLabel = (key: string) => {
    if (key === 'product_1') return t('productOne');
    if (key === 'product_2') return t('productTwo');
    return key.replace(/_/g, ' ');
  };

  if (!result) return <div className="no-data">{t('noComparisonData')}</div>;
  if (typeof (result as unknown) === 'string') return <p className="result-summary">{result as unknown as string}</p>;
  const { summary, comparison_table, key_differences, recommendation, sources } = result as any;
  return (
    <div>
      {summary && <p className="result-summary">{summary}</p>}
      {Array.isArray(comparison_table) && comparison_table.length > 0 && (
        <div className="comp-table-wrap">
          <table className={`comp-table ${state.lang === 'ar' ? 'rtl' : ''}`} dir={state.lang === 'ar' ? 'rtl' : 'ltr'}>
            <thead><tr>{Object.keys(comparison_table[0]).map(k=><th key={k}>{headerText(k)}</th>)}</tr></thead>
            <tbody>{comparison_table.map((row:any,i:number)=>(
              <tr key={i}>{Object.entries(row).map(([k,v],j:number)=><td key={j}>{String(v)}</td>)}</tr>
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
              <strong style={{ fontSize:'var(--text-sm)', textTransform:'capitalize' }}>{recommendationLabel(k)}</strong>
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
    </div>
  );
}

export default function ComparisonPage() {
  const { state } = useApp();
  const dispatch  = useDispatch();
  const t = useT(state.lang);
  const [loading,  setLoading]  = useState(false);
  const [chatLoad, setChatLoad] = useState(false);
  const [error,    setError]    = useState('');
  const resultsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (state.comparisonResult) {
      const el = resultsRef.current;
      if (el) {
        const header = document.querySelector('.page-header-row') as HTMLElement | null;
        const headerHeight = header ? header.getBoundingClientRect().height : 0;
        const padding = 20; // small gap from top
        const top = el.getBoundingClientRect().top + window.scrollY - headerHeight - padding;
        window.scrollTo({ top: top > 0 ? top : 0, behavior: 'smooth' });
      }
    }
  }, [state.comparisonResult]);

  const handleChat = async (msg: string) => {
    setChatLoad(true); setError('');
    try {
      if (!state.comparisonSessionId) {
        dispatch({ type:'RESET_AGENT', payload:'comparison' });
        const res: any = await startComparison(state.userId!, msg, state.lang);
        if (res.status !== 'success') throw new ApiClientError(res.message || 'Failed');
        dispatch({ type:'SET_COMPARISON', payload:{
          comparisonSessionId: res.session_id, comparisonResult: res.data,
          comparisonMessages: [{ role:'user', content:msg },{ role:'assistant', content:res.message||'', payload:res }],
        }});
        dispatch({ type:'SET_ACTIVE_SESSION', payload: res.session_id });
      } else {
        dispatch({ type:'APPEND_MSG', payload:{ agent:'comparison', msg:{ role:'user', content:msg }}});
        const res: any = await chatComparison(state.userId!, state.comparisonSessionId, msg, state.lang);
        if (res.status !== 'success') throw new ApiClientError(res.message || 'Failed');
        dispatch({ type:'APPEND_MSG', payload:{ agent:'comparison', msg:{ role:'assistant', content:res.message||'', payload:res }}});
        dispatch({ type:'SET_COMPARISON', payload:{
          comparisonSessionId: res.session_id || state.comparisonSessionId,
          comparisonResult: res.type === 'reset' ? null : res.data,
        }});
        if (res.session_id) dispatch({ type:'SET_ACTIVE_SESSION', payload: res.session_id });
      }
    } catch(e) { setError(e instanceof ApiClientError ? e.message : String(e)); }
    finally { setChatLoad(false); }
  };

  return (
    <div className="page-wrapper">
      <motion.div className="page-header-row" initial={{ opacity:0, y:-12 }} animate={{ opacity:1, y:0 }} transition={{ duration:.4 }}>
        <div>
          <div className="page-eyebrow"><LayoutGrid size={11} /> {t('comparison')}</div>
          <h1 className="page-title">{t('compareTitle')}</h1>
          <p className="page-subtitle">{t('comparisonDesc')}</p>
        </div>
        <div className="page-title-icon"><LayoutGrid size={22} /></div>
      </motion.div>

      {error && <div className="alert-error">{error}</div>}
      {/* Show comparison results when available */}
          {state.comparisonResult && (
            <motion.div ref={resultsRef as any} className="glass-card result-card" initial={{ opacity:0, y:8 }} animate={{ opacity:1, y:0 }} transition={{ delay:.15 }}>
              <div style={{ marginBottom: 10, fontWeight: 700 }}>{t('comparisonResults')}</div>
              <CompResult result={state.comparisonResult} />
            </motion.div>
          )}

      <motion.div className="glass-card chat-section" initial={{ opacity:0, y:8 }} animate={{ opacity:1, y:0 }} transition={{ delay:.2 }}>
        <div className="chat-section-title"><MessageSquare size={15} /> {t('chatHistory')}</div>
        <ChatBox messages={state.comparisonMessages} onSend={handleChat}
          placeholder={state.comparisonSessionId ? t('followUpComparison') : t('comparisonPlaceholder')} loading={chatLoad}
          emptyText={t('noComparisonData')} />
      </motion.div>
    </div>
  );
}
