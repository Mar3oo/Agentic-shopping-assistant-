import { Search, Bell, Moon, Sun, Menu } from 'lucide-react';
import { motion } from 'framer-motion';
import { useApp, useDispatch } from '../store/AppContext';
import { useT } from '../i18n/translations';
import RECOAvatar from './RECOAvatar';

export default function Header({ onMenuClick }: { onMenuClick?: () => void }) {
  const { state } = useApp();
  const dispatch = useDispatch();
  const t = useT(state.lang);

  const h = new Date().getHours();
  const greeting = h < 12 ? t('goodMorning') : h < 18 ? t('goodAfternoon') : t('goodEvening');
  const display = state.displayName || state.userEmail?.split('@')[0] || 'User';
  const today = new Date().toLocaleDateString(state.lang === 'ar' ? 'ar-EG' : 'en-US', { month: 'long', day: 'numeric', year: 'numeric' });

  return (
    <motion.header className="topbar" initial={{ y: -8, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ duration: 0.4 }}>
      <button className="menu-btn" onClick={onMenuClick}><Menu size={20} /></button>

      <div className="topbar-search">
        <Search className="topbar-search-icon" />
        <input
          type="text"
          className="topbar-search-input"
          placeholder={t('searchPlaceholder')}
          onKeyDown={e => { if (e.key === 'Enter') dispatch({ type: 'SET_PAGE', payload: 'search' }); }}
        />
        <kbd className="kbd">⌘K</kbd>
      </div>

      <div className="topbar-actions">
        <motion.button
          className="topbar-icon-btn"
          onClick={() => dispatch({ type: 'SET_THEME', payload: state.theme === 'dark' ? 'light' : 'dark' })}
          whileTap={{ scale: 0.9, rotate: 15 }} title="Toggle theme"
        >
          {state.theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
        </motion.button>

        <button className="topbar-lang-btn" onClick={() => dispatch({ type: 'SET_LANG', payload: state.lang === 'en' ? 'ar' : 'en' })}>
          {state.lang === 'en' ? 'عربي' : 'EN'}
        </button>

        <div className="topbar-sep" />

        <button className="topbar-icon-btn notif-btn">
          <Bell size={16} />
          <span className="notif-dot" />
        </button>

        <div className="topbar-user">
          <div className="topbar-avatar-3d">
            <RECOAvatar size={34} interactive={false} />
          </div>
          <div className="topbar-user-info">
            <span className="topbar-name">{greeting}, {display} 👋</span>
            <span className="topbar-sub">{today}</span>
          </div>
        </div>
      </div>
    </motion.header>
  );
}
