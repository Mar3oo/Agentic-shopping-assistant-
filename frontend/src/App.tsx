import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AppProvider, useApp } from './store/AppContext';
import AuthPage from './pages/AuthPage';
import RecommendationPage from './pages/RecommendationPage';
import ComparisonPage from './pages/ComparisonPage';
import ReviewPage from './pages/ReviewPage';
import SearchPage from './pages/SearchPage';
import SettingsPage from './pages/SettingsPage';
import PrivacyPage from './pages/PrivacyPage';
import TermsPage from './pages/TermsPage';
import Sidebar from './components/Sidebar';
import SidebarToggle from './components/SidebarToggle';
import Header from './components/Header';
import MeshBackground from './components/MeshBackground';
import FloatingActionButton from './components/FloatingActionButton';
import NeonBackground from './components/NeonBackground';
import './styles/global.css';

const RAIL_W = 52;
const FULL_W = 256;

const pageVariants = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0 },
  exit:    { opacity: 0, y: -5 },
};
const pageTransition = { duration: 0.25, ease: [0.16, 1, 0.3, 1] as [number,number,number,number] };

function AppShell() {
  const { state } = useApp();
  const [mobileOpen, setMobileOpen] = useState(false);


if (!state.userId ) {
  return (
    <div className={`${state.theme} palette-${state.colorPalette} ${state.glassmorphism ? 'glass-on' : 'glass-off'}`}>
      <MeshBackground />
      <NeonBackground />
      <AuthPage />
    </div>
  );
}
  const isRTL = state.lang === 'ar';
  const sidebarW = state.sidebarOpen ? FULL_W : RAIL_W;

  return (
    <div
      className={`app-shell ${state.theme} palette-${state.colorPalette} ${state.glassmorphism ? 'glass-on' : 'glass-off'} ${isRTL ? 'rtl' : 'ltr'}`}
      dir={isRTL ? 'rtl' : 'ltr'}
    >
      <MeshBackground />
      <NeonBackground />
      <div className={`sidebar-overlay ${mobileOpen ? 'vis' : ''}`} onClick={() => setMobileOpen(false)} />

      <Sidebar mobileOpen={mobileOpen} onClose={() => setMobileOpen(false)} />
      <SidebarToggle />

      <motion.div
        className="main-area"
        animate={{
          marginLeft:  isRTL ? 0 : sidebarW,
          marginRight: isRTL ? sidebarW : 0,
        }}
        transition={{ duration: 0.28, ease: [0.16, 1, 0.3, 1] }}
      >
        <Header onMenuClick={() => setMobileOpen(o => !o)} />
        <main className="main-content">
          <AnimatePresence mode="wait">
            <motion.div
              key={state.page}
              variants={pageVariants}
              initial="initial"
              animate="animate"
              exit="exit"
              transition={pageTransition}
            >
              {state.page === 'recommendation' && <RecommendationPage />}
              {state.page === 'comparison'     && <ComparisonPage />}
              {state.page === 'review'         && <ReviewPage />}
              {state.page === 'search'         && <SearchPage />}
              {state.page === 'settings'       && <SettingsPage />}
              {state.page === 'privacy'        && <PrivacyPage />}
              {state.page === 'terms'          && <TermsPage />}
              {!['recommendation','comparison','review','search','settings','privacy','terms'].includes(state.page) && <RecommendationPage />}
            </motion.div>
          </AnimatePresence>
        </main>
      </motion.div>

      <FloatingActionButton />
    </div>
  );
}

export default function App() {
  return (
    <AppProvider>
      <AppShell />
    </AppProvider>
  );
}
