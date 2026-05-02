import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Sparkles, LayoutGrid, Star, Search,
  LogOut, Zap, MessageSquare, Plus, Settings,
} from 'lucide-react';
import { useApp, useDispatch, type Page } from '../store/AppContext';
import { useT } from '../i18n/translations';
import { getSessions, getSession, getSessionMessages } from '../services/api';
import RecoLogo from './RecoLogo';
import RECOAvatar from './RECOAvatar';

const NAV: Array<{ key: Page; icon: React.ElementType; en: string; ar: string }> = [
  { key: 'recommendation', icon: Sparkles,    en: 'Recommendations', ar: 'التوصيات' },
  { key: 'comparison',     icon: LayoutGrid,   en: 'Comparison',      ar: 'المقارنة' },
  { key: 'review',         icon: Star,         en: 'Reviews',         ar: 'المراجعات' },
  { key: 'search',         icon: Search,       en: 'Search',          ar: 'البحث' },
  { key: 'settings',       icon: Settings,     en: 'Settings',        ar: 'الإعدادات' },
];

const ICON_RAIL_W = 52; // width of collapsed icon rail

export default function Sidebar({ mobileOpen, onClose }: { mobileOpen?: boolean; onClose?: () => void }) {
  const { state } = useApp();
  const dispatch = useDispatch();
  const t = useT(state.lang);
  const [sessions, setSessions] = useState<Array<Record<string, unknown>>>([]);
  const open = state.sidebarOpen;

  useEffect(() => {
    if (!state.userId) return;
    getSessions(state.userId, 30)
      .then(res => {
        const data = ((res as any).data?.sessions as Array<Record<string, unknown>>) || [];
        setSessions(data);
      })
      .catch(() => {});
  }, [state.userId, state.activeSessionId]);

  const handleSession = async (s: Record<string, unknown>) => {
    const sid = s.session_id as string;
    if (!state.userId || !sid) return;
    try {
      const [sesRes, msgRes] = await Promise.all([
        getSession(sid, state.userId),
        getSessionMessages(sid, state.userId, 100),
      ]);
      const sesData = ((sesRes as any).data?.session as Record<string, unknown>) || {};
      const agentType = sesData.agent_type as string;
      const rawMsgs = ((msgRes as any).data?.messages as Array<Record<string, unknown>>) || [];
      const messages = rawMsgs.map(m => ({
        role: m.role === 'user' ? 'user' as const : 'assistant' as const,
        content: String(m.content || ''),
        payload: m.payload as Record<string, unknown>,
      }));
      dispatch({ type: 'SET_ACTIVE_SESSION', payload: sid });
      if (agentType === 'recommendation') {
        const products = ((sesData.agent_state as any)?.last_recommendations as any[]) || [];
        dispatch({ type: 'SET_RECOMMENDATION', payload: { recommendationSessionId: sid, recommendationMessages: messages, recommendationProducts: products } });
        dispatch({ type: 'SET_PAGE', payload: 'recommendation' });
      } else if (agentType === 'comparison') {
        dispatch({ type: 'SET_COMPARISON', payload: { comparisonSessionId: sid, comparisonMessages: messages } });
        dispatch({ type: 'SET_PAGE', payload: 'comparison' });
      } else if (agentType === 'review') {
        dispatch({ type: 'SET_REVIEW', payload: { reviewSessionId: sid, reviewMessages: messages } });
        dispatch({ type: 'SET_PAGE', payload: 'review' });
      }
      onClose?.();
    } catch { /* silent */ }
  };

  const newChat = () => {
    (['recommendation','comparison','review'] as const).forEach(a => dispatch({ type: 'RESET_AGENT', payload: a }));
    dispatch({ type: 'SET_ACTIVE_SESSION', payload: null });
    dispatch({ type: 'SET_PAGE', payload: 'recommendation' });
    onClose?.();
  };

  const display = state.displayName || state.userEmail?.split('@')[0] || 'User';

  return (
    <motion.aside
      className={`sidebar ${mobileOpen ? 'mob-open' : ''} ${open ? 'sidebar-expanded' : 'sidebar-rail'}`}
      animate={{ width: open ? 256 : ICON_RAIL_W }}
      transition={{ duration: 0.28, ease: [0.16, 1, 0.3, 1] }}
      style={{ overflow: 'hidden', flexShrink: 0, position: 'fixed', top: 0, bottom: 0 }}
    >
      {/* ── EXPANDED SIDEBAR CONTENT ── */}
      <AnimatePresence>
        {open && (
          <motion.div
            style={{ width: 256, minWidth: 256, height: '100%', display: 'flex', flexDirection: 'column' }}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            {/* Logo */}
            <div className="sidebar-top">
              <div className="sidebar-logo">
                <RecoLogo size="sm" />
                <div className="logo-tagline">{t('appTagline')}</div>
              </div>
            </div>

            {/* Nav */}
            <nav className="sidebar-nav">
              <div className="sidebar-section-label">
                {state.lang === 'ar' ? 'التنقل' : 'Navigation'}
              </div>
              {NAV.map(({ key, icon: Icon, en, ar }) => {
                const active = state.page === key;
                return (
                  <motion.button
                    key={key}
                    className={`nav-item ${active ? 'active' : ''}`}
                    onClick={() => { dispatch({ type: 'SET_PAGE', payload: key }); onClose?.(); }}
                    whileHover={{ x: state.lang === 'ar' ? -2 : 2 }}
                    whileTap={{ scale: 0.98 }}
                    transition={{ duration: 0.12 }}
                  >
                    <Icon className="nav-icon" size={16} />
                    <span>{state.lang === 'ar' ? ar : en}</span>
                    {active && <span className="nav-active-pip" />}
                  </motion.button>
                );
              })}
            </nav>

            {/* Upgrade */}
            <motion.div className="sidebar-upgrade" whileHover={{ scale: 1.01 }} transition={{ duration: 0.2 }}>
              <div className="upgrade-title">
                <svg width="11" height="11" viewBox="0 0 16 16" fill="currentColor" style={{ display:'inline', marginInlineEnd:6 }}>
                  <path d="M8 1l1.9 4.1L14 6l-3 2.9.7 4.1L8 10.9l-3.7 2.1.7-4.1L2 6l4.1-.9z"/>
                </svg>
                {t('upgradePremium')}
              </div>
              <div className="upgrade-desc">{t('upgradeDesc')}</div>
              <button className="btn-upgrade"><Zap size={11} /> {t('upgradeNow')}</button>
            </motion.div>

            {/* Chat history */}
            <div className="sidebar-history-section">
              <div className="sidebar-history-header">
                <span className="sidebar-history-label">
                  <MessageSquare size={10} style={{ display:'inline', marginInlineEnd:4 }} />
                  {t('chatHistorySidebar')}
                </span>
                <button className="btn-new-chat" onClick={newChat}>
                  <Plus size={10} /> {t('newChat')}
                </button>
              </div>
              <div className="history-items">
                <AnimatePresence>
                  {sessions.length === 0 && <div className="history-empty">{t('noChats')}</div>}
                  {sessions.slice(0, 12).map((s, i) => {
                    const sid = s.session_id as string;
                    const isActive = sid === state.activeSessionId;
                    const title = ((s.title as string) || (s.agent_type as string) || 'Chat').slice(0, 30);
                    return (
                      <motion.button
                        key={sid}
                        className={`history-item ${isActive ? 'active' : ''}`}
                        onClick={() => handleSession(s)}
                        initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: i * 0.03 }}
                        whileHover={{ x: state.lang === 'ar' ? -2 : 2 }}
                      >
                        <span className="h-dot" />
                        <span className="h-title">{title}</span>
                        <span className="h-type">{s.agent_type as string}</span>
                      </motion.button>
                    );
                  })}
                </AnimatePresence>
              </div>
            </div>

            {/* Footer */}
            <div className="sidebar-footer">
              <div style={{ width:32, height:32, borderRadius:'50%', overflow:'hidden', flexShrink:0 }}>
                <RECOAvatar size={32} interactive={false} />
              </div>
              <div className="user-meta">
                <div className="user-meta-name">{display}</div>
                <div className="user-meta-role">{state.userMode === 'guest'
                  ? (state.lang === 'ar' ? 'زائر' : 'Guest')
                  : (state.lang === 'ar' ? 'عضو' : 'Member')}
                </div>
              </div>
              <button className="btn-logout" onClick={() => dispatch({ type: 'LOGOUT' })} title={t('logout')}>
                <LogOut size={15} />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── COLLAPSED ICON RAIL ── */}
      {!open && (
        <motion.div
          className="sidebar-icon-rail"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.2, delay: 0.1 }}
        >
          {/* Mini logo mark */}
          <div className="rail-logo-dot" title="RECO">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="12" cy="12" r="10" fill="var(--c-primary-600)" />
              <path d="M9 8 L9 16 M9 8 L13 8 Q15 8 15 10 Q15 12 13 12 L9 12 M12 12 L15 16" stroke="white" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
            </svg>
          </div>

          {/* Nav icons */}
          {NAV.map(({ key, icon: Icon, en, ar }) => {
            const active = state.page === key;
            return (
              <motion.button
                key={key}
                className={`rail-icon-btn ${active ? 'active' : ''}`}
                onClick={() => { dispatch({ type: 'SET_PAGE', payload: key }); onClose?.(); }}
                title={state.lang === 'ar' ? ar : en}
                whileHover={{ scale: 1.12 }}
                whileTap={{ scale: 0.92 }}
              >
                <Icon size={18} />
                {active && <span className="rail-active-dot" />}
              </motion.button>
            );
          })}

          {/* Spacer */}
          <div style={{ flex: 1 }} />

          {/* Logout at bottom */}
          <motion.button
            className="rail-icon-btn"
            onClick={() => dispatch({ type: 'LOGOUT' })}
            title={t('logout')}
            whileHover={{ scale: 1.1 }}
          >
            <LogOut size={16} />
          </motion.button>
        </motion.div>
      )}
    </motion.aside>
  );
}
