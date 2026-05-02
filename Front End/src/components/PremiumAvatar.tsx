import { motion } from 'framer-motion';

export default function PremiumAvatar({ size = 120, className = '' }: { size?: number; className?: string }) {
  return (
    <motion.div
      className={`premium-avatar-wrap ${className}`}
      style={{ width: size, height: size }}
      initial={{ scale: 0.9, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
    >
      {/* Glow ring */}
      <div className="avatar-glow-ring" />
      {/* Orbit ring */}
      <div className="avatar-orbit-ring" />
      {/* Floating dot top-right */}
      <div className="avatar-float-dot top-dot" />
      {/* Floating dot bottom-left */}
      <div className="avatar-float-dot btm-dot" />

      <svg
        viewBox="0 0 200 200"
        xmlns="http://www.w3.org/2000/svg"
        width={size}
        height={size}
        style={{ position: 'relative', zIndex: 2, filter: 'drop-shadow(0 24px 48px rgba(79,70,229,0.22)) drop-shadow(0 8px 16px rgba(0,0,0,0.14))' }}
      >
        <defs>
          {/* Background sphere gradient */}
          <radialGradient id="bgSphere" cx="42%" cy="32%" r="60%">
            <stop offset="0%" stopColor="#e8eaf6" />
            <stop offset="60%" stopColor="#c5cae9" />
            <stop offset="100%" stopColor="#9fa8da" />
          </radialGradient>

          {/* Skin gradient - warm matte */}
          <radialGradient id="skinBase" cx="44%" cy="36%" r="58%">
            <stop offset="0%" stopColor="#f5cba7" />
            <stop offset="45%" stopColor="#e8a87c" />
            <stop offset="80%" stopColor="#d4845a" />
            <stop offset="100%" stopColor="#c27048" />
          </radialGradient>

          {/* Skin shadow */}
          <radialGradient id="skinShadow" cx="50%" cy="80%" r="55%">
            <stop offset="0%" stopColor="rgba(100,50,20,0.35)" />
            <stop offset="100%" stopColor="rgba(100,50,20,0)" />
          </radialGradient>

          {/* Neck gradient */}
          <linearGradient id="neckGrad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#e8a87c" />
            <stop offset="100%" stopColor="#c47a4e" />
          </linearGradient>

          {/* Turtleneck gradient */}
          <linearGradient id="turtleGrad" x1="20%" y1="0%" x2="80%" y2="100%">
            <stop offset="0%" stopColor="#2c2c3e" />
            <stop offset="40%" stopColor="#1e1e2e" />
            <stop offset="100%" stopColor="#13131f" />
          </linearGradient>

          {/* Turtleneck fabric sheen */}
          <linearGradient id="turtleSheen" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="rgba(255,255,255,0)" />
            <stop offset="35%" stopColor="rgba(255,255,255,0.07)" />
            <stop offset="65%" stopColor="rgba(255,255,255,0.03)" />
            <stop offset="100%" stopColor="rgba(255,255,255,0)" />
          </linearGradient>

          {/* Hair gradient */}
          <radialGradient id="hairGrad" cx="50%" cy="25%" r="60%">
            <stop offset="0%" stopColor="#3d2b1f" />
            <stop offset="55%" stopColor="#1a1008" />
            <stop offset="100%" stopColor="#0d0804" />
          </radialGradient>

          {/* Hair sheen */}
          <radialGradient id="hairSheen" cx="38%" cy="22%" r="35%">
            <stop offset="0%" stopColor="rgba(255,220,170,0.18)" />
            <stop offset="100%" stopColor="rgba(255,220,170,0)" />
          </radialGradient>

          {/* Eye iris */}
          <radialGradient id="irisGrad" cx="38%" cy="35%" r="62%">
            <stop offset="0%" stopColor="#5b7fc4" />
            <stop offset="55%" stopColor="#2d5a8e" />
            <stop offset="100%" stopColor="#1a3a5c" />
          </radialGradient>

          {/* Subtle AO / overall shadow */}
          <radialGradient id="overallAO" cx="50%" cy="100%" r="50%">
            <stop offset="0%" stopColor="rgba(40,30,60,0.22)" />
            <stop offset="100%" stopColor="rgba(40,30,60,0)" />
          </radialGradient>

          {/* Clip circle */}
          <clipPath id="circleClip">
            <circle cx="100" cy="100" r="96" />
          </clipPath>

          {/* Depth of field blur */}
          <filter id="softBlur" x="-5%" y="-5%" width="110%" height="110%">
            <feGaussianBlur stdDeviation="0.4" />
          </filter>

          {/* Bottom fade for bust */}
          <linearGradient id="bustFade" x1="0%" y1="60%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="rgba(197,202,233,0)" />
            <stop offset="100%" stopColor="rgba(180,185,220,0.5)" />
          </linearGradient>
        </defs>

        {/* Background sphere */}
        <circle cx="100" cy="100" r="96" fill="url(#bgSphere)" />

        {/* Subtle background gradient overlay */}
        <circle cx="100" cy="100" r="96" fill="url(#overallAO)" />

        {/* === BODY (turtleneck bust) === */}
        {/* Main garment */}
        <path
          d="M 28 200 Q 35 155 50 140 Q 65 128 82 124 L 100 119 L 118 124 Q 135 128 150 140 Q 165 155 172 200 Z"
          fill="url(#turtleGrad)"
          clipPath="url(#circleClip)"
        />
        {/* Fabric sheen on garment */}
        <path
          d="M 28 200 Q 35 155 50 140 Q 65 128 82 124 L 100 119 L 118 124 Q 135 128 150 140 Q 165 155 172 200 Z"
          fill="url(#turtleSheen)"
          clipPath="url(#circleClip)"
        />
        {/* Turtleneck collar */}
        <path
          d="M 74 130 Q 76 120 82 115 L 100 110 L 118 115 Q 124 120 126 130 Q 113 136 100 136 Q 87 136 74 130 Z"
          fill="#252535"
          clipPath="url(#circleClip)"
        />
        {/* Collar fold highlight */}
        <path
          d="M 80 128 Q 82 119 88 115 L 100 112 L 112 115 Q 118 119 120 128 Q 110 133 100 133 Q 90 133 80 128 Z"
          fill="rgba(255,255,255,0.04)"
          clipPath="url(#circleClip)"
        />

        {/* === NECK === */}
        <path
          d="M 88 134 Q 88 148 90 154 L 100 157 L 110 154 Q 112 148 112 134 Q 106 138 100 138 Q 94 138 88 134 Z"
          fill="url(#neckGrad)"
          filter="url(#softBlur)"
        />
        {/* Neck shadow sides */}
        <path d="M 88 135 Q 85 145 88 154" stroke="rgba(140,80,40,0.3)" strokeWidth="2.5" fill="none" strokeLinecap="round" />
        <path d="M 112 135 Q 115 145 112 154" stroke="rgba(140,80,40,0.3)" strokeWidth="2.5" fill="none" strokeLinecap="round" />

        {/* === HEAD === */}
        {/* Main head shape */}
        <ellipse cx="100" cy="98" rx="34" ry="39" fill="url(#skinBase)" />
        {/* Skin AO shadow (chin/jaw area) */}
        <ellipse cx="100" cy="120" rx="30" ry="14" fill="rgba(160,90,40,0.2)" />
        {/* Forehead subtle highlight */}
        <ellipse cx="96" cy="78" rx="14" ry="10" fill="rgba(255,235,210,0.22)" />

        {/* === EARS === */}
        <ellipse cx="66.5" cy="98" rx="4.5" ry="6.5" fill="#e09060" />
        <ellipse cx="66.5" cy="98" rx="2.5" ry="4" fill="#d07848" />
        <ellipse cx="133.5" cy="98" rx="4.5" ry="6.5" fill="#e09060" />
        <ellipse cx="133.5" cy="98" rx="2.5" ry="4" fill="#d07848" />

        {/* === HAIR === */}
        {/* Hair base */}
        <ellipse cx="100" cy="77" rx="36" ry="26" fill="url(#hairGrad)" />
        {/* Hair sides */}
        <path d="M 66 86 Q 64 94 66 104 Q 67 92 70 88 Z" fill="#1a1008" />
        <path d="M 134 86 Q 136 94 134 104 Q 133 92 130 88 Z" fill="#1a1008" />
        {/* Hair top volume */}
        <path d="M 70 77 Q 72 58 100 58 Q 128 58 130 77 Q 118 70 100 70 Q 82 70 70 77 Z" fill="#1a1008" />
        {/* Hair sheen/highlight */}
        <ellipse cx="94" cy="64" rx="16" ry="8" fill="url(#hairSheen)" />
        {/* Hair detail strands */}
        <path d="M 72 80 Q 75 72 84 68" stroke="rgba(80,50,20,0.4)" strokeWidth="1" fill="none" strokeLinecap="round" />
        <path d="M 128 80 Q 125 72 116 68" stroke="rgba(80,50,20,0.4)" strokeWidth="1" fill="none" strokeLinecap="round" />

        {/* === FACE FEATURES === */}

        {/* Eyebrows */}
        <path d="M 81 88 Q 86 85 92 86" stroke="#3d2010" strokeWidth="2" fill="none" strokeLinecap="round" />
        <path d="M 108 86 Q 114 85 119 88" stroke="#3d2010" strokeWidth="2" fill="none" strokeLinecap="round" />

        {/* Eyes */}
        {/* Left eye */}
        <ellipse cx="88" cy="95" rx="7" ry="5.5" fill="white" />
        <ellipse cx="88" cy="95.5" rx="4.5" ry="4.5" fill="url(#irisGrad)" />
        <ellipse cx="88" cy="95.5" rx="2.8" ry="2.8" fill="#0d1a2a" />
        <ellipse cx="89.5" cy="93.8" rx="1.2" ry="1.2" fill="rgba(255,255,255,0.85)" />
        <ellipse cx="87.2" cy="96.8" rx="0.6" ry="0.6" fill="rgba(255,255,255,0.4)" />
        {/* Upper eyelid line */}
        <path d="M 81.5 93.5 Q 88 90.5 94.5 93.5" stroke="rgba(60,20,10,0.6)" strokeWidth="1.2" fill="none" strokeLinecap="round" />

        {/* Right eye */}
        <ellipse cx="112" cy="95" rx="7" ry="5.5" fill="white" />
        <ellipse cx="112" cy="95.5" rx="4.5" ry="4.5" fill="url(#irisGrad)" />
        <ellipse cx="112" cy="95.5" rx="2.8" ry="2.8" fill="#0d1a2a" />
        <ellipse cx="113.5" cy="93.8" rx="1.2" ry="1.2" fill="rgba(255,255,255,0.85)" />
        <ellipse cx="111.2" cy="96.8" rx="0.6" ry="0.6" fill="rgba(255,255,255,0.4)" />
        <path d="M 105.5 93.5 Q 112 90.5 118.5 93.5" stroke="rgba(60,20,10,0.6)" strokeWidth="1.2" fill="none" strokeLinecap="round" />

        {/* Lower eyelid subtle */}
        <path d="M 82.5 97 Q 88 99 93.5 97" stroke="rgba(160,90,60,0.25)" strokeWidth="0.8" fill="none" strokeLinecap="round" />
        <path d="M 106.5 97 Q 112 99 117.5 97" stroke="rgba(160,90,60,0.25)" strokeWidth="0.8" fill="none" strokeLinecap="round" />

        {/* Nose */}
        <path d="M 100 99 L 97 108 Q 100 110 103 108 Z" fill="rgba(160,80,40,0.18)" />
        <path d="M 97 108 Q 94 110 95 113 Q 98 114.5 100 114" stroke="rgba(140,70,30,0.35)" strokeWidth="1" fill="none" strokeLinecap="round" />
        <path d="M 103 108 Q 106 110 105 113 Q 102 114.5 100 114" stroke="rgba(140,70,30,0.35)" strokeWidth="1" fill="none" strokeLinecap="round" />
        {/* Nose bridge */}
        <path d="M 100 99 Q 99 103 99 107" stroke="rgba(160,90,50,0.2)" strokeWidth="1" fill="none" strokeLinecap="round" />

        {/* Mouth */}
        {/* Lips */}
        <path d="M 91 119 Q 95.5 116.5 100 116.5 Q 104.5 116.5 109 119 Q 105 121 100 121 Q 95 121 91 119 Z" fill="#c07060" />
        <path d="M 91 119 Q 95.5 121.5 100 122 Q 104.5 121.5 109 119 Q 105 123.5 100 124 Q 95 123.5 91 119 Z" fill="#a05848" />
        {/* Cupid's bow */}
        <path d="M 91 119 Q 95 117.5 100 118 Q 105 117.5 109 119" stroke="rgba(80,30,20,0.3)" strokeWidth="0.8" fill="none" strokeLinecap="round" />
        {/* Subtle smile crease */}
        <path d="M 88 117 Q 89.5 119.5 90 122" stroke="rgba(160,80,60,0.22)" strokeWidth="1" fill="none" strokeLinecap="round" />
        <path d="M 112 117 Q 110.5 119.5 110 122" stroke="rgba(160,80,60,0.22)" strokeWidth="1" fill="none" strokeLinecap="round" />

        {/* Cheek blush */}
        <ellipse cx="80" cy="107" rx="8" ry="5" fill="rgba(220,110,80,0.12)" />
        <ellipse cx="120" cy="107" rx="8" ry="5" fill="rgba(220,110,80,0.12)" />

        {/* === OVERALL DEPTH OVERLAY === */}
        {/* Cinematic vignette */}
        <circle cx="100" cy="100" r="96" fill="url(#overallAO)" opacity="0.6" />

        {/* Edge shadow for depth */}
        <circle cx="100" cy="100" r="96" fill="none" stroke="rgba(20,10,40,0.2)" strokeWidth="8" />
      </svg>

      {/* Floating chat bubble */}
      <div className="avatar-chat-bubble">
        <span className="bubble-dot" /><span className="bubble-dot" /><span className="bubble-dot" />
      </div>
    </motion.div>
  );
}
