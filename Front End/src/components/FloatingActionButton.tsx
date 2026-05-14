// RECO Floating Action Button — Glassmorphic sphere with gradient core
// Expands to reveal "Quick Ask" tooltip on hover
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageCircle, X, Send } from 'lucide-react';
import { useApp, useDispatch } from '../store/AppContext';
import { ApiClientError, startRecommendation } from '../services/api';

export default function FloatingActionButton() {
  const { state } = useApp();
  const dispatch = useDispatch();
  const [open, setOpen] = useState(false);
  const [hovered, setHovered] = useState(false);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleAsk = async () => {
    const prompt = input.trim();
    if (!prompt || loading) return;
    if (!state.userId) {
      setError(state.lang === 'ar' ? 'يرجى تسجيل الدخول أولاً.' : 'Please sign in first.');
      return;
    }

    setLoading(true);
    setError('');
    (['recommendation', 'comparison', 'review'] as const).forEach(agent => {
      dispatch({ type: 'RESET_AGENT', payload: agent });
    });

    try {
      const res: any = await startRecommendation(state.userId, prompt, state.lang);
      dispatch({ type: 'SET_RECOMMENDATION', payload: {
        recommendationSessionId: res.session_id,
        recommendationMessages: [
          { role: 'user', content: prompt },
          { role: 'assistant', content: res.message || '', payload: res },
        ],
        recommendationProducts: res.data?.products || [],
        recommendationSuggestions: res.data?.suggestions || [],
      } });
      if (res.session_id) dispatch({ type: 'SET_ACTIVE_SESSION', payload: res.session_id });
      dispatch({ type: 'SET_PAGE', payload: 'recommendation' });
      setOpen(false);
      setInput('');
    } catch (e) {
      setError(e instanceof ApiClientError ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fab-root">
      <AnimatePresence>
        {open && (
          <motion.div
            className="fab-panel glass-card"
            initial={{ opacity: 0, y: 16, scale: 0.92 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.94 }}
            transition={{ duration: 0.28, ease: [0.16, 1, 0.3, 1] }}
          >
            <div className="fab-panel-header">
              <div className="fab-panel-title">
                <span className="fab-nebula-dot" />
                Quick Ask RECO
              </div>
              <button className="fab-close" onClick={() => setOpen(false)}><X size={14} /></button>
            </div>
            <div className="fab-panel-body">
              <p className="fab-panel-hint">What are you looking for today?</p>
              {error && <div className="alert-error" role="alert">{error}</div>}
              <div className="fab-input-row">
                <input
                  className="fab-input"
                  placeholder={state.lang === 'ar' ? 'اسألني عن أي منتج...' : 'Ask me about any product...'}
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter') void handleAsk(); }}
                  disabled={loading}
                  autoFocus
                />
                <motion.button
                  className="fab-send"
                  onClick={() => { void handleAsk(); }}
                  disabled={!input.trim() || loading}
                  whileHover={{ scale: 1.08 }}
                  whileTap={{ scale: 0.93 }}
                >
                  {loading ? <span className="spinner" /> : <Send size={14} />}
                </motion.button>
              </div>
              <div className="fab-quick-chips">
                {['Best laptops 2025', 'Noise-cancelling headphones', 'Budget phones'].map(q => (
                  <button key={q} className="fab-chip" onClick={() => { setInput(q); }}>{q}</button>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Tooltip on hover */}
      <AnimatePresence>
        {hovered && !open && (
          <motion.div
            className="fab-tooltip"
            initial={{ opacity: 0, x: 8 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 4 }}
            transition={{ duration: 0.18 }}
          >
            Quick Ask
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main FAB sphere */}
      <motion.button
        className="fab-btn"
        onClick={() => setOpen(o => !o)}
        onHoverStart={() => setHovered(true)}
        onHoverEnd={() => setHovered(false)}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.93 }}
        animate={open ? { rotate: 0 } : { rotate: [0, 0] }}
      >
        <div className="fab-glow-ring" />
        <AnimatePresence mode="wait">
          {open
            ? <motion.span key="x" initial={{ rotate: -90, opacity: 0 }} animate={{ rotate: 0, opacity: 1 }} exit={{ rotate: 90, opacity: 0 }} transition={{ duration: 0.2 }}><X size={20} /></motion.span>
            : <motion.span key="msg" initial={{ rotate: 90, opacity: 0 }} animate={{ rotate: 0, opacity: 1 }} exit={{ rotate: -90, opacity: 0 }} transition={{ duration: 0.2 }}><MessageCircle size={20} /></motion.span>
          }
        </AnimatePresence>
      </motion.button>
    </div>
  );
}
