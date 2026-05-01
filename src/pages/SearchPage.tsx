import { useState } from 'react';
import { motion } from 'framer-motion';
import { Search, Send } from 'lucide-react';
import { useApp, useDispatch } from '../store/AppContext';
import { useT } from '../i18n/translations';
import { search, ApiClientError } from '../services/api';
import ProductCards from '../components/ProductCards';
import type { Product } from '../store/AppContext';

export default function SearchPage() {
  const { state } = useApp();
  const dispatch  = useDispatch();
  const t = useT(state.lang);
  const [query,   setQuery]   = useState('');
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState('');

  const handleSearch = async () => {
    if (!query.trim()) return;
    setLoading(true); setError('');
    try {
      const res: any = await search(state.userId!, query);
      if (res.status !== 'success') throw new ApiClientError(res.message || 'Failed');
      dispatch({ type:'SET_SEARCH_RESULTS', payload: (res.data?.products as Product[]) || [] });
    } catch(e) { setError(e instanceof ApiClientError ? e.message : String(e)); }
    finally { setLoading(false); }
  };

  return (
    <div className="page-wrapper">
      <motion.div className="page-header-row" initial={{ opacity:0, y:-12 }} animate={{ opacity:1, y:0 }} transition={{ duration:.4 }}>
        <div>
          <div className="page-eyebrow"><Search size={11} /> Search</div>
          <h1 className="page-title">{t('searchTitle')}</h1>
          <p className="page-subtitle">{t('searchDesc')}</p>
        </div>
        <div className="page-title-icon"><Search size={22} /></div>
      </motion.div>

      <motion.div className="glass-card prompt-card" initial={{ opacity:0, y:8 }} animate={{ opacity:1, y:0 }} transition={{ delay:.1 }}>
        <div className="prompt-row">
          <input className="prompt-input" placeholder={t('searchQueryPlaceholder')} value={query}
            onChange={e=>setQuery(e.target.value)} onKeyDown={e=>e.key==='Enter'&&handleSearch()} disabled={loading} />
          <motion.button className="btn btn-primary btn-lg" onClick={handleSearch} disabled={loading||!query.trim()} whileTap={{ scale:.97 }}>
            {loading ? <span className="spinner" /> : <><Send size={15} /> {t('searchBtn')}</>}
          </motion.button>
        </div>
      </motion.div>

      {error && <div className="alert-error">{error}</div>}

      {state.searchResults.length > 0 && (
        <motion.div initial={{ opacity:0, y:12 }} animate={{ opacity:1, y:0 }} transition={{ delay:.1 }}>
          <ProductCards products={state.searchResults} title={t('searchResults')} emptyText={t('noResults')} />
        </motion.div>
      )}
    </div>
  );
}
