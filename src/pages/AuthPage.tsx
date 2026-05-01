import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mail, Lock, Eye, EyeOff, User, Sun, Moon, Sparkles, ArrowRight } from 'lucide-react';
import { useApp, useDispatch } from '../store/AppContext';
import { useT } from '../i18n/translations';
import { login, register, createGuestUser, ApiClientError } from '../services/api';
import NebulaAvatar from '../components/NebulaAvatar';
import RecoLogo from '../components/RecoLogo';

export default function AuthPage() {
  const { state } = useApp();
  const dispatch = useDispatch();
  const t = useT(state.lang);
  const [tab, setTab]       = useState<'login' | 'signup'>('login');
  const [email, setEmail]   = useState('');
  const [password, setPass] = useState('');
  const [name, setName]     = useState('');
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError]   = useState('');

  const dir = state.lang === 'ar' ? 'rtl' : 'ltr';

  const onSuccess = (data: any) => {
    const u = data.data || {};
    dispatch({ type: 'SET_USER', payload: { userId: u.user_id, userMode: u.mode, userEmail: u.email, displayName: u.display_name } });
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) { setError(t('pleaseEnter')); return; }
    setLoading(true); setError('');
    try { onSuccess(await login(email, password)); }
    catch (e) { setError(e instanceof ApiClientError ? e.message : String(e)); }
    finally { setLoading(false); }
  };

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) { setError(t('pleaseEnter')); return; }
    setLoading(true); setError('');
    try { onSuccess(await register(email, password, name || undefined)); }
    catch (e) { setError(e instanceof ApiClientError ? e.message : String(e)); }
    finally { setLoading(false); }
  };

  const handleGuest = async () => {
    setLoading(true); setError('');
    try { onSuccess(await createGuestUser()); }
    catch (e) { setError(e instanceof ApiClientError ? e.message : String(e)); }
    finally { setLoading(false); }
  };

  return (
    <div className="auth-root" dir={dir}>
      {/* Animated background orbs */}
      <div className="auth-bg-canvas">
        <div className="auth-orb auth-orb-1" />
        <div className="auth-orb auth-orb-2" />
        <div className="auth-orb auth-orb-3" />
      </div>

      {/* Navbar */}
      <nav className="auth-nav">
        <RecoLogo size="md" />
        <div className="auth-nav-right">
          <div className="theme-pill">
            <button className={`theme-pill-btn ${state.theme==='light'?'active':''}`} onClick={() => dispatch({ type:'SET_THEME', payload:'light' })}>
              <Sun size={12} /> {state.lang==='en'?'Light':'فاتح'}
            </button>
            <button className={`theme-pill-btn ${state.theme==='dark'?'active':''}`} onClick={() => dispatch({ type:'SET_THEME', payload:'dark' })}>
              <Moon size={12} /> {state.lang==='en'?'Dark':'داكن'}
            </button>
          </div>
          <button className="btn btn-ghost btn-sm" onClick={() => dispatch({ type:'SET_LANG', payload: state.lang==='en'?'ar':'en' })}>
            {state.lang==='en'?'عربي':'EN'}
          </button>
        </div>
      </nav>

      {/* Body */}
      <div className="auth-body">
        {/* Hero */}
        <motion.div className="auth-hero" initial={{ opacity:0, x:-30 }} animate={{ opacity:1, x:0 }} transition={{ duration:.6, ease: "easeOut" }}>
          <div className="hero-label"><Sparkles size={11} /> AI-Powered Shopping</div>
          <h1 className="hero-h1">
            {t('heroTitle1')}<br />
            {t('heroTitle2')}<br />
            <em>{t('heroTitle3')}</em>
          </h1>
          <p className="hero-desc">{t('heroDesc')}</p>
          <div className="hero-stats">
            <div><div className="hero-stat-num">50K+</div><div className="hero-stat-lbl">Products Indexed</div></div>
            <div><div className="hero-stat-num">4.9★</div><div className="hero-stat-lbl">User Rating</div></div>
            <div><div className="hero-stat-num">99%</div><div className="hero-stat-lbl">Accuracy</div></div>
          </div>

          {/* Premium 3D Avatar Section */}
          <motion.div
            className="hero-avatar-section"
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.3, ease: [0.16, 1, 0.3, 1] }}
          >
            <div className="avatar-badge">
              <span className="avatar-badge-dot" />
              {state.lang === 'en' ? 'AI Shopping Assistant' : 'مساعد التسوق الذكي'}
            </div>

            <NebulaAvatar size={148} state="idle" />

            <div className="avatar-feature-pills">
              <div className="avatar-pill">
                <Sparkles size={11} style={{ color: 'var(--c-primary-600)' }} />
                {state.lang === 'en' ? 'Smart Picks' : 'اختيارات ذكية'}
              </div>
              <div className="avatar-pill">
                ⭐ {state.lang === 'en' ? '4.9 Rated' : 'تقييم ٤.٩'}
              </div>
              <div className="avatar-pill">
                🛍️ {state.lang === 'en' ? 'Best Deals' : 'أفضل العروض'}
              </div>
            </div>
          </motion.div>
        </motion.div>

        {/* Form */}
        <motion.div className="auth-form-card glass-card" initial={{ opacity:0, x:30 }} animate={{ opacity:1, x:0 }} transition={{ duration:.6, delay:.1, ease: "easeOut" }}>
          <div className="auth-form-title">{t('welcomeBack')}</div>
          <div className="auth-form-sub">{t('signInSubtitle')}</div>

          <div className="auth-tabs">
            <button className={`auth-tab ${tab==='login'?'active':''}`} onClick={() => { setTab('login'); setError(''); }}>{t('signIn')}</button>
            <button className={`auth-tab ${tab==='signup'?'active':''}`} onClick={() => { setTab('signup'); setError(''); }}>{t('createAccount')}</button>
          </div>

          <AnimatePresence mode="wait">
            {error && (
              <motion.div className="alert-error" key="err" initial={{ opacity:0, y:-6 }} animate={{ opacity:1, y:0 }} exit={{ opacity:0 }}>
                {error}
              </motion.div>
            )}
          </AnimatePresence>

          <AnimatePresence mode="wait">
            <motion.form
              key={tab}
              className="auth-form"
              initial={{ opacity:0, x: tab==='login'?-12:12 }}
              animate={{ opacity:1, x:0 }}
              exit={{ opacity:0, x: tab==='login'?12:-12 }}
              transition={{ duration:.25 }}
              onSubmit={tab==='login' ? handleLogin : handleSignup}
            >
              {tab==='signup' && (
                <div className="form-group">
                  <label className="form-label">{t('displayName')}</label>
                  <div className="input-group">
                    <span className="input-icon-left"><User size={15} /></span>
                    <input className="input-field" type="text" placeholder={t('yourName')} value={name} onChange={e=>setName(e.target.value)} />
                  </div>
                </div>
              )}
              <div className="form-group">
                <label className="form-label">{t('emailAddress')}</label>
                <div className="input-group">
                  <span className="input-icon-left"><Mail size={15} /></span>
                  <input className="input-field" type="email" placeholder={t('enterEmail')} value={email} onChange={e=>setEmail(e.target.value)} />
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">{t('password')}</label>
                <div className="input-group">
                  <span className="input-icon-left"><Lock size={15} /></span>
                  <input className="input-field" type={showPw?'text':'password'} placeholder={t('enterPassword')} value={password} onChange={e=>setPass(e.target.value)} style={{ paddingRight: 42 }} />
                  <button type="button" className="input-icon-right" onClick={()=>setShowPw(!showPw)}>
                    {showPw ? <EyeOff size={15} /> : <Eye size={15} />}
                  </button>
                </div>
              </div>
              {tab==='login' && (
                <div style={{ textAlign: 'right' }}>
                  <button type="button" style={{ background:'none',border:'none',color:'var(--c-primary-600)',fontSize:'var(--text-xs)',cursor:'pointer',fontWeight:600 }}>
                    {t('forgotPassword')}
                  </button>
                </div>
              )}
              <motion.button type="submit" className="btn btn-primary btn-lg btn-full" disabled={loading} whileHover={{ scale:1.01 }} whileTap={{ scale:.98 }}>
                {loading ? <span className="spinner" /> : <>{tab==='login'?t('signIn'):t('createAccount')} <ArrowRight size={15} /></>}
              </motion.button>
            </motion.form>
          </AnimatePresence>

          <div className="divider" style={{ margin:'20px 0' }}>{t('orContinueWith')}</div>

          <motion.button className="btn btn-ghost btn-lg btn-full" style={{ border:'1.5px solid var(--c-border)' }}
            onClick={handleGuest} disabled={loading}
            whileHover={{ scale:1.01 }} whileTap={{ scale:.98 }}>
            <span style={{ fontWeight:800, color:'var(--c-primary-600)', fontSize:'1rem' }}>G</span>
            {t('continueAsGuest')}
          </motion.button>

          <p className="auth-switch">
            {tab==='login' ? t('noAccount') : t('alreadyHaveAccount')}{' '}
            <button onClick={() => { setTab(tab==='login'?'signup':'login'); setError(''); }}>
              {tab==='login' ? t('createAccount') : t('signIn')}
            </button>
          </p>
        </motion.div>
      </div>

      <footer className="auth-footer">
        <span style={{ fontSize:'var(--text-xs)',color:'var(--c-text-4)' }}>{t('copyright')}</span>
        <div className="auth-footer-links">
          <button>{t('privacy')}</button>
          <button>{t('terms')}</button>
        </div>
      </footer>
    </div>
  );
}
