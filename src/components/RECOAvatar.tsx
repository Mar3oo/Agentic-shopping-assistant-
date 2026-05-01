// RECO Friendly Robot Avatar — inspired by Image 2
// White helmet robot with dark visor, headset, shopping bag, glowing smile
// Mouse-reactive eyes, blink, thought bubbles, state animations
import { useEffect, useRef, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export type AvatarState = 'idle' | 'listening' | 'thinking';

interface RECOAvatarProps {
  size?: number;
  avatarState?: AvatarState;
  className?: string;
  interactive?: boolean;
  showThoughts?: boolean;
}

const THOUGHTS_EN = ['Searching best deals…','Comparing prices…','Analyzing reviews…','Finding top picks…','Checking ratings…'];
const THOUGHTS_AR = ['أبحث عن أفضل العروض…','أقارن الأسعار…','أحلل التقييمات…','أجد أفضل الخيارات…','أفحص التقييمات…'];

export default function RECOAvatar({ size = 120, avatarState = 'idle', className = '', interactive = true, showThoughts = false }: RECOAvatarProps) {
  const rootRef = useRef<HTMLDivElement>(null);
  const [eyeOffset, setEyeOffset] = useState({ x: 0, y: 0 });
  const [blink, setBlink] = useState(false);
  const [thoughtIdx, setThoughtIdx] = useState(0);
  const [isRTL, setIsRTL] = useState(false);

  useEffect(() => {
    setIsRTL(document.documentElement.dir === 'rtl' || document.body.dir === 'rtl');
  }, []);

  // Mouse tracking — subtle eye follow
  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!interactive || !rootRef.current) return;
    const rect = rootRef.current.getBoundingClientRect();
    const cx = rect.left + rect.width / 2;
    const cy = rect.top + rect.height / 2;
    const dx = (e.clientX - cx) / window.innerWidth;
    const dy = (e.clientY - cy) / window.innerHeight;
    setEyeOffset({
      x: Math.max(-2.5, Math.min(2.5, dx * 6)),
      y: Math.max(-2, Math.min(2, dy * 5)),
    });
  }, [interactive]);

  useEffect(() => {
    if (!interactive) return;
    window.addEventListener('mousemove', handleMouseMove, { passive: true });
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, [interactive, handleMouseMove]);

  // Blink
  useEffect(() => {
    const loop = () => {
      const t = setTimeout(() => {
        setBlink(true);
        setTimeout(() => setBlink(false), 130);
        loop();
      }, 2800 + Math.random() * 2800);
      return t;
    };
    const t = loop();
    return () => clearTimeout(t);
  }, []);

  // Thought cycling
  useEffect(() => {
    if (avatarState !== 'thinking') return;
    const t = setInterval(() => setThoughtIdx(i => (i + 1) % THOUGHTS_EN.length), 2000);
    return () => clearInterval(t);
  }, [avatarState]);

  const thoughts = isRTL ? THOUGHTS_AR : THOUGHTS_EN;
  const px = eyeOffset.x;
  const py = eyeOffset.y;

  // Scale factor
  const vw = 140; const vh = 170;

  return (
    <div
      ref={rootRef}
      className={`reco-avatar-root ${className}`}
      style={{ width: size, height: size * (vh / vw), position: 'relative', display: 'inline-flex', flexDirection: 'column', alignItems: 'center' }}
    >
      {/* Thought bubble */}
      <AnimatePresence>
        {(avatarState === 'thinking' || showThoughts) && (
          <motion.div
            className="reco-thought-bubble"
            key={thoughtIdx}
            initial={{ opacity: 0, y: 5, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -4, scale: 0.93 }}
            transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
          >
            <span className="reco-thought-dots"><span /><span /><span /></span>
            <span className="reco-thought-text">{thoughts[thoughtIdx]}</span>
          </motion.div>
        )}
      </AnimatePresence>

      <motion.svg
        viewBox={`0 0 ${vw} ${vh}`}
        xmlns="http://www.w3.org/2000/svg"
        width={size}
        height={size * (vh / vw)}
        style={{ overflow: 'visible', position: 'relative', zIndex: 1 }}
        animate={{
          y: avatarState === 'listening' ? [0, -4, 0] : avatarState === 'thinking' ? [0, -2, 0] : [0, -2, 0],
          rotate: avatarState === 'listening' ? [-1, 1, -1] : 0,
        }}
        transition={{
          duration: avatarState === 'idle' ? 3 : 1.4,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
      >
        <defs>
          {/* Purple gradient background circle */}
          <radialGradient id="bgCircle" cx="45%" cy="38%" r="60%">
            <stop offset="0%" stopColor="var(--c-accent-1,#7c5cfc)" />
            <stop offset="60%" stopColor="var(--c-accent-2,#5b4ef5)" />
            <stop offset="100%" stopColor="#3730a3" />
          </radialGradient>

          {/* White helmet gradient */}
          <radialGradient id="helmetGrad" cx="38%" cy="28%" r="62%">
            <stop offset="0%" stopColor="#ffffff" />
            <stop offset="55%" stopColor="#e8e8f0" />
            <stop offset="100%" stopColor="#c8c8e0" />
          </radialGradient>

          {/* Visor gradient — dark with purple glow */}
          <radialGradient id="visorGrad" cx="40%" cy="40%" r="60%">
            <stop offset="0%" stopColor="#1a1040" />
            <stop offset="70%" stopColor="#0d0820" />
            <stop offset="100%" stopColor="#080414" />
          </radialGradient>

          {/* Body white gradient */}
          <radialGradient id="bodyWhite" cx="35%" cy="25%" r="65%">
            <stop offset="0%" stopColor="#ffffff" />
            <stop offset="60%" stopColor="#ddddf0" />
            <stop offset="100%" stopColor="#b8b8d8" />
          </radialGradient>

          {/* Shopping bag gradient */}
          <radialGradient id="bagGrad" cx="40%" cy="30%" r="60%">
            <stop offset="0%" stopColor="var(--c-accent-1,#7c5cfc)" />
            <stop offset="100%" stopColor="#4338ca" />
          </radialGradient>

          {/* Glow filter for visor */}
          <filter id="visorGlow" x="-15%" y="-15%" width="130%" height="130%">
            <feGaussianBlur stdDeviation="2.5" result="blur" />
            <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>

          {/* Drop shadow */}
          <filter id="robotShadow" x="-15%" y="-8%" width="130%" height="130%">
            <feDropShadow dx="0" dy="6" stdDeviation="10" floodColor="rgba(79,70,229,0.4)" />
          </filter>

          {/* Smile glow */}
          <filter id="smileGlow" x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur stdDeviation="2" result="blur" />
            <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
        </defs>

        {/* ── BACKGROUND CIRCLE ── */}
        <circle cx="70" cy="85" r="72" fill="url(#bgCircle)" filter="url(#robotShadow)" />
        {/* Inner highlight on bg */}
        <ellipse cx="52" cy="52" rx="36" ry="28" fill="rgba(255,255,255,0.10)" />

        {/* ── SPEECH BUBBLE (top right) ── */}
        <g transform="translate(92, 18)">
          <rect x="0" y="0" width="38" height="28" rx="8" fill="rgba(255,255,255,0.92)" />
          <polygon points="8,28 14,38 20,28" fill="rgba(255,255,255,0.92)" />
          {/* Cart icon inside bubble */}
          <path d="M8 8 L11 8 L14 20 L28 20 L30 12 L13 12" stroke="var(--c-accent-2,#5b4ef5)" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round" />
          <circle cx="16" cy="23" r="2" fill="var(--c-accent-2,#5b4ef5)" />
          <circle cx="26" cy="23" r="2" fill="var(--c-accent-2,#5b4ef5)" />
        </g>

        {/* ── BODY / TORSO ── */}
        <motion.g
          animate={{ scaleY: avatarState === 'listening' ? 1.02 : 1 }}
          transition={{ type: 'spring', stiffness: 200, damping: 20 }}
          style={{ transformOrigin: '70px 130px' }}
        >
          {/* Main torso shape */}
          <path d="M 34 118 Q 28 140 30 158 L 110 158 Q 112 140 106 118 Q 90 110 70 110 Q 50 110 34 118 Z" fill="url(#bodyWhite)" />

          {/* Chest AI badge */}
          <rect x="52" y="128" width="36" height="28" rx="8" fill="url(#bagGrad)" />
          {/* Shopping bag icon on chest */}
          <path d="M60 136 Q60 132 70 132 Q80 132 80 136" stroke="white" strokeWidth="2" fill="none" strokeLinecap="round" />
          <rect x="60" y="134" width="20" height="16" rx="4" fill="none" stroke="white" strokeWidth="1.8" />
          <text x="70" y="147" textAnchor="middle" fill="white" fontSize="8" fontWeight="700" fontFamily="Inter,sans-serif">AI</text>

          {/* Left shoulder */}
          <ellipse cx="32" cy="120" rx="14" ry="16" fill="url(#bodyWhite)" />
          <ellipse cx="32" cy="120" rx="9" ry="10" fill="rgba(255,255,255,0.5)" />

          {/* Right shoulder */}
          <ellipse cx="108" cy="120" rx="14" ry="16" fill="url(#bodyWhite)" />
          <ellipse cx="108" cy="120" rx="9" ry="10" fill="rgba(255,255,255,0.5)" />

          {/* Shoulder accent rings — purple */}
          <circle cx="32" cy="112" r="5" fill="var(--c-accent-1,#7c5cfc)" />
          <circle cx="108" cy="112" r="5" fill="var(--c-accent-1,#7c5cfc)" />

          {/* ── LEFT ARM (holding shopping bag) ── */}
          <motion.g
            animate={{ rotate: avatarState === 'thinking' ? [0, -8, 0] : [-3, 3, -3] }}
            transition={{ duration: avatarState === 'thinking' ? 0.8 : 3, repeat: Infinity, ease: 'easeInOut' }}
            style={{ transformOrigin: '28px 125px' }}
          >
            <rect x="14" y="124" width="12" height="30" rx="6" fill="url(#bodyWhite)" />
            {/* Shopping bag */}
            <motion.g
              animate={{ y: [0, -2, 0] }}
              transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
            >
              {/* Bag body */}
              <path d="M4 150 Q2 148 2 145 L4 138 Q5 136 8 136 L22 136 Q25 136 26 138 L28 145 Q28 148 26 150 Z" fill="url(#bagGrad)" />
              {/* Bag handles */}
              <path d="M9 136 Q9 130 15 130 Q21 130 21 136" stroke="var(--c-accent-2,#5b4ef5)" strokeWidth="2" fill="none" strokeLinecap="round" />
              {/* Bag shine */}
              <path d="M8 140 L10 145" stroke="rgba(255,255,255,0.4)" strokeWidth="1.5" strokeLinecap="round" />
            </motion.g>
          </motion.g>

          {/* ── RIGHT ARM ── */}
          <rect x="114" y="124" width="12" height="26" rx="6" fill="url(#bodyWhite)" />
          <ellipse cx="120" cy="152" rx="8" ry="6" fill="#d0d0e8" />
        </motion.g>

        {/* ── HEAD / HELMET ── */}
        <motion.g
          animate={{ y: avatarState === 'listening' ? -2 : 0 }}
          transition={{ type: 'spring', stiffness: 160, damping: 18 }}
        >
          {/* Helmet outer — white rounded */}
          <ellipse cx="70" cy="80" rx="42" ry="44" fill="url(#helmetGrad)" />

          {/* Helmet highlight top */}
          <ellipse cx="58" cy="56" rx="18" ry="12" fill="rgba(255,255,255,0.55)" />

          {/* ── HEADSET ── */}
          {/* Left ear cup */}
          <ellipse cx="28" cy="80" rx="8" ry="11" fill="var(--c-accent-1,#7c5cfc)" />
          <ellipse cx="28" cy="80" rx="5" ry="7" fill="#3730a3" />
          {/* Right ear cup */}
          <ellipse cx="112" cy="80" rx="8" ry="11" fill="var(--c-accent-1,#7c5cfc)" />
          <ellipse cx="112" cy="80" rx="5" ry="7" fill="#3730a3" />
          {/* Headband */}
          <path d="M 28 70 Q 28 38 70 36 Q 112 38 112 70" fill="none" stroke="var(--c-accent-1,#7c5cfc)" strokeWidth="5" strokeLinecap="round" />
          {/* Mic boom */}
          <path d="M 28 88 Q 22 92 20 98 Q 18 104 24 106" fill="none" stroke="var(--c-accent-2,#5b4ef5)" strokeWidth="3" strokeLinecap="round" />
          <circle cx="24" cy="107" r="4" fill="var(--c-accent-2,#5b4ef5)" />

          {/* ── VISOR ── dark face plate */}
          <rect x="38" y="62" width="64" height="40" rx="20" fill="url(#visorGrad)" />
          {/* Visor inner light */}
          <rect x="41" y="65" width="58" height="34" rx="17" fill="rgba(100,80,200,0.12)" />
          {/* Visor glass shine */}
          <path d="M 44 70 Q 54 66 64 68" stroke="rgba(255,255,255,0.2)" strokeWidth="2" fill="none" strokeLinecap="round" />

          {/* ── EYES (glowing arcs inside visor — smiling) ── */}
          {blink ? (
            <>
              <line x1="52" y1="79" x2="64" y2="79" stroke="rgba(167,139,250,0.9)" strokeWidth="3" strokeLinecap="round" />
              <line x1="76" y1="79" x2="88" y2="79" stroke="rgba(167,139,250,0.9)" strokeWidth="3" strokeLinecap="round" />
            </>
          ) : (
            <>
              {/* Left eye — arc shape (happy curved line = happy expression) */}
              <motion.path
                d={avatarState === 'thinking'
                  ? `M ${52+px} ${83+py} Q ${58+px} ${76+py} ${64+px} ${83+py}`
                  : `M ${52+px} ${82+py} Q ${58+px} ${75+py} ${64+px} ${82+py}`
                }
                stroke="rgba(196,181,253,0.95)" strokeWidth="3.5" fill="none" strokeLinecap="round"
                filter="url(#smileGlow)"
                animate={{ d: avatarState === 'listening'
                  ? [`M ${52+px} ${80+py} Q ${58+px} ${72+py} ${64+px} ${80+py}`,
                     `M ${52+px} ${82+py} Q ${58+px} ${74+py} ${64+px} ${82+py}`]
                  : undefined
                }}
                transition={{ duration: 0.6, repeat: Infinity, repeatType: 'reverse' }}
              />
              {/* Right eye */}
              <motion.path
                d={avatarState === 'thinking'
                  ? `M ${76+px} ${83+py} Q ${82+px} ${76+py} ${88+px} ${83+py}`
                  : `M ${76+px} ${82+py} Q ${82+px} ${75+py} ${88+px} ${82+py}`
                }
                stroke="rgba(196,181,253,0.95)" strokeWidth="3.5" fill="none" strokeLinecap="round"
                filter="url(#smileGlow)"
                animate={{ d: avatarState === 'listening'
                  ? [`M ${76+px} ${80+py} Q ${82+px} ${72+py} ${88+px} ${80+py}`,
                     `M ${76+px} ${82+py} Q ${82+px} ${74+py} ${88+px} ${82+py}`]
                  : undefined
                }}
                transition={{ duration: 0.6, repeat: Infinity, repeatType: 'reverse', delay: 0.08 }}
              />
              {/* Eye glow dots */}
              <circle cx={59+px} cy={85+py} r="2" fill="rgba(167,139,250,0.6)" filter="url(#smileGlow)" />
              <circle cx={83+px} cy={85+py} r="2" fill="rgba(167,139,250,0.6)" filter="url(#smileGlow)" />
            </>
          )}

          {/* ── SMILE ── glowing curved line */}
          <motion.path
            d="M 54 96 Q 70 106 86 96"
            stroke="rgba(196,181,253,0.88)" strokeWidth="3" fill="none" strokeLinecap="round"
            filter="url(#smileGlow)"
            animate={{ d: avatarState === 'listening'
              ? ['M 54 96 Q 70 108 86 96', 'M 54 96 Q 70 106 86 96']
              : 'M 54 96 Q 70 106 86 96'
            }}
            transition={{ duration: 0.5, repeat: Infinity, repeatType: 'reverse' }}
          />

          {/* Thinking dots on visor */}
          {avatarState === 'thinking' && (
            <g>
              {[0,1,2].map(i => (
                <motion.circle
                  key={i}
                  cx={56 + i * 14} cy="75" r="3.5"
                  fill="rgba(196,181,253,0.85)"
                  filter="url(#smileGlow)"
                  animate={{ y: [0,-5,0], opacity:[0.5,1,0.5] }}
                  transition={{ duration: 0.8, delay: i*0.16, repeat: Infinity }}
                />
              ))}
            </g>
          )}
        </motion.g>

        {/* Listening pulse rings from ears */}
        {avatarState === 'listening' && [1,2].map(i => (
          <motion.circle key={i} cx="28" cy="80" r={10}
            fill="none" stroke="var(--c-accent-1,#7c5cfc)" strokeWidth="1.5"
            animate={{ r:[10,10+i*10], opacity:[0.8,0] }}
            transition={{ duration: 1, delay: i*0.35, repeat: Infinity }}
          />
        ))}
      </motion.svg>
    </div>
  );
}
