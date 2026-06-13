import { useState } from 'react';
import { motion } from 'framer-motion';
import { LayoutGrid, MessageSquare, Link } from 'lucide-react';
import { useApp, useDispatch } from '../store/AppContext';
import { useT } from '../i18n/translations';
import { startComparison, chatComparison, ApiClientError } from '../services/api';
import ChatBox from '../components/ChatBox';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

function CompResult({ result }: { result: Record<string, unknown> | null }) {
  const { state } = useApp();
  const t = useT(state.lang);

  if (!result) return <div className="no-data">{t('noComparisonData')}</div>;
  if (typeof (result as unknown) === 'string') return <p className="result-summary">{result as unknown as string}</p>;

  // Robustly extract data - might be wrapped in .data or direct
  const data = (result.data || result) as any;
  const { 
    summary, 
    comparison_table, 
    key_differences, 
    recommendation, 
    sources,
    comparison,
    feature,
    product_labels
  } = data;


  // Robust label extraction
  const labels = product_labels || (result as any).products?.reduce((acc:any, p:any, i:number) => {
    acc[`product_${i+1}`] = p.product_clean;
    return acc;
  }, {}) || {};

  const getLabel = (key: string) => {
    if (labels[key]) return labels[key];
    if (key === 'product_1') return t('productOne');
    if (key === 'product_2') return t('productTwo');
    if (key === 'feature') return t('feature');
    return key.replace(/_/g, ' ');
  };

  const headerText = (key: string) => getLabel(key);
  const recommendationLabel = (key: string) => getLabel(key);

  const cleanList = (arr: any) => {
    if (!Array.isArray(arr)) return [];
    return arr
      .map(item => String(item).replace(/^[•\-\*]\s*/, '').trim())
      .filter(item => item.length > 0);
  };

  return (
    <div className="comp-result-inline">
      {summary && (
        <div className="result-summary prose prose-sm dark:prose-invert max-w-none" style={{ marginBottom: 20 }}>
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{summary}</ReactMarkdown>
        </div>
      )}

      {/* Feature Answer (Follow-ups) */}
      {comparison && feature && (
        <div className="result-section">
          <div className="result-section-title">🔍 {feature}</div>
          <div className="space-y-2 mt-2">
            {Object.entries(comparison).map(([k, v]) => (
              <div key={k} className="flex flex-col gap-1 p-3 rounded-lg bg-white/5 border border-white/5">
                <span className="text-[10px] uppercase tracking-wider font-bold text-gray-400">{headerText(k)}</span>
                <span className="text-sm leading-relaxed">{String(v)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Comparison Table */}
      {Array.isArray(comparison_table) && comparison_table.length > 0 && (
        <div className="result-section">
          <div className="result-section-title">📊 {t('comparisonTable') || 'Specifications'}</div>
          <div className="comp-table-wrap mt-3">
            <table className={`comp-table ${state.lang === 'ar' ? 'rtl' : ''}`} dir={state.lang === 'ar' ? 'rtl' : 'ltr'}>
              <thead><tr>{Object.keys(comparison_table[0]).map(k=><th key={k}>{headerText(k)}</th>)}</tr></thead>
              <tbody>{comparison_table.map((row:any,i:number)=>(
                <tr key={i}>{Object.entries(row).map(([k,v],j:number)=><td key={j}>{String(v)}</td>)}</tr>
              ))}</tbody>
            </table>
          </div>
        </div>
      )}

      {/* Key Differences */}
      {cleanList(key_differences).length > 0 && (
        <div className="result-section">
          <div className="result-section-title">🔀 {t('keyDifferences')}</div>
          <div className="result-list mt-2">
            {cleanList(key_differences).map((d:string,i:number)=>(
              <div key={i} className="result-list-item">
                {d}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommendation */}
      {recommendation && (
        <div className="result-section">
          <div className="result-section-title">🏆 {t('recommendation')}</div>
          <div className="space-y-3 mt-2">
            {Object.entries(recommendation).map(([k,v])=>(
              <div key={k} className="p-4 rounded-xl bg-primary/5 border border-primary/10">
                <strong style={{ fontSize:'var(--text-xs)', color:'var(--c-primary-500)', display:'block', marginBottom:4, textTransform:'uppercase', letterSpacing:'0.05em' }}>{recommendationLabel(k)}</strong>
                <div className="result-list">
                  {Array.isArray(v) ? (
                    cleanList(v).map((x,i)=>(
                      <div key={i} className="result-list-item">
                        {x}
                      </div>
                    ))
                  ) : (
                    <div className="text-sm" style={{ color:'var(--c-text-2)' }}>{String(v)}</div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Sources */}
      {Array.isArray(sources) && sources.length > 0 && (
        <div className="result-section">
          <div className="result-section-title"><Link size={14} /> {t('sources')}</div>
          <div className="source-chips mt-2">{sources.map((s:any,i:number)=>s.url
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
    const userMsg: ChatMessage = { role: 'user', content: msg };
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
        // Immediate feedback: append user message locally
        dispatch({ type: 'APPEND_MSG', payload: { agent: 'comparison', msg: userMsg } });
        
        const res: any = await chatComparison(state.userId!, state.comparisonSessionId, msg, state.lang);
        if (res.status !== 'success') throw new ApiClientError(res.message || 'Failed');
        
        // Append assistant response
        dispatch({ type:'APPEND_MSG', payload:{ agent:'comparison', msg:{ role:'assistant', content:res.message||'', payload:res }}});
        if (res.session_id) dispatch({ type:'SET_ACTIVE_SESSION', payload: res.session_id });
      }
    } catch(e) { setError(e instanceof ApiClientError ? e.message : String(e)); }
    finally { setChatLoad(false); }
  };


  const renderComparisonPayload = (payload: any) => {
    if (payload.type === 'comparison' || payload.type === 'feature_answer') {
      return (
        <div className="inline-payload-wrapper glass-card mt-4 overflow-hidden shadow-xl border-white/10">
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
