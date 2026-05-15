// RECO Living Nebula Avatar — "Friendly Digital Core"
// Organic multi-layered vector with pulse, orbital ring, and listening eyes
import { motion, useAnimation } from 'framer-motion';
import { useEffect, useState } from 'react';

type AvatarState = 'idle' | 'listening' | 'thinking';

interface NebulaAvatarProps {
  size?: number;
  state?: AvatarState;
  className?: string;
}

export default function NebulaAvatar({ size = 120, state: avatarState = 'idle', className = '' }: NebulaAvatarProps) {
  const [hovered, setHovered] = useState(false);
  const coreControls = useAnimation();

  useEffect(() => {
    if (avatarState === 'thinking') {
      coreControls.start({ rotate: 360, transition: { duration: 2, ease: 'linear', repeat: Infinity } });
    } else {
      coreControls.start({ rotate: 0, transition: { duration: 0.4 } });
    }
  }, [avatarState, coreControls]);

  const eyeY = avatarState === 'listening' ? -3 : 0;
  const eyeScale = avatarState === 'thinking' ? 1.3 : 1;

  return (
    <div
      className={`nebula-avatar-root ${className}`}
      style={{ width: size, height: size, position: 'relative', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer' }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg" width={size} height={size} style={{ position: 'relative', zIndex: 2, overflow: 'visible' }}>
        <defs>
          {/* Core gradient — Cyber Amethyst */}
          <radialGradient id="nebCore" cx="40%" cy="35%" r="65%">
            <stop offset="0%"   stopColor="#a78bfa" stopOpacity="1" />
            <stop offset="40%"  stopColor="#7c5cfc" stopOpacity="1" />
            <stop offset="75%"  stopColor="#4f46e5" stopOpacity="1" />
            <stop offset="100%" stopColor="#1e1b6e" stopOpacity="1" />
          </radialGradient>

          {/* Inner nebula — electric blue */}
          <radialGradient id="nebInner" cx="55%" cy="45%" r="55%">
            <stop offset="0%"   stopColor="#60a5fa" stopOpacity="0.9" />
            <stop offset="50%"  stopColor="#3b82f6" stopOpacity="0.7" />
            <stop offset="100%" stopColor="#1d4ed8" stopOpacity="0.4" />
          </radialGradient>

          {/* Outer bloom */}
          <radialGradient id="nebBloom" cx="50%" cy="50%" r="50%">
            <stop offset="0%"   stopColor="#7c5cfc" stopOpacity="0.4" />
            <stop offset="60%"  stopColor="#4f46e5" stopOpacity="0.15" />
            <stop offset="100%" stopColor="#4f46e5" stopOpacity="0" />
          </radialGradient>

          {/* Ring gradient */}
          <linearGradient id="nebRing" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%"   stopColor="#a78bfa" stopOpacity="0.9" />
            <stop offset="50%"  stopColor="#60a5fa" stopOpacity="0.6" />
            <stop offset="100%" stopColor="#7c5cfc" stopOpacity="0.8" />
          </linearGradient>

          {/* Glow filter */}
          <filter id="nebGlow" x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur stdDeviation="6" result="blur" />
            <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>

          {/* Soft inner light */}
          <filter id="softLight" x="-10%" y="-10%" width="120%" height="120%">
            <feGaussianBlur stdDeviation="2.5" result="blur" />
            <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>

          {/* Clip to circle */}
          <clipPath id="nebClip">
            <circle cx="100" cy="100" r="72" />
          </clipPath>
        </defs>

        {/* ── OUTER BLOOM ── */}
        <motion.circle
          cx="100" cy="100" r="90"
          fill="url(#nebBloom)"
          animate={{ scale: hovered ? 1.08 : [1, 1.04, 1] }}
          transition={hovered ? { duration: 0.3 } : { duration: 3.5, repeat: Infinity, ease: 'easeInOut' }}
        />

        {/* ── ORBITAL RING (shifts during listening) ── */}
        <motion.g
          animate={avatarState === 'listening'
            ? { rotate: [-8, 8, -8] }
            : { rotate: [0, 360] }
          }
          transition={avatarState === 'listening'
            ? { duration: 1.2, repeat: Infinity, ease: 'easeInOut' }
            : { duration: 18, repeat: Infinity, ease: 'linear' }
          }
          style={{ transformOrigin: '100px 100px' }}
        >
          <ellipse cx="100" cy="100" rx="78" ry="22"
            fill="none" stroke="url(#nebRing)" strokeWidth="1.5" strokeDasharray="8 6" opacity="0.7"
          />
          {/* Orbital dot */}
          <circle cx="178" cy="100" r="4" fill="#a78bfa" filter="url(#softLight)" />
          <circle cx="22"  cy="100" r="2.5" fill="#60a5fa" opacity="0.7" />
        </motion.g>

        {/* ── SECONDARY RING ── */}
        <motion.g
          animate={{ rotate: [0, -360] }}
          transition={{ duration: 25, repeat: Infinity, ease: 'linear' }}
          style={{ transformOrigin: '100px 100px' }}
        >
          <ellipse cx="100" cy="100" rx="60" ry="78"
            fill="none" stroke="rgba(167,139,250,0.25)" strokeWidth="1" strokeDasharray="4 8"
          />
        </motion.g>

        {/* ── MAIN CORE BODY ── */}
        {/* Organic outer blob */}
        <motion.path
          d="M 100 28 C 128 28 160 48 166 78 C 172 108 156 142 128 156 C 100 170 68 158 50 136 C 32 114 34 76 54 56 C 70 40 80 28 100 28 Z"
          fill="url(#nebCore)"
          clipPath="url(#nebClip)"
          animate={{ d: hovered
            ? "M 100 26 C 130 26 162 46 168 78 C 174 110 156 144 128 158 C 98 172 66 160 48 136 C 30 112 32 72 52 52 C 68 36 78 26 100 26 Z"
            : [
              "M 100 28 C 128 28 160 48 166 78 C 172 108 156 142 128 156 C 100 170 68 158 50 136 C 32 114 34 76 54 56 C 70 40 80 28 100 28 Z",
              "M 100 30 C 126 30 158 50 164 80 C 170 110 154 144 126 158 C 98 170 66 160 48 136 C 30 112 34 74 54 54 C 72 38 82 30 100 30 Z",
              "M 100 28 C 128 28 160 48 166 78 C 172 108 156 142 128 156 C 100 170 68 158 50 136 C 32 114 34 76 54 56 C 70 40 80 28 100 28 Z",
            ]
          }}
          transition={hovered ? { duration: 0.4 } : { duration: 5, repeat: Infinity, ease: 'easeInOut' }}
        />

        {/* Inner light layer */}
        <motion.ellipse
          cx="95" cy="88" rx="42" ry="40"
          fill="url(#nebInner)"
          clipPath="url(#nebClip)"
          animate={{ cx: [95, 98, 95], cy: [88, 92, 88], rx: [42, 44, 42] }}
          transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
        />

        {/* Bright core hotspot */}
        <motion.ellipse
          cx="88" cy="82" rx="18" ry="16"
          fill="rgba(196,181,253,0.55)"
          clipPath="url(#nebClip)"
          filter="url(#softLight)"
          animate={{ cx: [88, 92, 88], cy: [82, 86, 82] }}
          transition={{ duration: 3.5, repeat: Infinity, ease: 'easeInOut' }}
        />

        {/* ── MINIMALIST EYES ── */}
        {/* Left eye */}
        <motion.g
          animate={{ y: eyeY, scaleY: eyeScale }}
          transition={{ duration: 0.4, ease: [0.34, 1.56, 0.64, 1] }}
          style={{ transformOrigin: '85px 96px' }}
        >
          <ellipse cx="85" cy="96" rx="7" ry={avatarState === 'thinking' ? 4 : 6}
            fill="rgba(255,255,255,0.92)" filter="url(#softLight)"
          />
          <ellipse cx="86" cy="97" rx="3.5" ry="3.5" fill="#1e1b6e" />
          <ellipse cx="87.5" cy="95.5" rx="1.5" ry="1.5" fill="rgba(255,255,255,0.9)" />
        </motion.g>

        {/* Right eye */}
        <motion.g
          animate={{ y: eyeY, scaleY: eyeScale }}
          transition={{ duration: 0.4, ease: [0.34, 1.56, 0.64, 1] }}
          style={{ transformOrigin: '115px 96px' }}
        >
          <ellipse cx="115" cy="96" rx="7" ry={avatarState === 'thinking' ? 4 : 6}
            fill="rgba(255,255,255,0.92)" filter="url(#softLight)"
          />
          <ellipse cx="116" cy="97" rx="3.5" ry="3.5" fill="#1e1b6e" />
          <ellipse cx="117.5" cy="95.5" rx="1.5" ry="1.5" fill="rgba(255,255,255,0.9)" />
        </motion.g>

        {/* Subtle smile / arc when idle */}
        {avatarState === 'idle' && (
          <path d="M 88 112 Q 100 118 112 112"
            stroke="rgba(255,255,255,0.5)" strokeWidth="2"
            fill="none" strokeLinecap="round"
          />
        )}

        {/* Listening indicator — animated arc */}
        {avatarState === 'listening' && (
          <motion.path
            d="M 82 116 Q 100 124 118 116"
            stroke="rgba(167,139,250,0.8)" strokeWidth="2.5"
            fill="none" strokeLinecap="round"
            animate={{ d: ['M 82 116 Q 100 124 118 116', 'M 82 112 Q 100 120 118 112', 'M 82 116 Q 100 124 118 116'] }}
            transition={{ duration: 0.8, repeat: Infinity, ease: 'easeInOut' }}
          />
        )}

        {/* ── SPARKLE PARTICLES ── */}
        {[
          { cx: 145, cy: 55, r: 2.5, delay: 0 },
          { cx: 55,  cy: 148, r: 2,   delay: 0.8 },
          { cx: 158, cy: 130, r: 1.8, delay: 1.5 },
          { cx: 44,  cy: 70,  r: 2,   delay: 2.2 },
        ].map((p, i) => (
          <motion.circle
            key={i}
            cx={p.cx} cy={p.cy} r={p.r}
            fill="#c4b5fd"
            filter="url(#softLight)"
            animate={{ opacity: [0, 1, 0], scale: [0.5, 1.2, 0.5] }}
            transition={{ duration: 2.5, repeat: Infinity, delay: p.delay, ease: 'easeInOut' }}
          />
        ))}
      </svg>

      {/* State tooltip badge */}
      {avatarState !== 'idle' && (
        <motion.div
          className="nebula-state-badge"
          initial={{ opacity: 0, y: 4, scale: 0.9 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0 }}
        >
          {avatarState === 'listening' ? '● Listening' : '◌ Thinking...'}
        </motion.div>
      )}
    </div>
  );
}
