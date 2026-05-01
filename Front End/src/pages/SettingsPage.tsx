import { motion } from 'framer-motion';
import { Zap } from 'lucide-react';
import { Sun, Moon, Globe, Monitor, Palette, Layers, ChevronRight } from 'lucide-react';
import { useApp, useDispatch, type ColorPalette, type Theme } from '../store/AppContext';
import RECOAvatar from '../components/RECOAvatar';

const PALETTES: Array<{ key: ColorPalette; label: string; dark?: boolean; colors: string[] }> = [
  {
    key: 'cyber-amethyst',
    label: 'Cyber Amethyst',
    colors: ['#7c5cfc', '#4f46e5', '#3b82f6', '#080C14', '#F8FAFC'],
  },
  {
    key: 'obsidian-orange',
    label: 'Obsidian & Orange',
    dark: true,
    colors: ['#F97316', '#FB923C', '#C2410C', '#0B0B0B', '#1A1A1A'],
  },
  {
    key: 'neon-purple',
    label: 'Neon Purple',
    dark: true,
    colors: ['#d946ef', '#a855f7', '#7c3aed', '#09020f', '#160b24'],
  },
  {
    key: 'arctic-white',
    label: 'Arctic White',
    dark: false,
    colors: ['#0ea5e9', '#38bdf8', '#0284c7', '#f0f9ff', '#ffffff'],
  },
  {
    key: 'emerald-dark',
    label: 'Emerald Dark',
    dark: true,
    colors: ['#10b981', '#34d399', '#059669', '#020f09', '#0a1f14'],
  },
  {
    key: 'rose-gold',
    label: 'Rose Gold',
    dark: false,
    colors: ['#f43f5e', '#fb7185', '#e11d48', '#fff1f2', '#fdf2f8'],
  },
];

const SECTION = ({ title, icon: Icon, children }: { title: string; icon: React.ElementType; children: React.ReactNode }) => (
  <div className="settings-section glass-card">
    <div className="settings-section-header">
      <div className="settings-section-icon"><Icon size={16} /></div>
      <h3 className="settings-section-title">{title}</h3>
    </div>
    <div className="settings-section-body">{children}</div>
  </div>
);

const TOGGLE = ({ label, desc, value, onChange }: { label: string; desc?: string; value: boolean; onChange: (v: boolean) => void }) => (
  <div className="settings-toggle-row">
    <div className="settings-toggle-info">
      <div className="settings-toggle-label">{label}</div>
      {desc && <div className="settings-toggle-desc">{desc}</div>}
    </div>
    <button
      className={`settings-toggle-btn ${value ? 'on' : 'off'}`}
      onClick={() => onChange(!value)}
      aria-label={label}
    >
      <span className="settings-toggle-thumb" />
    </button>
  </div>
);

export default function SettingsPage() {
  const { state } = useApp();
  const dispatch = useDispatch();

  const selectedPalette = PALETTES.find(p => p.key === state.colorPalette) || PALETTES[0];

  return (
    <motion.div
      className="page-wrapper"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
    >
      {/* Header */}
      <div className="page-header-row">
        <div>
          <div className="page-eyebrow">
            <Monitor size={11} />
            Configuration
          </div>
          <h1 className="page-title">Settings</h1>
          <p className="page-subtitle">Customize your RECO experience</p>
        </div>
        <div className="page-title-icon">
          <Monitor size={22} />
        </div>
      </div>

      {/* Avatar preview with states */}
      <div className="glass-card settings-avatar-preview">
        <div className="settings-avatar-preview-inner">
          <RECOAvatar size={160} avatarState="idle" interactive showThoughts={false} />
          <div className="settings-avatar-states">
            <h4 className="settings-avatar-title">Your AI Assistant</h4>
            <p className="settings-avatar-desc">Interactive 3D avatar — drag to rotate</p>
            <div className="settings-avatar-state-pills">
              <span className="avatar-state-pill idle">Idle</span>
              <span className="avatar-state-pill listening">Listening</span>
              <span className="avatar-state-pill thinking">Thinking</span>
            </div>
          </div>
        </div>
      </div>

      {/* Appearance */}
      <SECTION title="Appearance" icon={Sun}>
        {/* Theme */}
        <div className="settings-row-label">Theme</div>
        <div className="settings-theme-row">
          {(['light', 'dark'] as Theme[]).map(t => (
            <button
              key={t}
              className={`settings-theme-btn ${state.theme === t ? 'active' : ''}`}
              onClick={() => dispatch({ type: 'SET_THEME', payload: t })}
            >
              {t === 'light' ? <Sun size={15} /> : <Moon size={15} />}
              {t.charAt(0).toUpperCase() + t.slice(1)}
            </button>
          ))}
        </div>

        {/* Glassmorphism toggle */}
        <TOGGLE
          label="Glassmorphism"
          desc={state.lang === 'ar' ? 'تأثيرات الزجاج المضبب (افتراضي: مفعّل)' : 'Frosted glass backgrounds and blur effects (default: enabled)'}
          value={state.glassmorphism}
          onChange={v => dispatch({ type: 'SET_GLASS', payload: v })}
        />
        <TOGGLE
          label={state.lang === 'ar' ? 'خلفية النيون / الذكاء الاصطناعي' : 'Neon / AI Background'}
          desc={state.lang === 'ar' ? 'شبكة متحركة ونيون وجسيمات (افتراضي: معطّل)' : 'Animated grid, neon scan lines & particles (default: off)'}
          value={state.neonBg}
          onChange={v => dispatch({ type: 'SET_NEON', payload: v })}
        />
      </SECTION>

      {/* Color Palettes */}
      <SECTION title="Color Palette" icon={Palette}>
        <p className="settings-palette-hint">
          3 dark palettes · 3 light palettes — switching auto-applies theme
        </p>
        <div className="settings-palette-grid">
          {PALETTES.map(p => (
            <motion.button
              key={p.key}
              className={`settings-palette-card ${state.colorPalette === p.key ? 'active' : ''}`}
              onClick={() => {
                dispatch({ type: 'SET_PALETTE', payload: p.key });
                if (p.dark !== undefined) dispatch({ type: 'SET_THEME', payload: p.dark ? 'dark' : 'light' });
              }}
              whileHover={{ y: -3 }}
              whileTap={{ scale: 0.97 }}
              transition={{ duration: 0.18 }}
            >
              <div className="palette-swatches">
                {p.colors.map((c, i) => (
                  <span key={i} className="palette-swatch" style={{ background: c }} />
                ))}
              </div>
              <div className="palette-meta">
                <span className="palette-name">{p.label}</span>
                <span className={`palette-mode-tag ${p.dark ? 'dark' : 'light'}`}>
                  {p.dark === undefined ? 'any' : p.dark ? 'dark' : 'light'}
                </span>
              </div>
              {state.colorPalette === p.key && (
                <span className="palette-active-check">
                  <svg viewBox="0 0 16 16" width="14" height="14" fill="currentColor">
                    <path d="M13.5 3.5L6 11 2.5 7.5l-1 1L6 13l8.5-8.5z"/>
                  </svg>
                </span>
              )}
            </motion.button>
          ))}
        </div>
      </SECTION>

      {/* Language */}
      <SECTION title="Language" icon={Globe}>
        <div className="settings-theme-row">
          {(['en', 'ar'] as const).map(l => (
            <button
              key={l}
              className={`settings-theme-btn ${state.lang === l ? 'active' : ''}`}
              onClick={() => dispatch({ type: 'SET_LANG', payload: l })}
            >
              {l === 'en' ? 'English' : 'العربية'}
            </button>
          ))}
        </div>
      </SECTION>

      {/* Interface */}
      <SECTION title="Interface" icon={Layers}>
        <TOGGLE
          label="Sidebar open by default"
          desc="Keep the navigation sidebar expanded on load"
          value={state.sidebarOpen}
          onChange={v => dispatch({ type: 'SET_SIDEBAR', payload: v })}
        />
      </SECTION>

      {/* Legal links */}
      <div className="settings-legal-row">
        <button className="settings-legal-link" onClick={() => dispatch({ type: 'SET_PAGE', payload: 'privacy' })}>
          Privacy Policy <ChevronRight size={12} />
        </button>
        <button className="settings-legal-link" onClick={() => dispatch({ type: 'SET_PAGE', payload: 'terms' })}>
          Terms of Service <ChevronRight size={12} />
        </button>
      </div>

      {/* Copyright */}
      <div className="settings-copyright">
        &copy; 2026 RECO AI — All rights reserved
      </div>
    </motion.div>
  );
}
