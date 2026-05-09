import {
  Bar,
  BarChart,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  XAxis,
  YAxis,
} from "recharts";

const INK = "#2B2D34";
const TERRACOTTA = "#B96E46";
const OLIVE = "#92977D";
const HAIRLINE = "rgba(43, 45, 52, 0.10)";
const FAINT = "rgba(43, 45, 52, 0.34)";
const MUTED = "rgba(43, 45, 52, 0.58)";

const SANS = "'Basier Square', 'Inter', system-ui, sans-serif";
const MONO = "'Basier Square Mono', ui-monospace, monospace";

const tickAxis = { stroke: HAIRLINE, strokeWidth: 1 } as const;
const tickStyle = {
  fontSize: 10,
  fontFamily: MONO,
  fill: MUTED,
} as const;

/* ─────────────────── 1. Deadline strip ─────────────────── */
export const DeadlineStrip = ({
  items,
  riskUnderDays = 5,
  maxDays = 30,
}: {
  items: { id: string | number; daysLeft: number }[];
  riskUnderDays?: number;
  maxDays?: number;
}) => {
  const points = items.map((r) => ({
    x: r.daysLeft,
    y: 0,
    risk: r.daysLeft <= riskUnderDays,
  }));
  return (
    <ResponsiveContainer width="100%" height={64}>
      <ScatterChart margin={{ top: 12, right: 16, bottom: 22, left: 16 }}>
        <XAxis
          type="number"
          dataKey="x"
          domain={[0, maxDays]}
          ticks={[0, riskUnderDays, Math.round(maxDays / 2), maxDays]}
          tickFormatter={(v) => (v === 0 ? "0d" : `${v}d`)}
          tick={tickStyle}
          axisLine={tickAxis}
          tickLine={tickAxis}
          reversed
        />
        <YAxis type="number" dataKey="y" hide domain={[-1, 1]} />
        <ReferenceLine
          x={riskUnderDays}
          stroke={TERRACOTTA}
          strokeDasharray="2 3"
          strokeWidth={1}
        />
        <Scatter
          data={points.filter((p) => !p.risk)}
          fill={INK}
          shape="circle"
          isAnimationActive={false}
        />
        <Scatter
          data={points.filter((p) => p.risk)}
          fill={TERRACOTTA}
          shape="circle"
          isAnimationActive={false}
        />
      </ScatterChart>
    </ResponsiveContainer>
  );
};

/* ─────────────────── 2. Sorted severity bars ─────────────────── */
export const SortedSeverity = ({
  items,
  threshold,
  unit = "",
  accent = false,
}: {
  items: { name: string; value: number }[];
  threshold?: number;
  unit?: string;
  accent?: boolean;
}) => {
  const sorted = [...items].sort((a, b) => b.value - a.value);
  const max = Math.max(...sorted.map((d) => d.value), threshold ?? 0);
  return (
    <ResponsiveContainer width="100%" height={Math.max(72, sorted.length * 22)}>
      <BarChart
        layout="vertical"
        data={sorted}
        margin={{ top: 4, right: 36, bottom: 4, left: 0 }}
      >
        <XAxis type="number" hide domain={[0, max * 1.1]} />
        <YAxis
          type="category"
          dataKey="name"
          tickLine={false}
          axisLine={false}
          width={170}
          tick={{ fontSize: 11, fill: MUTED, fontFamily: SANS }}
        />
        {threshold != null ? (
          <ReferenceLine
            x={threshold}
            stroke={TERRACOTTA}
            strokeDasharray="2 3"
            strokeWidth={1}
            label={{
              value: `${threshold}${unit}`,
              position: "right",
              fontSize: 9,
              fill: TERRACOTTA,
              fontFamily: MONO,
            }}
          />
        ) : null}
        <Bar
          dataKey="value"
          fill={accent ? TERRACOTTA : INK}
          barSize={4}
          isAnimationActive={false}
        />
      </BarChart>
    </ResponsiveContainer>
  );
};

/* ─────────────────── 3. Stacked breakdown bar ─────────────────── */
export const StackedBreakdown = ({
  segments,
}: {
  segments: { key: string; label: string; value: number }[];
}) => {
  const palette = [INK, TERRACOTTA, OLIVE, MUTED, FAINT];
  const segs = segments.map((s, i) => ({ ...s, color: palette[i % palette.length] }));
  const total = segs.reduce((sum, s) => sum + s.value, 0);
  const data = [
    segs.reduce<Record<string, number | string>>(
      (acc, s) => ((acc[s.key] = s.value), acc),
      { name: "all" },
    ),
  ];
  return (
    <div>
      <ResponsiveContainer width="100%" height={26}>
        <BarChart
          layout="vertical"
          data={data}
          margin={{ top: 0, right: 0, bottom: 0, left: 0 }}
          barCategoryGap={0}
        >
          <XAxis type="number" hide domain={[0, total]} />
          <YAxis type="category" dataKey="name" hide />
          {segs.map((s) => (
            <Bar
              key={s.key}
              dataKey={s.key}
              stackId="a"
              fill={s.color}
              isAnimationActive={false}
              barSize={12}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
      <div
        style={{
          display: "flex",
          gap: 16,
          marginTop: 12,
          flexWrap: "wrap",
          fontFamily: SANS,
          fontSize: 11,
        }}
      >
        {segs.map((s) => (
          <div
            key={s.key}
            style={{ display: "flex", alignItems: "center", gap: 6 }}
          >
            <span
              style={{
                width: 8,
                height: 8,
                background: s.color,
                display: "inline-block",
              }}
            />
            <span style={{ color: MUTED }}>{s.label}</span>
            <span style={{ color: INK, fontFamily: MONO }}>{s.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

/* ─────────────────── 4. Queue with age ─────────────────── */
export const QueueWithAge = ({
  depths,
  oldestHours,
  slaHours,
}: {
  depths: number[];
  oldestHours: number;
  slaHours: number;
}) => {
  const data = depths.map((v, i) => ({ x: i, value: v }));
  const ageRatio = Math.min(1, oldestHours / slaHours);
  const breached = oldestHours > slaHours;
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      <ResponsiveContainer width="100%" height={48}>
        <LineChart data={data} margin={{ top: 4, right: 4, bottom: 4, left: 4 }}>
          <XAxis dataKey="x" hide />
          <YAxis hide domain={["auto", "auto"]} />
          <Line
            type="linear"
            dataKey="value"
            stroke={INK}
            strokeWidth={1.25}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
      <div>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            fontFamily: MONO,
            fontSize: 10,
            color: MUTED,
            letterSpacing: "0.06em",
            marginBottom: 4,
          }}
        >
          <span>OLDEST · {oldestHours}h</span>
          <span>SLA · {slaHours}h</span>
        </div>
        <div
          style={{
            position: "relative",
            height: 4,
            background: HAIRLINE,
            borderRadius: 2,
            overflow: "hidden",
          }}
        >
          <div
            style={{
              position: "absolute",
              left: 0,
              top: 0,
              bottom: 0,
              width: `${ageRatio * 100}%`,
              background: breached ? TERRACOTTA : INK,
            }}
          />
        </div>
      </div>
    </div>
  );
};

/* ─────────────────── 5. Row list + sparkline ─────────────────── */
export const RowListSparkline = ({
  items,
  trend,
}: {
  items: { label: string; meta: string; tone?: "default" | "attention" }[];
  trend: number[];
}) => {
  const data = trend.map((v, i) => ({ x: i, value: v }));
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      <div style={{ display: "flex", flexDirection: "column" }}>
        {items.map((item, i) => (
          <div
            key={item.label}
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              padding: "6px 0",
              borderTop: i === 0 ? "none" : `1px solid ${HAIRLINE}`,
              fontFamily: SANS,
              fontSize: 12.5,
              color: INK,
            }}
          >
            <span
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 8,
              }}
            >
              <span
                style={{
                  width: 4,
                  height: 4,
                  borderRadius: "50%",
                  background:
                    item.tone === "attention" ? TERRACOTTA : MUTED,
                  display: "inline-block",
                }}
              />
              {item.label}
            </span>
            <span
              style={{ fontFamily: MONO, fontSize: 11, color: MUTED }}
            >
              {item.meta}
            </span>
          </div>
        ))}
      </div>
      <ResponsiveContainer width="100%" height={28}>
        <LineChart data={data} margin={{ top: 4, right: 4, bottom: 4, left: 4 }}>
          <XAxis dataKey="x" hide />
          <YAxis hide domain={["auto", "auto"]} />
          <Line
            type="linear"
            dataKey="value"
            stroke={INK}
            strokeWidth={1.25}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

/* ─────────────────── 6. Timeline of finds ─────────────────── */
export const TimelineOfFinds = ({
  finds,
}: {
  finds: { day: number; type: "primary" | "secondary" | "tertiary" }[];
}) => {
  const yByType: Record<string, number> = {
    primary: 0.6,
    secondary: 0,
    tertiary: -0.6,
  };
  const colorByType: Record<string, string> = {
    primary: INK,
    secondary: TERRACOTTA,
    tertiary: OLIVE,
  };
  const points = finds.map((f) => ({
    x: f.day,
    y: yByType[f.type],
    type: f.type,
  }));
  return (
    <ResponsiveContainer width="100%" height={70}>
      <ScatterChart margin={{ top: 8, right: 12, bottom: 22, left: 12 }}>
        <XAxis
          type="number"
          dataKey="x"
          domain={[0, 30]}
          ticks={[0, 7, 14, 21, 30]}
          tickFormatter={(v) => `${30 - v}d`}
          tick={tickStyle}
          axisLine={tickAxis}
          tickLine={tickAxis}
        />
        <YAxis type="number" dataKey="y" hide domain={[-1, 1]} />
        {(["primary", "secondary", "tertiary"] as const).map((t) => (
          <Scatter
            key={t}
            data={points.filter((p) => p.type === t)}
            fill={colorByType[t]}
            shape="circle"
            isAnimationActive={false}
          />
        ))}
      </ScatterChart>
    </ResponsiveContainer>
  );
};

/* ─────────────────── 7. Sparkline with threshold ─────────────────── */
export const SparklineThreshold = ({
  values,
  threshold,
}: {
  values: number[];
  threshold: number;
}) => {
  const data = values.map((v, i) => ({ x: i, value: v }));
  return (
    <ResponsiveContainer width="100%" height={56}>
      <LineChart data={data} margin={{ top: 6, right: 6, bottom: 6, left: 6 }}>
        <XAxis dataKey="x" hide />
        <YAxis hide domain={["auto", "auto"]} />
        <ReferenceLine
          y={threshold}
          stroke={TERRACOTTA}
          strokeDasharray="2 3"
          strokeWidth={1}
        />
        <Line
          type="linear"
          dataKey="value"
          stroke={INK}
          strokeWidth={1.25}
          dot={false}
          isAnimationActive={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
};

/* ─────────────────── 8. Density dot grid ─────────────────── */
export const DensityDotGrid = ({
  total,
  warning,
  critical,
  cols = 16,
  cell = 12,
  gap = 4,
}: {
  total: number;
  warning: number;
  critical: number;
  cols?: number;
  cell?: number;
  gap?: number;
}) => {
  const rows = Math.ceil(total / cols);
  const w = cols * cell + (cols - 1) * gap;
  const h = rows * cell + (rows - 1) * gap;
  const criticalSet = new Set(
    Array.from({ length: critical }, (_, i) => i * 17 + 11).filter(
      (n) => n < total,
    ),
  );
  const warningSet = new Set(
    Array.from({ length: warning }, (_, i) => i * 11 + 5)
      .filter((n) => n < total && !criticalSet.has(n)),
  );

  return (
    <div style={{ display: "flex" }}>
      <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`}>
        {Array.from({ length: total }, (_, i) => {
          const col = i % cols;
          const row = Math.floor(i / cols);
          const x = col * (cell + gap);
          const y = row * (cell + gap);
          if (criticalSet.has(i)) {
            return (
              <rect
                key={i}
                x={x}
                y={y}
                width={cell}
                height={cell}
                fill={TERRACOTTA}
              />
            );
          }
          if (warningSet.has(i)) {
            return (
              <rect
                key={i}
                x={x + 1}
                y={y + 1}
                width={cell - 2}
                height={cell - 2}
                fill="none"
                stroke={TERRACOTTA}
                strokeWidth={1}
              />
            );
          }
          return (
            <rect
              key={i}
              x={x + 1}
              y={y + 1}
              width={cell - 2}
              height={cell - 2}
              fill="none"
              stroke={HAIRLINE}
              strokeWidth={1}
            />
          );
        })}
      </svg>
    </div>
  );
};

/* ─────────────────── 9. Sparkline + by-system bars ─────────────────── */
export const SparklinePlusBars = ({
  trend,
  bars,
}: {
  trend: number[];
  bars: { name: string; value: number }[];
}) => {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
      <div>
        <div
          style={{
            fontFamily: MONO,
            fontSize: 9,
            letterSpacing: "0.12em",
            color: FAINT,
            marginBottom: 4,
          }}
        >
          30D TREND
        </div>
        <ResponsiveContainer width="100%" height={56}>
          <LineChart
            data={trend.map((v, i) => ({ x: i, value: v }))}
            margin={{ top: 4, right: 4, bottom: 4, left: 4 }}
          >
            <XAxis dataKey="x" hide />
            <YAxis hide domain={["auto", "auto"]} />
            <Line
              type="linear"
              dataKey="value"
              stroke={INK}
              strokeWidth={1.25}
              dot={false}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div>
        <div
          style={{
            fontFamily: MONO,
            fontSize: 9,
            letterSpacing: "0.12em",
            color: FAINT,
            marginBottom: 4,
          }}
        >
          BY SYSTEM
        </div>
        <SortedSeverity items={bars} />
      </div>
    </div>
  );
};

/* ─────────────────── 10. Confidence histogram ─────────────────── */
export const ConfidenceHistogram = ({
  buckets,
  threshold,
}: {
  buckets: { range: string; count: number }[];
  threshold: number;
}) => {
  return (
    <ResponsiveContainer width="100%" height={92}>
      <BarChart
        data={buckets}
        margin={{ top: 8, right: 8, bottom: 22, left: 0 }}
      >
        <XAxis
          dataKey="range"
          tick={tickStyle}
          axisLine={tickAxis}
          tickLine={false}
        />
        <YAxis hide />
        <ReferenceLine
          x={threshold}
          stroke={TERRACOTTA}
          strokeDasharray="2 3"
          strokeWidth={1}
        />
        <Bar
          dataKey="count"
          fill={INK}
          barSize={20}
          isAnimationActive={false}
        />
      </BarChart>
    </ResponsiveContainer>
  );
};

/* ─────────────────── 11. Mini lineage ─────────────────── */
export const MiniLineage = ({
  nodes,
  edges,
  width = 360,
  height = 110,
}: {
  nodes: { id: string; label: string; x: number; y: number; tone?: "default" | "new" }[];
  edges: { from: string; to: string; tone?: "default" | "new" }[];
  width?: number;
  height?: number;
}) => {
  const pos = Object.fromEntries(nodes.map((n) => [n.id, n]));
  return (
    <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`}>
      {edges.map((e, i) => {
        const a = pos[e.from];
        const b = pos[e.to];
        if (!a || !b) return null;
        return (
          <line
            key={i}
            x1={a.x}
            y1={a.y}
            x2={b.x}
            y2={b.y}
            stroke={e.tone === "new" ? TERRACOTTA : HAIRLINE}
            strokeWidth={e.tone === "new" ? 1.5 : 1}
            strokeDasharray={e.tone === "new" ? undefined : "2 3"}
          />
        );
      })}
      {nodes.map((n) => (
        <g key={n.id}>
          <circle
            cx={n.x}
            cy={n.y}
            r={4}
            fill={n.tone === "new" ? TERRACOTTA : INK}
          />
          <text
            x={n.x}
            y={n.y + 18}
            textAnchor="middle"
            fontFamily={SANS}
            fontSize={10}
            fill={MUTED}
          >
            {n.label}
          </text>
        </g>
      ))}
    </svg>
  );
};

/* ─────────────────── 12. Proportion donut ─────────────────── */
export const ProportionDonut = ({
  value,
  total = 100,
  unit = "%",
}: {
  value: number;
  total?: number;
  unit?: string;
}) => {
  const size = 132;
  const stroke = 6;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const filled = Math.min(c, (value / total) * c);
  return (
    <div style={{ display: "flex", justifyContent: "center" }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={HAIRLINE}
          strokeWidth={stroke}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={INK}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={`${filled} ${c}`}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
        />
        <text
          x={size / 2}
          y={size / 2 - 2}
          textAnchor="middle"
          dominantBaseline="middle"
          fontFamily={MONO}
          fontSize={28}
          fill={INK}
          letterSpacing="-0.02em"
        >
          {value}
        </text>
        <text
          x={size / 2}
          y={size / 2 + 22}
          textAnchor="middle"
          dominantBaseline="middle"
          fontFamily={MONO}
          fontSize={9}
          fill={FAINT}
          letterSpacing="0.14em"
        >
          {unit} REACHABLE
        </text>
      </svg>
    </div>
  );
};

/* ─────────────────── 13. Slope lines ─────────────────── */
export const SlopeLines = ({
  items,
  domain = [0, 100],
}: {
  items: { name: string; from: number; to: number; tone?: "up" | "down" | "neutral" }[];
  domain?: [number, number];
}) => {
  const data = [
    items.reduce<Record<string, number | string>>(
      (acc, s) => ((acc[s.name] = s.from), acc),
      { x: 0 },
    ),
    items.reduce<Record<string, number | string>>(
      (acc, s) => ((acc[s.name] = s.to), acc),
      { x: 1 },
    ),
  ];
  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: 16 }}>
      <ResponsiveContainer width="100%" height={92}>
        <LineChart data={data} margin={{ top: 8, right: 8, bottom: 8, left: 8 }}>
          <XAxis dataKey="x" hide />
          <YAxis hide domain={domain} />
          {items.map((s) => {
            const c =
              s.tone === "up"
                ? TERRACOTTA
                : s.tone === "down"
                  ? OLIVE
                  : INK;
            return (
              <Line
                key={s.name}
                type="linear"
                dataKey={s.name}
                stroke={c}
                strokeWidth={1.25}
                dot={{ r: 2, fill: c, stroke: c }}
                isAnimationActive={false}
              />
            );
          })}
        </LineChart>
      </ResponsiveContainer>
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          fontFamily: MONO,
          fontSize: 9,
          color: FAINT,
          letterSpacing: "0.10em",
          paddingTop: 4,
          paddingBottom: 4,
        }}
      >
        <span>30D AGO</span>
        <span>NOW</span>
      </div>
    </div>
  );
};

/* ─────────────────── Card → viz registry ─────────────────── */

export const CardViz = ({ id }: { id: string }) => {
  switch (id) {
    case "dsr-sla":
      return (
        <DeadlineStrip
          items={[
            { id: 1, daysLeft: 0.6 },
            { id: 2, daysLeft: 0.75 },
            { id: 3, daysLeft: 0.92 },
            { id: 4, daysLeft: 1.2 },
            { id: 5, daysLeft: 1.5 },
            { id: 6, daysLeft: 2 },
            { id: 7, daysLeft: 2.5 },
            { id: 8, daysLeft: 3 },
            { id: 9, daysLeft: 4 },
            { id: 10, daysLeft: 8 },
            { id: 11, daysLeft: 12 },
            { id: 12, daysLeft: 18 },
            { id: 13, daysLeft: 24 },
          ]}
          riskUnderDays={2}
          maxDays={30}
        />
      );
    case "dsr-stuck":
      return (
        <StackedBreakdown
          segments={[
            { key: "verify", label: "Identity verify", value: 5 },
            { key: "connector", label: "Connector down", value: 2 },
            { key: "retry", label: "Retry queued", value: 1 },
          ]}
        />
      );
    case "dsr-failed":
      return (
        <SortedSeverity
          accent
          items={[
            { name: "Postgres · users", value: 5 },
            { name: "HubSpot · contacts", value: 3 },
            { name: "Mixpanel · profiles", value: 2 },
          ]}
        />
      );
    case "dsr-verify":
      return (
        <QueueWithAge
          depths={[8, 9, 11, 12, 13, 14, 14]}
          oldestHours={19}
          slaHours={12}
        />
      );
    case "dsr-escalations":
      return (
        <RowListSparkline
          items={[
            {
              label: "Refile · analytics events",
              meta: "3 subjects",
              tone: "attention",
            },
          ]}
          trend={[1, 1, 2, 2, 3, 3, 3]}
        />
      );

    case "pol-retention":
      return (
        <SortedSeverity
          accent
          items={[
            { name: "analytics_events", value: 1200 },
            { name: "session_logs", value: 184 },
            { name: "support_tickets", value: 9 },
          ]}
          unit="k"
        />
      );
    case "pol-sensitive":
      return (
        <StackedBreakdown
          segments={[
            { key: "pii", label: "PII", value: 5 },
            { key: "email", label: "Email", value: 4 },
            { key: "ssn", label: "SSN-like", value: 2 },
          ]}
        />
      );
    case "pol-web":
      return (
        <StackedBreakdown
          segments={[
            { key: "ad", label: "Ad pixels", value: 2 },
            { key: "analytics", label: "Analytics", value: 2 },
            { key: "session", label: "Session", value: 1 },
          ]}
        />
      );
    case "pol-sla":
      return (
        <SparklineThreshold
          values={[2, 3, 4, 5, 6, 7, 7]}
          threshold={5}
        />
      );
    case "pol-ai":
      return (
        <RowListSparkline
          items={[
            { label: "support-bot v3", meta: "missing IA", tone: "attention" },
            {
              label: "fraud-classifier",
              meta: "prohibited input",
              tone: "attention",
            },
          ]}
          trend={[0, 1, 1, 2, 2, 2, 2]}
        />
      );

    case "cov-new":
      return (
        <TimelineOfFinds
          finds={[
            { day: 4, type: "primary" },
            { day: 8, type: "secondary" },
            { day: 12, type: "primary" },
            { day: 18, type: "primary" },
            { day: 22, type: "tertiary" },
            { day: 26, type: "secondary" },
          ]}
        />
      );
    case "cov-stale":
      return (
        <SortedSeverity
          items={[
            { name: "mongo://crm-archive", value: 62 },
            { name: "bigquery://eu-marketing", value: 47 },
            { name: "redshift://growth", value: 38 },
            { name: "s3://ops-logs", value: 32 },
          ]}
          threshold={30}
          unit="d"
        />
      );
    case "cov-conn":
      return (
        <SortedSeverity
          accent
          items={[
            { name: "salesforce-prod", value: 12 },
            { name: "stripe-eu", value: 8 },
            { name: "hubspot-eu", value: 3 },
            { name: "mixpanel", value: 2 },
          ]}
          unit=" fails"
        />
      );
    case "cov-drift":
      return (
        <SparklinePlusBars
          trend={[2, 4, 6, 9, 12, 15, 18]}
          bars={[
            { name: "users", value: 7 },
            { name: "orders", value: 6 },
            { name: "events_v2", value: 5 },
          ]}
        />
      );
    case "cov-fulfill":
      return <ProportionDonut value={91} total={100} unit="%" />;

    case "cls-gaps":
      return (
        <StackedBreakdown
          segments={[
            { key: "marketing", label: "Marketing", value: 12 },
            { key: "product", label: "Product", value: 18 },
            { key: "support", label: "Support", value: 12 },
          ]}
        />
      );
    case "cls-low":
      return (
        <ConfidenceHistogram
          threshold={0.7}
          buckets={[
            { range: "0.5", count: 2 },
            { range: "0.6", count: 6 },
            { range: "0.7", count: 8 },
            { range: "0.8", count: 2 },
          ]}
        />
      );
    case "cls-sensitive":
      return (
        <StackedBreakdown
          segments={[
            { key: "pii", label: "PII", value: 7 },
            { key: "email", label: "Email", value: 4 },
          ]}
        />
      );
    case "cls-lineage":
      return (
        <MiniLineage
          nodes={[
            { id: "a", label: "raw.users", x: 30, y: 30 },
            { id: "b", label: "stg.users", x: 140, y: 30 },
            { id: "c", label: "dim_users", x: 250, y: 30, tone: "new" },
            { id: "d", label: "growth.events", x: 30, y: 80 },
            { id: "e", label: "fct_orders", x: 250, y: 80, tone: "new" },
          ]}
          edges={[
            { from: "a", to: "b" },
            { from: "b", to: "c", tone: "new" },
            { from: "d", to: "e", tone: "new" },
          ]}
        />
      );
    case "cls-new":
      return (
        <SparklinePlusBars
          trend={[3, 5, 8, 11, 14, 16, 18]}
          bars={[
            { name: "growth", value: 9 },
            { name: "product", value: 5 },
            { name: "ops", value: 4 },
          ]}
        />
      );

    case "ai-new":
      return (
        <TimelineOfFinds
          finds={[
            { day: 6, type: "primary" },
            { day: 14, type: "primary" },
            { day: 22, type: "secondary" },
          ]}
        />
      );
    case "ai-drift":
      return (
        <SlopeLines
          items={[
            { name: "fraud-classifier", from: 60, to: 82, tone: "up" },
            { name: "pricing-optimizer", from: 55, to: 78, tone: "up" },
            { name: "support-bot v3", from: 70, to: 70, tone: "neutral" },
            { name: "lead-scoring", from: 50, to: 58, tone: "up" },
          ]}
        />
      );
    case "ai-vendor":
      return (
        <RowListSparkline
          items={[
            { label: "Zendesk", meta: "policy update" },
            { label: "Notion", meta: "new AI feature" },
          ]}
          trend={[0, 0, 1, 1, 2, 2, 2]}
        />
      );
    case "ai-training":
      return (
        <MiniLineage
          width={200}
          height={170}
          nodes={[
            { id: "src", label: "support_tickets", x: 100, y: 24 },
            { id: "ds", label: "finetune-2", x: 100, y: 88, tone: "new" },
            { id: "model", label: "support-bot v3", x: 100, y: 152 },
          ]}
          edges={[
            { from: "src", to: "ds", tone: "new" },
            { from: "ds", to: "model" },
          ]}
        />
      );
    case "ai-fw":
      return (
        <SlopeLines
          items={[
            { name: "Art.10 governance", from: 80, to: 65, tone: "down" },
            { name: "Art.13 transparency", from: 75, to: 60, tone: "down" },
            { name: "Art.9 risk mgmt", from: 70, to: 70, tone: "neutral" },
          ]}
        />
      );

    case "con-drift":
      return (
        <SlopeLines
          items={[
            { name: "DE", from: 88, to: 81, tone: "down" },
            { name: "FR", from: 86, to: 82, tone: "down" },
            { name: "UK", from: 84, to: 82, tone: "down" },
            { name: "US-CA", from: 80, to: 80, tone: "neutral" },
          ]}
        />
      );
    case "con-gaps":
      return (
        <SortedSeverity
          accent
          items={[
            { name: "BR", value: 100 },
            { name: "IN", value: 38 },
            { name: "AU", value: 29 },
            { name: "MX", value: 14 },
          ]}
          unit=" gap"
        />
      );
    case "con-regulatory":
      return (
        <RowListSparkline
          items={[
            { label: "California · CCPA dark patterns", meta: "May 6", tone: "attention" },
            { label: "EU · AI Act biometric consent", meta: "May 2", tone: "attention" },
          ]}
          trend={[0, 0, 1, 1, 1, 2, 2]}
        />
      );
    case "con-records":
      return <SparklineThreshold values={[6, 7, 8, 9, 11, 13, 14]} threshold={10} />;
    case "con-notice":
      return <ProportionDonut value={87} total={100} unit="%" />;
    case "con-revocation":
      return (
        <SparklineThreshold
          values={[120, 132, 145, 168, 220, 310, 384]}
          threshold={180}
        />
      );

    case "asm-pending":
      return (
        <QueueWithAge
          depths={[4, 5, 5, 6, 7, 8, 8]}
          oldestHours={144}
          slaHours={120}
        />
      );
    case "asm-stale":
      return (
        <SortedSeverity
          accent
          items={[
            { name: "Marketing AI", value: 124 },
            { name: "Vendor · Notion", value: 96 },
            { name: "Ad targeting", value: 72 },
            { name: "Vendor · Slack", value: 41 },
          ]}
          unit="d"
          threshold={90}
        />
      );
    case "asm-dpia":
      return (
        <RowListSparkline
          items={[
            { label: "fraud-classifier", meta: "high-risk", tone: "attention" },
            { label: "lead-gen scoring", meta: "high-risk", tone: "attention" },
          ]}
          trend={[0, 0, 1, 1, 2, 2, 2]}
        />
      );
    case "asm-coverage":
      return <ProportionDonut value={73} total={100} unit="%" />;
    case "asm-new":
      return (
        <StackedBreakdown
          segments={[
            { key: "vendor", label: "Vendor", value: 3 },
            { key: "internal", label: "Internal", value: 2 },
          ]}
        />
      );
    case "asm-due":
      return (
        <DeadlineStrip
          items={[
            { id: 1, daysLeft: 5 },
            { id: 2, daysLeft: 7 },
            { id: 3, daysLeft: 9 },
            { id: 4, daysLeft: 14 },
            { id: 5, daysLeft: 20 },
            { id: 6, daysLeft: 27 },
          ]}
          riskUnderDays={7}
          maxDays={30}
        />
      );

    default:
      return null;
  }
};
