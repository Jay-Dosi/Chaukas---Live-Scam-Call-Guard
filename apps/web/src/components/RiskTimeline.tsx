import { useTranslation } from '@i18n/useTranslation';

interface RiskTimelineProps {
  history: Array<{ score: number; level: string; t_ms: number }>;
  thresholds: { caution: number; danger: number; critical: number };
  width: number;
  height?: number;
}

export function RiskTimeline({ history, thresholds, width, height = 160 }: RiskTimelineProps) {
  const { t } = useTranslation();

  if (history.length === 0) {
    return (
      <div className="risk-timeline" style={{ width, height }}>
        <svg width={width} height={height}>
          <text
            x={width / 2}
            y={height / 2}
            textAnchor="middle"
            fill="var(--ink-3)"
            fontSize="14"
            fontFamily="var(--font-ui)"
          >
            {t('liveGuard.noData')}
          </text>
        </svg>
      </div>
    );
  }

  const maxScore = 100;
  const padding = 40;
  const chartWidth = width - padding * 2;
  const chartHeight = height - padding * 2;

  // Generate points for stepped line
  const points = history.map((a, i) => {
    const x = padding + (i / Math.max(1, history.length - 1)) * chartWidth;
    const y = padding + chartHeight - (a.score / maxScore) * chartHeight;
    return { x, y, score: a.score, level: a.level, t: a.t_ms };
  });

  // Threshold lines
  const cautionY = padding + chartHeight - (thresholds.caution / maxScore) * chartHeight;
  const dangerY = padding + chartHeight - (thresholds.danger / maxScore) * chartHeight;
  const criticalY = padding + chartHeight - (thresholds.critical / maxScore) * chartHeight;

  // Stepped path: horizontal then vertical (flight recorder style)
  const path = points.reduce((acc, p, i) => {
    if (i === 0) {
      return `M ${p.x} ${p.y}`;
    }
    // Horizontal line to current x, then vertical to current y
    return `${acc} H ${p.x} V ${p.y}`;
  }, '');

  return (
    <div className="risk-timeline" style={{ width, height }}>
      <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
        {/* Hairline gridlines - Y axis at 0, 50, 100 */}
        <line
          x1={padding}
          y1={padding}
          x2={padding + chartWidth}
          y2={padding}
          stroke="var(--line)"
          strokeWidth="0.5"
        />
        <line
          x1={padding}
          y1={padding + chartHeight / 2}
          x2={padding + chartWidth}
          y2={padding + chartHeight / 2}
          stroke="var(--line)"
          strokeWidth="0.5"
        />
        <line
          x1={padding}
          y1={padding + chartHeight}
          x2={padding + chartWidth}
          y2={padding + chartHeight}
          stroke="var(--line-strong)"
          strokeWidth="1"
        />

        {/* Y axis - left edge */}
        <line
          x1={padding}
          y1={padding}
          x2={padding}
          y2={padding + chartHeight}
          stroke="var(--line-strong)"
          strokeWidth="1"
        />

        {/* Threshold lines - hairline dashed */}
        <line
          x1={padding}
          y1={cautionY}
          x2={padding + chartWidth}
          y2={cautionY}
          stroke="var(--caution)"
          strokeWidth="1"
          strokeDasharray="4,4"
        />
        <line
          x1={padding}
          y1={dangerY}
          x2={padding + chartWidth}
          y2={dangerY}
          stroke="var(--danger)"
          strokeWidth="1"
          strokeDasharray="4,4"
        />
        <line
          x1={padding}
          y1={criticalY}
          x2={padding + chartWidth}
          y2={criticalY}
          stroke="var(--danger)"
          strokeWidth="1"
          strokeDasharray="4,4"
        />

        {/* Threshold labels - right aligned */}
        <text
          x={padding + chartWidth + 8}
          y={cautionY + 4}
          textAnchor="start"
          fontSize="10"
          fill="var(--caution)"
          fontFamily="var(--font-mono)"
          style={{ fontVariantNumeric: 'tabular-nums' }}
        >
          {t('liveGuard.thresholds.caution')}{thresholds.caution}
        </text>
        <text
          x={padding + chartWidth + 8}
          y={dangerY + 4}
          textAnchor="start"
          fontSize="10"
          fill="var(--danger)"
          fontFamily="var(--font-mono)"
          style={{ fontVariantNumeric: 'tabular-nums' }}
        >
          {t('liveGuard.thresholds.danger')}{thresholds.danger}
        </text>
        <text
          x={padding + chartWidth + 8}
          y={criticalY + 4}
          textAnchor="start"
          fontSize="10"
          fill="var(--danger)"
          fontFamily="var(--font-mono)"
          style={{ fontVariantNumeric: 'tabular-nums' }}
        >
          {t('liveGuard.thresholds.critical')}{thresholds.critical}
        </text>

        {/* Risk line - stepped, no gradient */}
        <path
          d={path}
          fill="none"
          stroke="var(--ink)"
          strokeWidth="1.5"
        />

        {/* Points - small circles at data points */}
        {points.map((p, i) => (
          <circle
            key={i}
            cx={p.x}
            cy={p.y}
            r={3}
            fill="var(--ink)"
          />
        ))}

        {/* Y axis labels - left side */}
        <text
          x={padding - 8}
          y={padding + 4}
          textAnchor="end"
          fontSize="10"
          fill="var(--ink-3)"
          fontFamily="var(--font-mono)"
          style={{ fontVariantNumeric: 'tabular-nums' }}
        >
          100
        </text>
        <text
          x={padding - 8}
          y={padding + chartHeight / 2 + 4}
          textAnchor="end"
          fontSize="10"
          fill="var(--ink-3)"
          fontFamily="var(--font-mono)"
          style={{ fontVariantNumeric: 'tabular-nums' }}
        >
          50
        </text>
        <text
          x={padding - 8}
          y={padding + chartHeight + 4}
          textAnchor="end"
          fontSize="10"
          fill="var(--ink-3)"
          fontFamily="var(--font-mono)"
          style={{ fontVariantNumeric: 'tabular-nums' }}
        >
          0
        </text>

        {/* X axis labels */}
        {points.length > 1 && (
          <>
            <text
              x={padding}
              y={padding + chartHeight + 20}
              textAnchor="start"
              fontSize="10"
              fill="var(--ink-3)"
              fontFamily="var(--font-mono)"
              style={{ fontVariantNumeric: 'tabular-nums' }}
            >
              0s
            </text>
            <text
              x={padding + chartWidth}
              y={padding + chartHeight + 20}
              textAnchor="end"
              fontSize="10"
              fill="var(--ink-3)"
              fontFamily="var(--font-mono)"
              style={{ fontVariantNumeric: 'tabular-nums' }}
            >
              {Math.round((points[points.length - 1]?.t ?? 0) / 1000)}s
            </text>
          </>
        )}
      </svg>
    </div>
  );
}