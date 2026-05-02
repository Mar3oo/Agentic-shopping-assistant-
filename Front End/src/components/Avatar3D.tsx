// RECO 3D Avatar — loads avatar.glb via @react-three/fiber + drei
// Shows thinking/listening/idle animations, interactive on click
import { Suspense, useRef, useEffect, useState } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { useGLTF, OrbitControls, Environment, ContactShadows } from '@react-three/drei';
import { motion, AnimatePresence } from 'framer-motion';
import * as THREE from 'three';

type AvatarState = 'idle' | 'listening' | 'thinking';

// Inner 3D model component
function AvatarModel({ avatarState }: { avatarState: AvatarState }) {
  const group = useRef<THREE.Group>(null!);
  const { scene } = useGLTF('/avatar.glb');

  // Clone scene to avoid shared state issues
  const clonedScene = scene.clone(true);

  // Subtle idle bob + thinking spin animations
  useFrame((state) => {
    if (!group.current) return;
    const t = state.clock.elapsedTime;

    if (avatarState === 'idle') {
      group.current.position.y = Math.sin(t * 0.8) * 0.04;
      group.current.rotation.y = Math.sin(t * 0.3) * 0.06;
    } else if (avatarState === 'listening') {
      group.current.position.y = Math.sin(t * 1.8) * 0.06;
      group.current.rotation.y = Math.sin(t * 0.6) * 0.12;
    } else if (avatarState === 'thinking') {
      group.current.rotation.y += 0.012;
      group.current.position.y = Math.sin(t * 1.2) * 0.05;
    }
  });

  return (
    <group ref={group}>
      <primitive
        object={clonedScene}
        scale={avatarState === 'thinking' ? 1.05 : 1}
        position={[0, -0.9, 0]}
      />
    </group>
  );
}

// Fallback nebula for when 3D fails or loads
function NebulFallback({ size }: { size: number }) {
  return (
    <svg viewBox="0 0 200 200" width={size} height={size} xmlns="http://www.w3.org/2000/svg">
      <defs>
        <radialGradient id="nbFbCore" cx="40%" cy="35%" r="65%">
          <stop offset="0%" stopColor="#a78bfa" />
          <stop offset="55%" stopColor="#7c5cfc" />
          <stop offset="100%" stopColor="#1e1b6e" />
        </radialGradient>
        <filter id="nbFbGlow" x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur stdDeviation="5" result="blur" />
          <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
      </defs>
      <circle cx="100" cy="100" r="88" fill="url(#nbFbCore)" filter="url(#nbFbGlow)" />
      <ellipse cx="88" cy="90" rx="7" ry="6" fill="rgba(255,255,255,0.9)" />
      <ellipse cx="112" cy="90" rx="7" ry="6" fill="rgba(255,255,255,0.9)" />
      <ellipse cx="89" cy="91" rx="3" ry="3" fill="#1e1b6e" />
      <ellipse cx="113" cy="91" rx="3" ry="3" fill="#1e1b6e" />
      <path d="M 88 108 Q 100 115 112 108" stroke="rgba(255,255,255,0.6)" strokeWidth="2" fill="none" strokeLinecap="round" />
    </svg>
  );
}

interface Avatar3DProps {
  size?: number;
  avatarState?: AvatarState;
  className?: string;
  interactive?: boolean;
}

export default function Avatar3D({ size = 120, avatarState = 'idle', className = '', interactive = true }: Avatar3DProps) {
  const [hovered, setHovered] = useState(false);
  const [glbError, setGlbError] = useState(false);

  const stateLabel = avatarState === 'thinking' ? 'Thinking...' : avatarState === 'listening' ? 'Listening' : null;

  return (
    <div
      className={`avatar3d-root ${className}`}
      style={{ width: size, height: size, position: 'relative', display: 'inline-block' }}
      onMouseEnter={() => interactive && setHovered(true)}
      onMouseLeave={() => interactive && setHovered(false)}
    >
      {/* Ambient glow behind canvas */}
      <div className="avatar3d-glow" style={{
        width: size * 1.4,
        height: size * 1.4,
        top: -(size * 0.2),
        left: -(size * 0.2),
      }} />

      {glbError ? (
        <NebulFallback size={size} />
      ) : (
        <Canvas
          style={{ width: size, height: size, borderRadius: '50%' }}
          camera={{ position: [0, 0.2, 2.2], fov: 36 }}
          gl={{ antialias: true, alpha: true }}
          dpr={[1, 2]}
        >
          <ambientLight intensity={0.6} />
          <directionalLight position={[3, 5, 3]} intensity={1.2} color="#fff" castShadow />
          <directionalLight position={[-3, 2, -2]} intensity={0.4} color="#a78bfa" />
          <pointLight position={[0, 3, 1]} intensity={0.8} color="#7c5cfc" />

          <Suspense fallback={null}>
            <AvatarModel avatarState={avatarState} />
            <Environment preset="studio" />
            <ContactShadows position={[0, -1.2, 0]} opacity={0.35} scale={3} blur={2} />
          </Suspense>

          {interactive && (
            <OrbitControls
              enableZoom={false}
              enablePan={false}
              minPolarAngle={Math.PI / 3}
              maxPolarAngle={Math.PI / 1.8}
              autoRotate={avatarState === 'idle'}
              autoRotateSpeed={0.6}
            />
          )}
        </Canvas>
      )}

      {/* State indicator badge */}
      <AnimatePresence>
        {stateLabel && (
          <motion.div
            className="avatar3d-state-badge"
            initial={{ opacity: 0, y: 6, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 4 }}
            transition={{ duration: 0.2 }}
          >
            <span className="avatar3d-state-dot" />
            {stateLabel}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Thinking ring overlay */}
      {avatarState === 'thinking' && (
        <div className="avatar3d-thinking-ring" style={{ width: size + 16, height: size + 16, top: -8, left: -8 }} />
      )}
    </div>
  );
}
