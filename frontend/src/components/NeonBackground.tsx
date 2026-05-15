// RECO Neon/AI Background — animated neon grid, floating particles, scan lines
// Controlled by appState.neonBg — toggled from Settings
import { useEffect, useRef } from 'react';
import { useApp } from '../store/AppContext';

export default function NeonBackground() {
  const { state } = useApp();
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const rafRef = useRef<number>(0);
  const timeRef = useRef(0);

  useEffect(() => {
    if (!state.neonBg) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener('resize', resize, { passive: true });

    // Get accent color from CSS
    const getAccent = () => {
      const style = getComputedStyle(document.documentElement);
      return style.getPropertyValue('--c-accent-1').trim() || '#7c5cfc';
    };

    // Floating particles
    const PARTICLE_COUNT = 100;
    const particles = Array.from({ length: PARTICLE_COUNT }, () => ({
      x: Math.random() * window.innerWidth,
      y: Math.random() * window.innerHeight,
      r: 1 + Math.random() * 2.5,
      vx: (Math.random() - 0.5) * 0.35,
      vy: (Math.random() - 0.5) * 0.35,
      alpha: 0.2 + Math.random() * 0.5,
      pulse: Math.random() * Math.PI * 2,
    }));

    const draw = (t: number) => {
      timeRef.current = t;
      const w = canvas.width;
      const h = canvas.height;
      ctx.clearRect(0, 0, w, h);

      const isDark = state.theme === 'dark';
      const accent = getAccent();
	  // ── Neon energy path (S curve 🔥) ──
		ctx.beginPath();

			for (let y = 0; y < h; y += 6) {
				const wave =
				Math.sin(y * 0.01 + t * 0.001) * 80 +
				Math.sin(y * 0.02 + t * 0.0007) * 40;

				const x = w * 0.25 + wave;

			if (y === 0) ctx.moveTo(x, y);
			else ctx.lineTo(x, y);
}

const neonGrad = ctx.createLinearGradient(0, 0, 0, h);
neonGrad.addColorStop(0, "#ff00cc");
neonGrad.addColorStop(0.5, "#ff6a00");
neonGrad.addColorStop(1, "#ff00cc");

ctx.strokeStyle = neonGrad;
ctx.lineWidth = 0;

ctx.shadowColor = "#ff6a00";
ctx.shadowBlur = 35;

ctx.stroke();
ctx.shadowBlur = 0;
	// ── Neon terrain waves ──
for (let layer = 0; layer < 3; layer++) {
  ctx.beginPath();

  for (let x = 0; x <= w; x += 8) {
    const y =
      h * 0.75 +
      Math.sin(x * 0.01 + t * 0.001 + layer) * (20 + layer * 10);

    if (x === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }

  const grad = ctx.createLinearGradient(0, h * 0.7, 0, h);
  grad.addColorStop(0, "#ff6a00");
  grad.addColorStop(1, "transparent");

  ctx.strokeStyle = grad;
  ctx.lineWidth = 1.5 + layer;

  ctx.shadowColor = "#ff6a00";
  ctx.shadowBlur = 25;

  ctx.stroke();
  ctx.shadowBlur = 0;
}
// ── Big glow orb ──
const orb = ctx.createRadialGradient(
  w * 0.2,
  h * 0.4,
  0,
  w * 0.2,
  h * 0.4,
  300
);

orb.addColorStop(0, "rgba(255,106,0,0.35)");
orb.addColorStop(1, "transparent");

ctx.fillStyle = orb;
ctx.fillRect(0, 0, w, h);

      // ── Perspective grid ──
      const gridAlpha = isDark ? 0.045 : 0.03;
      ctx.strokeStyle = accent;
      ctx.lineWidth = 0.7;

      // Horizontal lines — vanishing point center-bottom
      const VP = { x: w / 2, y: h * 1.1 };
      const LINES = 0;
      for (let i = 0; i <= LINES; i++) {
        const yFrac = i / LINES;
        const y = h * 0.35 + yFrac * h * 0.65;
        const fade = yFrac * 0.8;
        ctx.globalAlpha = gridAlpha * 1.8
		ctx.shadowColor = accent
		ctx.shadowBlur = 8
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(w, y);
        ctx.stroke();
      }

      // Vertical convergent lines toward VP
      const VLINES = 0;
      for (let i = 0; i <= VLINES; i++) {
        const xFrac = i / VLINES;
        const xTop = xFrac * w;
        ctx.globalAlpha = gridAlpha * 0.7;
        ctx.beginPath();
        ctx.moveTo(xTop, h * 0.3);
        ctx.lineTo(VP.x + (xTop - VP.x) * 2.2, h);
        ctx.stroke();
      }


      // ── Floating particles ──
      particles.forEach(p => {
        p.x += p.vx;
        p.y += p.vy;
        p.pulse += 0.018;
        if (p.x < 0) p.x = w;
        if (p.x > w) p.x = 0;
        if (p.y < 0) p.y = h;
        if (p.y > h) p.y = 0;

        const pAlpha = p.alpha * (0.6 + 0.4 * Math.sin(p.pulse));
        ctx.globalAlpha = pAlpha * (isDark ? 0.85 : 0.45);
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = accent;
        ctx.fill();

        // Particle glow
        const grad = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.r * 5);
        grad.addColorStop(0, accent + '40');
        grad.addColorStop(1, 'transparent');
        ctx.globalAlpha = pAlpha * 0.4 * (isDark ? 1 : 0.5);
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r * 5, 0, Math.PI * 2);
        ctx.fillStyle = grad;
        ctx.fill();
      });

      // ── Corner glow accents ──
      const corners = [
        { x: 0, y: 0 }, { x: w, y: 0 },
        { x: 0, y: h }, { x: w, y: h },
      ];
      corners.forEach(({ x, y }) => {
        const cg = ctx.createRadialGradient(x, y, 0, x, y, w * 0.28);
        cg.addColorStop(0, accent + (isDark ? '14' : '0c'));
        cg.addColorStop(1, 'transparent');
        ctx.globalAlpha = 1;
        ctx.fillStyle = cg;
        ctx.fillRect(0, 0, w, h);
      });

      ctx.globalAlpha = 1;
      rafRef.current = requestAnimationFrame(draw);
    };

    rafRef.current = requestAnimationFrame(draw);

    return () => {
      cancelAnimationFrame(rafRef.current);
      window.removeEventListener('resize', resize);
    };
  }, [state.neonBg, state.theme, state.colorPalette]);

  if (!state.neonBg) return null;

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 1,
        pointerEvents: 'none',
        opacity: state.theme === 'dark' ? 1 : 0.6,
      }}
      aria-hidden="true"
    />
  );
}
