type Dimension = {
  name: string;
  score: number;
  weight: number;
};

type Palette = {
  ink: string;
  muted: string;
  faint: string;
  arcStrong: string;
  arcWarm: string;
  hairline: string;
  hairlineFaint: string;
  centerStroke: string;
};

type Props = {
  size?: number;
  dimensions: Dimension[];
  overallScore: number;
  palette?: Palette;
};

const LIGHT_PALETTE: Palette = {
  ink: "#1c1c1c",
  muted: "#6f6a60",
  faint: "#9a9485",
  arcStrong: "#2b2e35",
  arcWarm: "#b97048",
  hairline: "rgba(28, 28, 28, 0.10)",
  hairlineFaint: "rgba(28, 28, 28, 0.06)",
  centerStroke: "rgba(28, 28, 28, 0.30)",
};

const sans = "'Inter', system-ui, sans-serif";
const mono = "'IBM Plex Mono', ui-monospace, monospace";

const polar = (cx: number, cy: number, r: number, angleDeg: number) => {
  const a = ((angleDeg - 90) * Math.PI) / 180;
  return [cx + r * Math.cos(a), cy + r * Math.sin(a)] as const;
};

const arcPath = (
  cx: number,
  cy: number,
  r: number,
  startAngle: number,
  endAngle: number,
) => {
  const [x1, y1] = polar(cx, cy, r, startAngle);
  const [x2, y2] = polar(cx, cy, r, endAngle);
  const largeArc = endAngle - startAngle > 180 ? 1 : 0;
  return `M ${x1} ${y1} A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2}`;
};

const labelAlignment = (angle: number) => {
  const norm = ((angle % 360) + 360) % 360;
  if (norm < 18 || norm > 342) return "TOP" as const;
  if (norm > 162 && norm < 198) return "BOTTOM" as const;
  if (norm >= 18 && norm <= 162) return "RIGHT" as const;
  return "LEFT" as const;
};

const RadialScoreChart = ({
  size = 520,
  dimensions,
  overallScore,
  palette = LIGHT_PALETTE,
}: Props) => {
  const { ink, muted, faint, arcStrong, arcWarm, hairline, hairlineFaint, centerStroke } = palette;
  const cx = size / 2;
  const cy = size / 2;
  const innerR = size * 0.115;
  const arcInner = innerR + size * 0.034;
  const arcOuter = size * 0.36;
  const labelR = size * 0.45;
  const arcGap = 2.4;

  const totalWeight = dimensions.reduce((s, d) => s + d.weight, 0);
  const firstSpan = (dimensions[0].weight / totalWeight) * 360;
  let cursor = -firstSpan / 2;
  const slices = dimensions.map((d) => {
    const span = (d.weight / totalWeight) * 360;
    const start = cursor;
    const end = cursor + span;
    cursor = end;
    const mid = (start + end) / 2;
    const radius = arcInner + (arcOuter - arcInner) * (d.score / 100);
    const color = d.score < 75 ? arcWarm : arcStrong;
    return { ...d, start, end, mid, radius, color };
  });

  return (
    <div style={{ position: "relative", width: size, height: size }}>
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        style={{ overflow: "visible" }}
      >
        {[0.33, 0.66, 1].map((t) => (
          <circle
            key={t}
            cx={cx}
            cy={cy}
            r={arcInner + (arcOuter - arcInner) * t}
            fill="none"
            stroke={hairlineFaint}
            strokeWidth={1}
            strokeDasharray="2 4"
          />
        ))}

        {slices.map((s) => {
          const [x1, y1] = polar(cx, cy, innerR + 4, s.end);
          const [x2, y2] = polar(cx, cy, arcOuter + 6, s.end);
          return (
            <line
              key={`div-${s.name}`}
              x1={x1}
              y1={y1}
              x2={x2}
              y2={y2}
              stroke={hairline}
              strokeWidth={1}
            />
          );
        })}

        {slices.map((s) => {
          const start = s.start + arcGap;
          const end = s.end - arcGap;
          if (end <= start) return null;
          return (
            <path
              key={`arc-${s.name}`}
              d={arcPath(cx, cy, s.radius, start, end)}
              fill="none"
              stroke={s.color}
              strokeWidth={4}
              strokeLinecap="round"
            />
          );
        })}

        <circle
          cx={cx}
          cy={cy}
          r={innerR}
          fill="none"
          stroke={centerStroke}
          strokeWidth={1}
        />
        <text
          x={cx}
          y={cy - 4}
          textAnchor="middle"
          dominantBaseline="middle"
          fill={ink}
          fontFamily={mono}
          fontSize={size * 0.075}
          fontWeight={300}
        >
          {overallScore}
        </text>
        <text
          x={cx}
          y={cy + size * 0.04}
          textAnchor="middle"
          dominantBaseline="middle"
          fill={muted}
          fontFamily={sans}
          fontSize={10}
          letterSpacing="0.12em"
        >
          OVERALL
        </text>
      </svg>

      {slices.map((s) => {
        const [lx, ly] = polar(cx, cy, labelR, s.mid);
        const mode = labelAlignment(s.mid);
        const tx = mode === "RIGHT" ? "0%" : mode === "LEFT" ? "-100%" : "-50%";
        const ty = mode === "TOP" ? "-100%" : mode === "BOTTOM" ? "0%" : "-50%";
        const align: "left" | "right" | "center" =
          mode === "RIGHT" ? "left" : mode === "LEFT" ? "right" : "center";
        return (
          <div
            key={`label-${s.name}`}
            style={{
              position: "absolute",
              left: lx,
              top: ly,
              transform: `translate(${tx}, ${ty})`,
              textAlign: align,
              minWidth: 100,
              pointerEvents: "none",
              fontFamily: sans,
            }}
          >
            <div style={{ fontSize: 11, color: muted, marginBottom: 2 }}>
              {s.name}
            </div>
            <div
              style={{
                fontFamily: mono,
                fontSize: 28,
                fontWeight: 300,
                lineHeight: 1,
                color: ink,
              }}
            >
              {s.score}
            </div>
            <div
              style={{
                fontSize: 9,
                color: faint,
                marginTop: 4,
                letterSpacing: "0.10em",
              }}
            >
              WEIGHT {s.weight}%
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default RadialScoreChart;
