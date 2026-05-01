// RECO Brand Logo — Shopping cart with RECO wordmark + speed lines
// Faithful SVG recreation of the uploaded brand logo (Image 1)
// Speed lines on left, RECO text inside cart body, 4-point star in O, wheels below
import { motion } from 'framer-motion';

interface RecoLogoProps {
  size?: 'xs' | 'sm' | 'md' | 'lg';
  variant?: 'color' | 'white' | 'mono';
  animate?: boolean;
}

export default function RecoLogo({ size = 'md', variant = 'color', animate = false }: RecoLogoProps) {
  const widths: Record<string, number> = { xs: 72, sm: 108, md: 160, lg: 240 };
  const w = widths[size] ?? 160;
  const h = Math.round(w * 0.52);

  const col = variant === 'white' ? '#ffffff'
            : variant === 'mono' ? 'currentColor'
            : 'url(#recoCartGrad)';
  const colSolid = variant === 'white' ? '#ffffff'
                 : variant === 'mono' ? 'currentColor'
                 : '#5b4ef5';

  const Wrap = animate ? motion.svg : 'svg';
  const wrapProps = animate ? {
    initial: { opacity: 0, x: -8 },
    animate: { opacity: 1, x: 0 },
    transition: { duration: 0.45, ease: [0.16,1,0.3,1] as [number,number,number,number] },
  } : {};

  return (
    <Wrap
      viewBox="0 0 320 166"
      xmlns="http://www.w3.org/2000/svg"
      width={w}
      height={h}
      style={{ display: 'block', flexShrink: 0, overflow: 'visible' }}
      {...(wrapProps as any)}
    >
      <defs>
        <linearGradient id="recoCartGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="var(--c-accent-1,#7c5cfc)" />
          <stop offset="55%" stopColor="var(--c-accent-2,#5b4ef5)" />
          <stop offset="100%" stopColor="#4338ca" />
        </linearGradient>
        {/* Speed lines gradient — fades left */}
        <linearGradient id="speedGrad" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="var(--c-accent-1,#7c5cfc)" stopOpacity="0" />
          <stop offset="100%" stopColor="var(--c-accent-1,#7c5cfc)" stopOpacity="1" />
        </linearGradient>
      </defs>

      {/* ── SPEED LINES (left of R) ── */}
      {/* Top line */}
      <rect x="2"  y="44" width="60" height="7"  rx="3.5" fill="url(#speedGrad)" />
      {/* Middle line */}
      <rect x="8"  y="58" width="52" height="6"  rx="3"   fill="url(#speedGrad)" />
      {/* Bottom line */}
      <rect x="14" y="71" width="44" height="5"  rx="2.5" fill="url(#speedGrad)" />
      {/* Dot */}
      <circle cx="71" cy="88" r="4" fill={col} />

      {/* ── R ── bold rounded letterform */}
      {/* Vertical stem */}
      <rect x="76" y="32" width="14" height="72" rx="7" fill={col} />
      {/* Bowl — top arc */}
      <path d="M 76 32 Q 76 32 90 32 L 108 32 Q 126 32 126 50 Q 126 68 108 70 L 90 70" stroke={col} strokeWidth="14" fill="none" strokeLinecap="round" strokeLinejoin="round" />
      {/* Bowl fill */}
      <path d="M 90 32 L 108 32 Q 118 32 118 44 Q 118 56 108 58 L 90 58 Z" fill={col} />
      {/* Diagonal leg */}
      <line x1="94" y1="70" x2="120" y2="104" stroke={col} strokeWidth="14" strokeLinecap="round" />

      {/* ── E ── */}
      <rect x="135" y="32" width="14" height="72" rx="7" fill={col} />
      <rect x="135" y="32" width="52" height="14" rx="7" fill={col} />
      <rect x="135" y="63" width="44" height="12" rx="6" fill={col} />
      <rect x="135" y="90" width="52" height="14" rx="7" fill={col} />

      {/* ── C ── thick open arc ~300° */}
      <path d="M 236 38 A 44 44 0 1 0 236 96" stroke={col} strokeWidth="14" fill="none" strokeLinecap="round" />

      {/* ── O ── thick ring with 4-pt star ── */}
      <circle cx="286" cy="67" r="38" fill={col} />
      <circle cx="286" cy="67" r="24" fill={variant === 'white' ? 'rgba(0,0,0,0)' : 'var(--c-bg,#fff)'} />
      {/* 4-point star inside O */}
      <path d="M286 48 L289 61 L303 67 L289 73 L286 86 L283 73 L269 67 L283 61 Z" fill={col} />

      {/* ── CART BODY ── rounded rectangle bottom / basket */}
      <path
        d="M 76 108 L 274 108 Q 286 108 290 116 L 300 142 Q 302 148 296 148 L 80 148 Q 74 148 72 142 L 65 116 Q 63 108 76 108 Z"
        fill="none" stroke={col} strokeWidth="10" strokeLinejoin="round"
      />

      {/* Cart handle — top right arch */}
      <path
        d="M 280 108 Q 308 108 308 80 L 308 42 Q 308 32 298 32"
        fill="none" stroke={col} strokeWidth="12" strokeLinecap="round"
      />

      {/* ── WHEELS ── */}
      <circle cx="120" cy="160" r="14" fill={col} />
      <circle cx="120" cy="160" r="8"  fill={variant === 'white' ? 'rgba(255,255,255,0.2)' : 'var(--c-bg,#fff)'} />
      <circle cx="240" cy="160" r="14" fill={col} />
      <circle cx="240" cy="160" r="8"  fill={variant === 'white' ? 'rgba(255,255,255,0.2)' : 'var(--c-bg,#fff)'} />
    </Wrap>
  );
}
