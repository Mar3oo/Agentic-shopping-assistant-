import React, { createContext, useContext, useReducer } from 'react';

export type UserMode = 'guest' | 'registered' | null;
export type Lang = 'en' | 'ar';
export type Theme = 'light' | 'dark';
export type Page = 'auth' | 'recommendation' | 'comparison' | 'review' | 'search' | 'settings' | 'privacy' | 'terms';
export type ColorPalette = 'cyber-amethyst' | 'obsidian-orange' | 'neon-purple' | 'arctic-white' | 'emerald-dark' | 'rose-gold';

export interface Product {
  title?: string;
  price?: string | number;
  price_text?: string;
  currency?: string;
  source?: string;
  details_text?: string;
  link?: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  payload?: Record<string, unknown>;
}

export interface AppState {
  // Auth
  userId: string | null;
  userMode: UserMode;
  userEmail: string | null;
  displayName: string | null;
  loginDate: string | null;
  // Navigation
  page: Page;
  sidebarOpen: boolean;
  // Theme / Lang / Palette
  theme: Theme;
  lang: Lang;
  colorPalette: ColorPalette;
  glassmorphism: boolean;
  neonBg: boolean;
  // Recommendation
  recommendationSessionId: string | null;
  recommendationMessages: ChatMessage[];
  recommendationProducts: Product[];
  recommendationSuggestions: Array<{ message: string }>;
  selectedReviewProduct: string | null;
  // Comparison
  comparisonSessionId: string | null;
  comparisonMessages: ChatMessage[];
  comparisonResult: Record<string, unknown> | null;
  // Review
  reviewSessionId: string | null;
  reviewMessages: ChatMessage[];
  reviewResult: Record<string, unknown> | null;
  // Search
  searchResults: Product[];
  // Sessions history
  sessions: Array<Record<string, unknown>>;
  activeSessionId: string | null;
}

const defaultState: AppState = {
  userId: null, userMode: null, userEmail: null, displayName: null, loginDate: null,
  page: 'auth',
  sidebarOpen: true,
  theme: (localStorage.getItem('reco-theme') as Theme) || 'dark',
  lang: (localStorage.getItem('reco-lang') as Lang) || 'en',
  colorPalette: (localStorage.getItem('reco-palette') as ColorPalette) || 'cyber-amethyst',
  glassmorphism: localStorage.getItem('reco-glass') !== 'false',
  neonBg: localStorage.getItem('reco-neon') === 'true',
  recommendationSessionId: null, recommendationMessages: [], recommendationProducts: [], recommendationSuggestions: [], selectedReviewProduct: null,
  comparisonSessionId: null, comparisonMessages: [], comparisonResult: null,
  reviewSessionId: null, reviewMessages: [], reviewResult: null,
  searchResults: [],
  sessions: [], activeSessionId: null,
};

type Action =
  | { type: 'SET_USER'; payload: { userId: string; userMode: UserMode; userEmail?: string; displayName?: string } }
  | { type: 'LOGOUT' }
  | { type: 'SET_PAGE'; payload: Page }
  | { type: 'SET_THEME'; payload: Theme }
  | { type: 'SET_LANG'; payload: Lang }
  | { type: 'SET_PALETTE'; payload: ColorPalette }
  | { type: 'SET_GLASS'; payload: boolean }
  | { type: 'SET_NEON'; payload: boolean }
  | { type: 'TOGGLE_SIDEBAR' }
  | { type: 'SET_SIDEBAR'; payload: boolean }
  | { type: 'SET_RECOMMENDATION'; payload: Partial<AppState> }
  | { type: 'SET_COMPARISON'; payload: Partial<AppState> }
  | { type: 'SET_REVIEW'; payload: Partial<AppState> }
  | { type: 'SET_SEARCH_RESULTS'; payload: Product[] }
  | { type: 'APPEND_MSG'; payload: { agent: 'recommendation' | 'comparison' | 'review'; msg: ChatMessage } }
  | { type: 'SET_SESSIONS'; payload: Array<Record<string, unknown>> }
  | { type: 'SET_ACTIVE_SESSION'; payload: string | null }
  | { type: 'RESET_AGENT'; payload: 'recommendation' | 'comparison' | 'review' };

function reducer(state: AppState, action: Action): AppState {
  switch (action.type) {
    case 'SET_USER':
      return { ...state, ...action.payload, page: 'recommendation', loginDate: new Date().toLocaleDateString('en-US', { year:'numeric', month:'long', day:'numeric' }) };
    case 'LOGOUT':
      return { ...defaultState, theme: state.theme, lang: state.lang, colorPalette: state.colorPalette, glassmorphism: state.glassmorphism, neonBg: state.neonBg, page: 'auth' };
    case 'SET_PAGE':
      return { ...state, page: action.payload };
    case 'SET_THEME':
      localStorage.setItem('reco-theme', action.payload);
      return { ...state, theme: action.payload };
    case 'SET_LANG':
      localStorage.setItem('reco-lang', action.payload);
      return { ...state, lang: action.payload };
    case 'SET_PALETTE':
      localStorage.setItem('reco-palette', action.payload);
      return { ...state, colorPalette: action.payload };
    case 'SET_NEON':
      localStorage.setItem('reco-neon', String(action.payload));
      return { ...state, neonBg: action.payload };
    case 'SET_GLASS':
      localStorage.setItem('reco-glass', String(action.payload));
      return { ...state, glassmorphism: action.payload };
    case 'TOGGLE_SIDEBAR':
      return { ...state, sidebarOpen: !state.sidebarOpen };
    case 'SET_SIDEBAR':
      return { ...state, sidebarOpen: action.payload };
    case 'SET_RECOMMENDATION':
      return { ...state, ...action.payload };
    case 'SET_COMPARISON':
      return { ...state, ...action.payload };
    case 'SET_REVIEW':
      return { ...state, ...action.payload };
    case 'SET_SEARCH_RESULTS':
      return { ...state, searchResults: action.payload };
    case 'APPEND_MSG': {
      const key = `${action.payload.agent}Messages` as keyof AppState;
      const prev = (state[key] as ChatMessage[]) || [];
      return { ...state, [key]: [...prev, action.payload.msg] };
    }
    case 'SET_SESSIONS':
      return { ...state, sessions: action.payload };
    case 'SET_ACTIVE_SESSION':
      return { ...state, activeSessionId: action.payload };
    case 'RESET_AGENT':
      if (action.payload === 'recommendation')
        return { ...state, recommendationSessionId: null, recommendationMessages: [], recommendationProducts: [], recommendationSuggestions: [], selectedReviewProduct: null };
      if (action.payload === 'comparison')
        return { ...state, comparisonSessionId: null, comparisonMessages: [], comparisonResult: null };
      if (action.payload === 'review')
        return { ...state, reviewSessionId: null, reviewMessages: [], reviewResult: null };
      return state;
    default:
      return state;
  }
}

interface ContextType {
  state: AppState;
  dispatch: React.Dispatch<Action>;
}

const Ctx = createContext<ContextType | null>(null);

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(reducer, defaultState);
  return <Ctx.Provider value={{ state, dispatch }}>{children}</Ctx.Provider>;
}

export function useApp() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error('useApp must be used inside AppProvider');
  return ctx;
}

export function useDispatch() {
  return useApp().dispatch;
}
