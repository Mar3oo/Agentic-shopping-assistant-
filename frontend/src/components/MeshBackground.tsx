// Interactive ambient mesh gradient background
// Reacts subtly to mouse movement using CSS custom properties
import { useEffect, useRef } from 'react';

export default function MeshBackground() {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let rafId: number;
    let targetX = 50, targetY = 50;
    let currentX = 50, currentY = 50;

    const onMove = (e: MouseEvent) => {
      targetX = (e.clientX / window.innerWidth) * 100;
      targetY = (e.clientY / window.innerHeight) * 100;
    };

    const animate = () => {
      // Lerp towards target (lazy follow — feels organic, not jumpy)
      currentX += (targetX - currentX) * 0.035;
      currentY += (targetY - currentY) * 0.035;

      if (ref.current) {
        ref.current.style.setProperty('--mx', `${currentX.toFixed(2)}%`);
        ref.current.style.setProperty('--my', `${currentY.toFixed(2)}%`);
      }
      rafId = requestAnimationFrame(animate);
    };

    window.addEventListener('mousemove', onMove, { passive: true });
    rafId = requestAnimationFrame(animate);

    return () => {
      window.removeEventListener('mousemove', onMove);
      cancelAnimationFrame(rafId);
    };
  }, []);

  return <div ref={ref} className="mesh-bg" aria-hidden="true" />;
}
