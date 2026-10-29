import type { Analysis } from '@protocol/index';

interface RiskTimelineProps {
  history: Analysis[];
  thresholds: { caution: number; danger: number; critical: number };
  width: number;
  height?: number;
}

export function RiskTimeline({ history, thresholds, width, height = 160 }: RiskTimelineProps) {
  if (history.length === 0) {
    return (
      <div className="risk-timeline" style={{width, height}}>
        <svg width={width} height={height}>
          <text x={width / 2} y={height / 2} textAnchor="middle" fill="var(--ink-3)" fontSize="14">
            No data yet
          </text>
        </svg>
      </div>
    );
  }

  const maxScore = 100;
  const padding = 40;
  const chartWidth = width - padding * 2;
  const chartHeight = height - padding * 2;

  // Generate points
  const points = history.map((a, i) => {
    const x = padding + (i / Math.max(1, history.length - 1)) * chartWidth;
    const y = padding + chartHeight - (a.score / maxScore) * chartHeight;
    return { x, y, score: a.score, level: a.level, t: a.t_ms };
  });

  // Threshold lines
  const cautionY = padding + chartHeight - (thresholds.caution / maxScore) * chartHeight;
  const dangerY = padding + chartHeight - (thresholds.danger / maxScore) * chartHeight;
  const criticalY = padding + chartHeight - (thresholds.critical / maxScore) * chartHeight;

  // Path
  const path = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');

  return (
    <div className="risk-timeline" style={{width, height}}>
      <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
        {/* Grid lines */}
        <line x1={padding} y1={padding} x2={padding} y2={padding + chartHeight} stroke="var(--line)" strokeWidth="1" />
        <line x1={padding} y1={padding + chartHeight} x2={padding + chartWidth} y2={padding + chartHeight} stroke="var(--line)" strokeWidth="1" />

        {/* Threshold lines */}
        <line x1={padding} y1={cautionY} x2={padding + chartWidth} y2={cautionY}
              stroke="var(--caution)" strokeWidth="1" strokeDasharray="4,4" />
        <line x1={padding} y1={dangerY} x2={padding + chartWidth} y2={dangerY}
              stroke="var(--danger)" strokeWidth="1" strokeDasharray="4,4" />
        <line x1={padding} y1={criticalY} x2={padding + chartWidth} y2={criticalY}
              stroke="var(--critical-bg)" strokeWidth="1" strokeDasharray="4,4" />

        {/* Threshold labels */}
        <text x={padding - 8} y={cautionY + 4} textAnchor="end" fontSize="10" fill="var(--caution)">
          Caution ({thresholds.caution})
        </text>
        <text x={padding - 8} y={dangerY + 4} textAnchor="end" fontSize="10" fill="var(--danger)">
          Danger ({thresholds.danger})
        </text>
        <text x={padding - 8} y={criticalY + 4} textAnchor="end" fontSize="10" fill="var(--critical-bg)">
          Critical ({thresholds.critical})
        </text>

        {/* Risk line */}
        <path d={path} fill="none" stroke="var(--ink)" strokeWidth="1.5" />

        {/* Points */}
        {points.map((p, i) => (
          <circle key={i} cx={p.x} cy={p.y} r={3} fill="var(--ink)" />
        ))}

        {/* Y axis labels */}
        <text x={padding - 12} y={padding + 4} textAnchor="end" fontSize="10" fill="var(--ink-3)">100</text>
        <text x={padding - 12} y={padding + chartHeight / 2 + 4} textAnchor="end" fontSize="10" fill="var(--ink-3)">50</text>
        <text x={padding - 12} y={padding + chartHeight + 4} textAnchor="end" fontSize="10" fill="var(--ink-3)">0</text>

        {/* X axis labels */}
        {points.length > 1 && (
          <>
            <text x={padding} y={padding + chartHeight + 20} textAnchor="start" fontSize="10" fill="var(--ink-3)">
              0s
            </text>
            <text x={padding + chartWidth} y={padding + chartHeight + 20} textAnchor="end" fontSize="10" fill="var(--ink-3)">
              {Math.round((points[points.length - 1]?.t ?? 0) / 1000)}s
            </text>
          </>
        )}
      </svg>
    </div>
  );
}