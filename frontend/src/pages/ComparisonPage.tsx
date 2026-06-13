import { useState } from 'react';
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

  const { 
    summary, 
    comparison_table, 
    key_differences, 
    recommendation, 
    sources,
    comparison,
    feature
  } = result as any;

  return (
    <div>
      {summary && <p className="result-summary" style={{ fontSize: 'var(--text-sm)' }}>{summary}</p>}

      {/* Feature Answer (Follow-ups) */}
      {comparison && feature && (
        <div className="result-section">
          <div className="result-section-title">🔍 {feature}</div>
          <div className="space-y-2 mt-2">
            {Object.entries(comparison).map(([k, v]) => (
              <div key={k} className="flex flex-col gap-1 p-3 rounded-lg bg-white/5 border border-white/5">
                <span className="text-[10px] uppercase tracking-wider font-bold text-gray-400">{headerText(k)}</span>
                <span className="text-sm">{String(v)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Comparison Table */}
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

      {/* Key Differences */}
      {Array.isArray(key_differences) && key_differences.length > 0 && (
        <div className="result-section">
          <div className="result-section-title">🔀 {t('keyDifferences')}</div>
          <div className="result-list">{key_differences.map((d:string,i:number)=>(
            <div key={i} className="result-list-item" style={{ fontSize: 'var(--text-xs)' }}>{d}</div>
          ))}</div>
        </div>
      )}

      {/* Recommendation */}
      {recommendation && (
        <div className="result-section">
          <div className="result-section-title">🏆 {t('recommendation')}</div>
          {Object.entries(recommendation).map(([k,v])=>(
            <div key={k} style={{ marginBottom:12 }}>
              <strong style={{ fontSize:'var(--text-xs)', color:'var(--c-primary-500)', display:'block', marginBottom:4 }}>{recommendationLabel(k)}</strong>
              {Array.isArray(v) ? <div className="result-list">{(v as string[]).map((x,i)=><div key={i} className="result-list-item" style={{ fontSize:'var(--text-xs)' }}>{x}</div>)}</div>
              : <p style={{ fontSize:'var(--text-xs)', color:'var(--c-text-2)' }}>{String(v)}</p>}
            </div>
          ))}
        </div>
      )}

      {/* Sources */}
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
  const [chatLoad, setChatLoad] = useState(false);
  const [error,    setError]    = useState('');

  const handleChat = async (msg: string) => {
    setChatLoad(true); setError('');
    try {
      if (!state.comparisonSessionId) {
        dispatch({ type:'RESET_AGENT', payload:'comparison' });
        const res: any = await startComparison(state.userId!, msg, state.lang);
        if (res.status !== 'success') throw new ApiClientError(res.message || 'Failed');
        dispatch({ type:'SET_COMPARISON', payload:{
          comparisonSessionId: res.session_id,
          comparisonMessages: [{ role:'user', content:msg },{ role:'assistant', content:res.message||'', payload:res }],
        }});
        dispatch({ type:'SET_ACTIVE_SESSION', payload: res.session_id });
      } else {
        const res: any = await chatComparison(state.userId!, state.comparisonSessionId, msg, state.lang);
        if (res.status !== 'success') throw new ApiClientError(res.message || 'Failed');
        dispatch({ type:'APPEND_MSG', payload:{ agent:'comparison', msg:{ role:'assistant', content:res.message||'', payload:res }}});
        if (res.session_id) dispatch({ type:'SET_ACTIVE_SESSION', payload: res.session_id });
      }
    } catch(e) { setError(e instanceof ApiClientError ? e.message : String(e)); }
    finally { setChatLoad(false); }
  };

  const renderComparisonPayload = (payload: any) => {
    if (payload.type === 'comparison' || payload.type === 'feature_answer') {
      return (
        <div className="inline-payload-wrapper glass-card p-4 md:p-6 mt-2 overflow-hidden">
          <CompResult result={payload.data || payload} />
        </div>
      );
    }
    return null;
  };

  return (
    <div className="page-wrapper conversational-page">
      <motion.div className="page-header-row" initial={{ opacity:0, y:-12 }} animate={{ opacity:1, y:0 }} transition={{ duration:.4 }}>
        <div>
          <div className="page-eyebrow"><LayoutGrid size={11} /> {t('comparison')}</div>
          <h1 className="page-title">{t('compareTitle')}</h1>
          <p className="page-subtitle">{t('comparisonDesc')}</p>
        </div>
        <div className="page-title-icon"><LayoutGrid size={22} /></div>
      </motion.div>

      {error && <div className="alert-error" style={{ marginBottom: 20 }}>{error}</div>}

      <div className="conversational-chat-container">
        <ChatBox 
          messages={state.comparisonMessages} 
          onSend={handleChat}
          placeholder={state.comparisonSessionId ? t('followUpComparison') : t('comparisonPlaceholder')} 
          loading={chatLoad}
          renderPayload={renderComparisonPayload}
          emptyText={t('noComparisonData')} 
        />
      </div>
    </div>
  );
}
