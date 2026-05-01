# RECO AI — Frontend Documentation

**RECO** is a premium AI Shopping Assistant frontend built with React + TypeScript.  
*Intelligent. Airy. Expensive.* © 2026 RECO AI — All rights reserved.

---

## Quick Start

### Run (no build needed)
```bash
cd dist-ready
npx serve .
# Open → http://localhost:3000
```
> The 3D avatar (`avatar.glb`) requires a local server — do not open `index.html` directly from the filesystem.

### Development
```bash
npm install --legacy-peer-deps
npx parcel build index.html --dist-dir dist --no-source-maps
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| UI Framework | React 18 + TypeScript |
| Animation | Framer Motion |
| Styling | CSS Custom Properties (no Tailwind runtime) |
| Bundler | Parcel |
| State | React Context + useReducer |
| 3D | Three.js / @react-three/fiber (optional GLB) |
| Fonts | Inter, Syne, Cairo (Google Fonts) |

---

## Project Structure

```
src/
├── components/
│   ├── RECOAvatar.tsx        # Friendly robot SVG avatar — mouse-reactive, states
│   ├── RecoLogo.tsx          # Shopping cart brand logo SVG
│   ├── NeonBackground.tsx    # Canvas neon/AI background (toggleable)
│   ├── MeshBackground.tsx    # Mouse-reactive mesh gradient
│   ├── Sidebar.tsx           # Collapsible sidebar + icon rail
│   ├── SidebarToggle.tsx     # Claude-style pill toggle button
│   ├── Header.tsx            # Top navigation bar
│   ├── ChatBox.tsx           # Chat UI with avatar column
│   ├── FloatingActionButton.tsx  # FAB with quick-ask panel
│   └── ProductCards.tsx      # Product card grid
│
├── pages/
│   ├── AuthPage.tsx          # Login / Register / Guest
│   ├── RecommendationPage.tsx# AI product recommendations
│   ├── ComparisonPage.tsx    # Side-by-side comparison
│   ├── ReviewPage.tsx        # AI review analysis
│   ├── SearchPage.tsx        # Product search
│   ├── SettingsPage.tsx      # Theme, palette, avatar, toggles
│   ├── PrivacyPage.tsx       # Privacy Policy
│   └── TermsPage.tsx         # Terms of Service
│
├── store/
│   └── AppContext.tsx        # Global state (theme, lang, palette, etc.)
│
├── i18n/
│   └── translations.ts      # EN + AR strings
│
├── services/
│   └── api.ts               # Backend API client
│
└── styles/
    └── global.css           # Full design system (~2400 lines)
```

---

## Design System

### Color Palettes (6 total)

| Palette | Mode | Accent | Background |
|---------|------|--------|------------|
| **Cyber Amethyst** *(default)* | Dark | `#7c5cfc → #3b82f6` | `#080C14` |
| Obsidian & Orange | Dark | `#F97316` | `#0B0B0B` |
| Neon Purple | Dark | `#d946ef` | `#09020f` |
| Arctic White | Light | `#0ea5e9` | `#f0f9ff` |
| Emerald Dark | Dark | `#10b981` | `#020f09` |
| Rose Gold | Light | `#f43f5e` | `#fff1f2` |

Switch palette in **Settings → Color Palette**. Switching a dark palette auto-enables dark mode.

### Typography
- **Display / Headings**: Syne (800 weight) + Inter fallback  
- **Body**: Inter (`-0.011em` letter spacing — Apple-style)  
- **Arabic**: Cairo (RTL-optimised)

### Radius System
```
--r-xs: 6px   --r-sm: 10px  --r-md: 16px
--r-lg: 20px  --r-xl: 24px  --r-2xl: 32px
```

### Shadow System
Lavender-tinted layered shadows (no harsh black). Dark mode: purple-tinted depth.

---

## Avatar — `RECOAvatar`

Friendly white-helmet robot with glowing visor, headset, and shopping bag.

```tsx
<RECOAvatar
  size={120}           // px — scales proportionally
  avatarState="idle"   // 'idle' | 'listening' | 'thinking'
  interactive          // enables mouse eye-tracking
  showThoughts         // shows thought bubble with AI messages
/>
```

**States:**
- `idle` — gentle floating bob, random blinking
- `listening` — eyebrows raise, ear pulse rings, mouth animates  
- `thinking` — 3 forehead dots bounce, thought bubble cycles messages
- **Mouse tracking** — eyes follow cursor (clamped ±2.5px, smooth)

The avatar automatically switches to `listening` while the user types and `thinking` while the AI responds.

---

## Sidebar

- **Expanded** (256px): full navigation, history, upgrade card, user footer
- **Collapsed** (52px icon rail): logo mark + page icons + active dot indicator
- **Toggle**: Claude-style frosted-glass pill button at the sidebar edge

```
Sidebar → SidebarToggle button → animates width 256 ↔ 52px
Main area margin adjusts via Framer Motion (no layout jump)
```

---

## Settings

| Setting | Default | Description |
|---------|---------|-------------|
| Theme | Dark | Light / Dark |
| Color Palette | Cyber Amethyst | 6 palettes |
| Glassmorphism | Enabled | Frosted glass UI |
| Neon / AI Background | Disabled | Canvas grid + particles |
| Sidebar open | true | Persisted in state |
| Language | English | EN / AR (RTL) |

All settings persist via `localStorage`.

---

## Backend Integration

The app connects to a backend at `VITE_BACKEND_URL` (defaults to `http://127.0.0.1:8000`).

API calls are in `src/services/api.ts`:
- `login(email, password)`
- `register(name, email, password)`
- `createGuestUser()`
- `getSessions(userId, limit)`
- `getSessionMessages(sessionId, userId, limit)`

The UI degrades gracefully — all UI works without a backend, API calls fail silently.

---

## Internationalization (i18n)

Full EN + AR support. RTL layout via `dir="rtl"` on the root element.

Arabic includes: all navigation labels, settings titles, avatar thought messages, chat placeholders, empty states, user role labels.

---

## Legal

- **Privacy Policy**: `/pages/PrivacyPage.tsx` — effective date = login date
- **Terms of Service**: `/pages/TermsPage.tsx` — effective date = login date  
- Contact: asamir1000samira@gmail.com
- Governing law: Egypt

Accessible via **Settings → Privacy Policy / Terms of Service**.

---

## Browser Support

Chrome 90+, Firefox 88+, Safari 14+, Edge 90+.  
WebGL required for Neon Background canvas. Degrades gracefully without it.

---

## License & Copyright

© 2026 RECO AI — All rights reserved.  
All content, branding, and technology are proprietary.
