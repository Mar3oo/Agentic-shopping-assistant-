import { useApp } from '../store/AppContext';

interface PolarChartProps {
  data: Array<{
    metric: string;
    product_1: number;
    product_2: number;
    reason?: string;
  }>;
  labels: Record<string, string>;
}

export default function PolarChart({ data, labels }: PolarChartProps) {
  const { state } = useApp();
  const isRtl = state.lang === 'ar';

  if (!data || data.length === 0) return null;

  const size = 300;
  const center = size / 2;
  const radius = size * 0.35;
  const angleStep = (Math.PI * 2) / data.length;

  const getCoordinates = (angle: number, value: number) => {
    const r = (value / 100) * radius;
    return {
      x: center + r * Math.cos(angle - Math.PI / 2),
      y: center + r * Math.sin(angle - Math.PI / 2),
    };
  };

  const product1Points = data
    .map((d, i) => {
      const { x, y } = getCoordinates(i * angleStep, d.product_1);
      return `${x},${y}`;
    })
    .join(' ');

  const product2Points = data
    .map((d, i) => {
      const { x, y } = getCoordinates(i * angleStep, d.product_2);
      return `${x},${y}`;
    })
    .join(' ');

  return (
    <div className="flex flex-col items-center my-6">
      <div className="relative">
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="overflow-visible">
          {/* Grid Circles */}
          {[20, 40, 60, 80, 100].map((v) => (
            <circle
              key={v}
              cx={center}
              cy={center}
              r={(v / 100) * radius}
              fill="none"
              stroke="var(--c-border)"
              strokeDasharray="4 2"
              opacity="0.5"
            />
          ))}

          {/* Grid Spikes */}
          {data.map((_, i) => {
            const { x, y } = getCoordinates(i * angleStep, 100);
            return (
              <line
                key={i}
                x1={center}
                y1={center}
                x2={x}
                y2={y}
                stroke="var(--c-border)"
                opacity="0.5"
              />
            );
          })}

          {/* Product 1 Area */}
          <polygon
            points={product1Points}
            fill="rgba(59, 130, 246, 0.4)"
            stroke="rgb(59, 130, 246)"
            strokeWidth="2"
          />

          {/* Product 2 Area */}
          <polygon
            points={product2Points}
            fill="rgba(239, 68, 68, 0.4)"
            stroke="rgb(239, 68, 68)"
            strokeWidth="2"
          />

          {/* Labels */}
          {data.map((d, i) => {
            const { x, y } = getCoordinates(i * angleStep, 115);
            return (
              <text
                key={i}
                x={x}
                y={y}
                textAnchor="middle"
                dominantBaseline="middle"
                fontSize="10"
                fill="var(--c-text-1)"
                fontWeight="600"
                dir={isRtl ? 'rtl' : 'ltr'}
              >
                {d.metric}
              </text>
            );
          })}
        </svg>
      </div>

      {/* Legend */}
      <div className="flex gap-4 mt-4 text-xs">
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-full bg-blue-500" />
          <span className="text-gray-400 font-medium">{labels.product_1}</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-full bg-red-500" />
          <span className="text-gray-400 font-medium">{labels.product_2}</span>
        </div>
      </div>
    </div>
  );
}
