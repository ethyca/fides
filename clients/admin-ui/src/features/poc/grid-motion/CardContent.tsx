import { AnimatePresence, motion } from "framer-motion";
import { CSSProperties, useEffect, useMemo, useRef, useState } from "react";

import { CardSpec } from "./types";

const INK = "#2b2e35";
const INK_MUTED = "#53575c";
const INK_TERTIARY = "#7e8185";
const TRACK = "rgba(43,46,53,0.10)";

const MONO = "'Basier Square Mono', ui-monospace, SFMono-Regular, monospace";

const headerStyle: CSSProperties = {
  fontFamily: MONO,
  fontSize: 9,
  fontWeight: 500,
  letterSpacing: "1.4px",
  textTransform: "uppercase",
  color: INK_TERTIARY,
  lineHeight: 1,
};

const shellStyle: CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: 8,
  width: "100%",
  height: "100%",
};

// ── Atoms ───────────────────────────────────────────────────────────────────

const HBar = ({ label, pct }: { label: string; pct: number }) => (
  <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "baseline",
        fontFamily: MONO,
        fontSize: 9,
        letterSpacing: "1.2px",
        textTransform: "uppercase",
      }}
    >
      <span style={{ color: INK_TERTIARY }}>{label}</span>
      <span style={{ color: INK, fontSize: 11, letterSpacing: 0 }}>{pct}%</span>
    </div>
    <div
      style={{
        height: 4,
        background: TRACK,
        borderRadius: 2,
        position: "relative",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          position: "absolute",
          left: 0,
          top: 0,
          bottom: 0,
          width: `${pct}%`,
          background: INK,
        }}
      />
    </div>
  </div>
);

const ConcentricDonuts = ({
  outer,
  inner,
  size = 56,
}: {
  outer: number;
  inner: number;
  size?: number;
}) => {
  const outerR = size / 2 - 3;
  const innerR = size / 2 - 13;
  const outerC = 2 * Math.PI * outerR;
  const innerC = 2 * Math.PI * innerR;
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      <g transform={`rotate(-90 ${size / 2} ${size / 2})`}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={outerR}
          fill="none"
          stroke={TRACK}
          strokeWidth={3}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={outerR}
          fill="none"
          stroke={INK}
          strokeOpacity={0.85}
          strokeWidth={3}
          strokeDasharray={outerC}
          strokeDashoffset={outerC * (1 - outer / 100)}
          strokeLinecap="butt"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={innerR}
          fill="none"
          stroke={TRACK}
          strokeWidth={3}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={innerR}
          fill="none"
          stroke={INK}
          strokeOpacity={0.55}
          strokeWidth={3}
          strokeDasharray={innerC}
          strokeDashoffset={innerC * (1 - inner / 100)}
          strokeLinecap="butt"
        />
      </g>
    </svg>
  );
};

const Donut = ({ pct, size = 36 }: { pct: number; size?: number }) => {
  const r = size / 2 - 3;
  const c = 2 * Math.PI * r;
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      <g transform={`rotate(-90 ${size / 2} ${size / 2})`}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={TRACK}
          strokeWidth={3}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={INK}
          strokeWidth={3}
          strokeDasharray={c}
          strokeDashoffset={c * (1 - pct / 100)}
          strokeLinecap="butt"
        />
      </g>
    </svg>
  );
};

const Sankey = ({
  sources,
  targets,
  edges,
}: {
  sources: { label: string; value: number }[];
  targets: { label: string; value: number }[];
  edges: {
    from: number;
    to: number;
    value: number;
    salient?: boolean;
  }[];
}) => {
  const W = 240;
  const H = 80;
  const bandX = 6;
  const bandW = 4;
  const padY = 4;
  const bandGap = 4;
  const MIN_FLOW_H = 1.5;
  const usableH = H - padY * 2;

  const total = Math.max(
    sources.reduce((s, b) => s + b.value, 0),
    targets.reduce((s, b) => s + b.value, 0),
  );

  const nGaps = Math.max(sources.length - 1, targets.length - 1, 0);
  const flowBudget = Math.max(0, usableH - nGaps * bandGap);

  // Salient flows get a minimum visible height so a single-request finding
  // still reads as a ribbon at L1 sizing.
  const salientHeights = edges.map((e) => {
    if (!e.salient) {
      return 0;
    }
    const prop = (e.value / total) * flowBudget;
    return Math.max(MIN_FLOW_H, prop);
  });
  const salientTotalH = salientHeights.reduce((a, b) => a + b, 0);
  const nonSalientShare = Math.max(0, flowBudget - salientTotalH);
  const nonSalientValueTotal = edges
    .filter((e) => !e.salient)
    .reduce((s, e) => s + e.value, 0);

  const edgeH = edges.map((e, i) => {
    if (e.salient) {
      return salientHeights[i];
    }
    return nonSalientValueTotal > 0
      ? (e.value / nonSalientValueTotal) * nonSalientShare
      : 0;
  });

  // Non-salient first (drawn under), salient last (drawn on top and stacked
  // at the bottom of each band so they read as a tail).
  const orderedIndices = edges
    .map((_, i) => i)
    .sort((a, b) => Number(!!edges[a].salient) - Number(!!edges[b].salient));

  const sourceLayout: { y: number; h: number; cursor: number }[] = [];
  sources.reduce((cursorY, _, i) => {
    const h = orderedIndices
      .filter((idx) => edges[idx].from === i)
      .reduce((acc, idx) => acc + edgeH[idx], 0);
    sourceLayout.push({ y: cursorY, h, cursor: cursorY });
    return cursorY + h + bandGap;
  }, padY);

  const targetLayout: { y: number; h: number; cursor: number }[] = [];
  targets.reduce((cursorY, _, i) => {
    const h = orderedIndices
      .filter((idx) => edges[idx].to === i)
      .reduce((acc, idx) => acc + edgeH[idx], 0);
    targetLayout.push({ y: cursorY, h, cursor: cursorY });
    return cursorY + h + bandGap;
  }, padY);

  // Precompute each edge's source/target y position so labels can land
  // exactly at salient flow endpoints.
  const flowGeometry: { sy: number; ty: number }[] = new Array(edges.length);
  {
    const sCursors = sourceLayout.map((b) => b.y);
    const tCursors = targetLayout.map((b) => b.y);
    orderedIndices.forEach((idx) => {
      const edge = edges[idx];
      flowGeometry[idx] = {
        sy: sCursors[edge.from],
        ty: tCursors[edge.to],
      };
      sCursors[edge.from] += edgeH[idx];
      tCursors[edge.to] += edgeH[idx];
    });
  }

  const sourceSalientCount = sources.map((_, i) =>
    edges
      .filter((e) => e.from === i && e.salient)
      .reduce((sum, e) => sum + e.value, 0),
  );

  const labelStyle: CSSProperties = {
    position: "absolute",
    fontFamily: MONO,
    fontSize: 9,
    letterSpacing: "1.2px",
    textTransform: "uppercase",
    color: INK,
    lineHeight: 1,
    whiteSpace: "nowrap",
    pointerEvents: "none",
    textShadow:
      "0 0 3px #fff, 0 0 3px #fff, 0 0 2px #fff, 0 0 2px #fff, 0 0 1px #fff",
  };

  return (
    <div style={{ position: "relative", width: "100%", height: "100%" }}>
      <svg
        width="100%"
        height="100%"
        viewBox={`0 0 ${W} ${H}`}
        preserveAspectRatio="none"
        style={{ display: "block" }}
      >
        {sourceLayout.map((b, i) => (
          <rect
            key={`s-${i}`}
            x={bandX}
            y={b.y}
            width={bandW}
            height={b.h}
            fill={INK}
            fillOpacity={0.45}
          />
        ))}
        {targetLayout.map((b, i) => (
          <rect
            key={`t-${i}`}
            x={W - bandX - bandW}
            y={b.y}
            width={bandW}
            height={b.h}
            fill={INK}
            fillOpacity={0.45}
          />
        ))}
        {orderedIndices.map((idx) => {
          const edge = edges[idx];
          const h = edgeH[idx];
          const { sy, ty } = flowGeometry[idx];
          const x1 = bandX + bandW;
          const x2 = W - bandX - bandW;
          const cx1 = x1 + (x2 - x1) * 0.45;
          const cx2 = x2 - (x2 - x1) * 0.45;
          const d = `M ${x1} ${sy} C ${cx1} ${sy} ${cx2} ${ty} ${x2} ${ty} L ${x2} ${ty + h} C ${cx2} ${ty + h} ${cx1} ${sy + h} ${x1} ${sy + h} Z`;
          return (
            <path
              key={`e-${idx}`}
              d={d}
              fill={INK}
              fillOpacity={edge.salient ? 1 : 0.2}
            />
          );
        })}
      </svg>
      {sources.map((s, i) => {
        const b = sourceLayout[i];
        const centerPct = ((b.y + b.h / 2) / H) * 100;
        const count = sourceSalientCount[i];
        return (
          <div
            key={`sl-${s.label}`}
            style={{
              ...labelStyle,
              left: `${((bandX + bandW + 2) / W) * 100}%`,
              top: `${centerPct}%`,
              transform: "translateY(-50%)",
            }}
          >
            {s.label}
            {count > 0 ? (
              <span style={{ color: INK_TERTIARY }}>{` · ${count}`}</span>
            ) : null}
          </div>
        );
      })}
      {targets.map((t, i) => {
        const b = targetLayout[i];
        const centerPct = ((b.y + b.h / 2) / H) * 100;
        return (
          <div
            key={`tl-${t.label}`}
            style={{
              ...labelStyle,
              right: `${((bandX + bandW + 2) / W) * 100}%`,
              top: `${centerPct}%`,
              transform: "translateY(-50%)",
              textAlign: "right",
            }}
          >
            {t.label}
          </div>
        );
      })}
      {edges.map((e, idx) => {
        if (!e.salient) {
          return null;
        }
        const h = edgeH[idx];
        const { ty } = flowGeometry[idx];
        const centerPct = ((ty + h / 2) / H) * 100;
        return (
          <div
            key={`fn-${e.from}-${e.to}`}
            style={{
              ...labelStyle,
              right: `${((bandX + bandW + 2) / W) * 100}%`,
              top: `${centerPct}%`,
              transform: "translateY(-50%)",
              textAlign: "right",
              letterSpacing: 0,
              fontWeight: 500,
            }}
          >
            {e.value}
          </div>
        );
      })}
    </div>
  );
};

const HourlyBar = ({
  hours,
  criticalIndices,
  colWidth = 8,
  gap = 2,
}: {
  hours: { total: number; violations: number }[];
  criticalIndices: number[];
  colWidth?: number;
  gap?: number;
}) => {
  const max = Math.max(...hours.map((h) => h.total));
  return (
    <div
      style={{
        display: "flex",
        alignItems: "flex-end",
        gap,
        height: "100%",
        width: "100%",
        overflow: "hidden",
      }}
    >
      {hours.map((h, i) => {
        const totalH = (h.total / max) * 100;
        const violationH = (h.violations / h.total) * totalH;
        const isCritical = criticalIndices.includes(i);
        return (
          <div
            key={i}
            style={{
              width: colWidth,
              minWidth: colWidth,
              height: "100%",
              display: "flex",
              flexDirection: "column",
              justifyContent: "flex-end",
            }}
          >
            <div
              style={{
                position: "relative",
                height: `${totalH}%`,
                background: TRACK,
              }}
            >
              <div
                style={{
                  position: "absolute",
                  left: 0,
                  right: 0,
                  top: 0,
                  height: `${(h.violations / h.total) * 100}%`,
                  background: INK,
                  opacity: isCritical ? 1 : 0.85,
                }}
              />
              {/* avoid unused var warning while keeping shape symmetric */}
              <div style={{ display: "none" }}>{violationH}</div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

const POLICY_GLASS_H = 76;
const POLICY_BAR_W = 8;
const POLICY_BAR_GAP = 2;
const POLICY_BAR_COUNT = 240;

const POLICY_BAR_HOURS = Array.from({ length: POLICY_BAR_COUNT }, (_, i) => {
  const total =
    80 + Math.round(Math.sin(i * 0.4) * 25 + Math.sin(i * 0.13) * 18);
  const violations = Math.max(2, Math.round(total * (0.05 + (i % 5) * 0.02)));
  return { total, violations };
});

const POLICY_CRITICAL_INDICES = Array.from({ length: POLICY_BAR_COUNT })
  .map((_, i) => i)
  .filter((i) => i % 7 === 3 || i % 11 === 5);

const HourlyBarScroll = () => {
  const innerWidth =
    POLICY_BAR_COUNT * (POLICY_BAR_W + POLICY_BAR_GAP) - POLICY_BAR_GAP;
  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        overflowX: "auto",
        overflowY: "hidden",
      }}
    >
      <div style={{ width: innerWidth, height: "100%" }}>
        <HourlyBar
          hours={POLICY_BAR_HOURS}
          criticalIndices={POLICY_CRITICAL_INDICES}
          colWidth={POLICY_BAR_W}
          gap={POLICY_BAR_GAP}
        />
      </div>
    </div>
  );
};

// ── Per-card renderers ──────────────────────────────────────────────────────

const Coverage = () => (
  <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
    <HBar label="Managed" pct={73} />
    <HBar label="Classified" pct={82} />
  </div>
);

const ClassificationHealth = () => (
  <div
    style={{
      display: "flex",
      alignItems: "center",
      gap: 14,
      height: "100%",
    }}
  >
    <ConcentricDonuts outer={78} inner={54} size={62} />
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 4,
        fontFamily: MONO,
      }}
    >
      <div style={{ fontSize: 18, color: INK, lineHeight: 1 }}>78%</div>
      <div
        style={{
          fontSize: 9,
          letterSpacing: "1.2px",
          textTransform: "uppercase",
          color: INK_TERTIARY,
        }}
      >
        Overall
      </div>
      <div
        style={{
          fontSize: 11,
          color: INK_MUTED,
          lineHeight: 1,
          marginTop: 4,
        }}
      >
        54%
      </div>
      <div
        style={{
          fontSize: 9,
          letterSpacing: "1.2px",
          textTransform: "uppercase",
          color: INK_TERTIARY,
        }}
      >
        AI-specific
      </div>
    </div>
  </div>
);

const ConsentAlignment = () => (
  <div
    style={{
      display: "flex",
      flexDirection: "column",
      gap: 12,
      height: "100%",
    }}
  >
    <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
      <div
        style={{
          fontFamily: MONO,
          fontSize: 32,
          color: INK,
          lineHeight: 1,
          letterSpacing: "-0.02em",
        }}
      >
        9
      </div>
      <div
        style={{
          fontFamily: MONO,
          fontSize: 9,
          letterSpacing: "1.4px",
          textTransform: "uppercase",
          color: INK_MUTED,
        }}
      >
        Fired without consent
      </div>
    </div>
    <div style={{ flex: 1, minHeight: 0 }}>
      <Sankey
        sources={[
          { label: "Opt-in", value: 740 },
          { label: "Mixed", value: 215 },
          { label: "Opt-out", value: 9 },
        ]}
        targets={[
          { label: "Advertising", value: 357 },
          { label: "Analytics", value: 262 },
          { label: "Functional", value: 170 },
          { label: "Personalization", value: 105 },
          { label: "Essential", value: 70 },
        ]}
        edges={[
          { from: 0, to: 0, value: 280 },
          { from: 0, to: 1, value: 200 },
          { from: 0, to: 2, value: 130 },
          { from: 0, to: 3, value: 80 },
          { from: 0, to: 4, value: 50 },
          { from: 1, to: 0, value: 70 },
          { from: 1, to: 1, value: 60 },
          { from: 1, to: 2, value: 40 },
          { from: 1, to: 3, value: 25 },
          { from: 1, to: 4, value: 20 },
          { from: 2, to: 0, value: 7, salient: true },
          { from: 2, to: 1, value: 2, salient: true },
        ]}
      />
    </div>
  </div>
);

const DsrCompliance = () => (
  <div
    style={{
      display: "flex",
      justifyContent: "space-between",
      alignItems: "stretch",
      gap: 12,
      height: "100%",
    }}
  >
    <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
      <div
        style={{
          fontFamily: MONO,
          fontSize: 32,
          color: INK,
          lineHeight: 1,
          letterSpacing: "-0.02em",
        }}
      >
        47
      </div>
      <div
        style={{
          fontFamily: MONO,
          fontSize: 9,
          letterSpacing: "1.4px",
          textTransform: "uppercase",
          color: INK_TERTIARY,
        }}
      >
        Active DSRs
      </div>
    </div>
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        alignItems: "flex-end",
        gap: 4,
        flex: 1,
      }}
    >
      <div
        style={{
          fontFamily: MONO,
          fontSize: 11,
          letterSpacing: "1.2px",
          textTransform: "uppercase",
          color: INK,
        }}
      >
        3 overdue
      </div>
      <div style={{ width: "100%" }}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            fontFamily: MONO,
            fontSize: 8,
            letterSpacing: "1px",
            textTransform: "uppercase",
            color: INK_TERTIARY,
            marginBottom: 3,
          }}
        >
          <span>SLA</span>
          <span>92%</span>
        </div>
        <div
          style={{
            height: 3,
            display: "flex",
            background: TRACK,
            borderRadius: 1.5,
            overflow: "hidden",
          }}
        >
          <div style={{ width: "92%", background: INK }} />
          <div style={{ flex: 1, background: INK, opacity: 0.4 }} />
        </div>
      </div>
    </div>
  </div>
);

const PolicyEnforcement = () => (
  <div
    style={{
      display: "flex",
      flexDirection: "column",
      height: "100%",
      gap: 8,
    }}
  >
    <div
      style={{
        display: "flex",
        alignItems: "baseline",
        gap: 8,
      }}
    >
      <div
        style={{
          fontFamily: MONO,
          fontSize: 32,
          color: INK,
          lineHeight: 1,
          letterSpacing: "-0.02em",
        }}
      >
        47
      </div>
      <div
        style={{
          fontFamily: MONO,
          fontSize: 9,
          letterSpacing: "1.4px",
          textTransform: "uppercase",
          color: INK_TERTIARY,
        }}
      >
        Violations
      </div>
    </div>
    <div
      style={{
        flex: 1,
        minHeight: 0,
        marginLeft: -14,
        marginRight: -14,
        marginBottom: -14,
      }}
    >
      <HourlyBarScroll />
    </div>
  </div>
);

// ── Policy Enforcement L2 (expanded) ────────────────────────────────────────

type PolicyResult = "Violation" | "Gap";

interface PolicyEvent {
  id: number;
  ts: string;
  result: PolicyResult;
  consumer: string;
  dataset: string;
  reason: string;
}

const POLICY_CONSUMERS = [
  { slug: "ad-targeting", weight: 5 },
  { slug: "recommend-engine", weight: 4 },
  { slug: "lookalike-modeler", weight: 3 },
  { slug: "marketing-attribution", weight: 2 },
  { slug: "churn-predictor", weight: 2 },
  { slug: "fraud-detector", weight: 1 },
];

const POLICY_DATASETS = [
  "events.web",
  "transactions.orders",
  "users.profile",
  "inventory.products",
];

const POLICY_REASONS = [
  "Purpose mismatch",
  "User not mapped",
  "Dataset purpose missing",
];

const formatTime = (d: Date) =>
  [d.getHours(), d.getMinutes(), d.getSeconds()]
    .map((n) => String(n).padStart(2, "0"))
    .join(":");

const pickWeighted = <T extends { weight: number }>(items: T[]): T => {
  const total = items.reduce((s, it) => s + it.weight, 0);
  let r = Math.random() * total;
  return (
    items.find((it) => {
      r -= it.weight;
      return r <= 0;
    }) ?? items[items.length - 1]
  );
};

const generatePolicyEvent = (id: number, when: Date): PolicyEvent => {
  const consumer = pickWeighted(POLICY_CONSUMERS).slug;
  const dataset =
    POLICY_DATASETS[Math.floor(Math.random() * POLICY_DATASETS.length)];
  const reason =
    POLICY_REASONS[Math.floor(Math.random() * POLICY_REASONS.length)];
  const result: PolicyResult = Math.random() < 0.75 ? "Violation" : "Gap";
  return { id, ts: formatTime(when), result, consumer, dataset, reason };
};

const seedPolicyEvents = (count: number): PolicyEvent[] => {
  const now = Date.now();
  return Array.from({ length: count }, (_, i) =>
    generatePolicyEvent(count - i, new Date(now - i * 2500)),
  );
};

const PolicyLogRow = ({
  event,
  onClick,
}: {
  event: PolicyEvent;
  onClick: (event: PolicyEvent) => void;
}) => (
  <div
    role="button"
    tabIndex={0}
    onClick={(e) => {
      e.stopPropagation();
      onClick(event);
    }}
    onKeyDown={(e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        e.stopPropagation();
        onClick(event);
      }
    }}
    className="pol-row"
    style={{
      display: "flex",
      alignItems: "center",
      gap: 8,
      fontFamily: MONO,
      fontSize: 9,
      lineHeight: 1,
      height: 16,
      paddingLeft: 4,
      paddingRight: 4,
      animation: "polRowIn 280ms ease-out",
      cursor: "pointer",
    }}
  >
    <span
      style={{
        color: INK_TERTIARY,
        fontVariantNumeric: "tabular-nums",
        flexShrink: 0,
      }}
    >
      {event.ts}
    </span>
    <span
      style={{
        width: 5,
        height: 5,
        flexShrink: 0,
        background: event.result === "Violation" ? INK : "transparent",
        border: `1px solid ${INK}`,
        boxSizing: "border-box",
      }}
    />
    <span
      style={{
        color: INK,
        letterSpacing: "1.2px",
        textTransform: "uppercase",
        flexShrink: 0,
      }}
    >
      {event.consumer}
    </span>
    <span style={{ color: INK_TERTIARY, flexShrink: 0 }}>·</span>
    <span style={{ color: INK_MUTED, flexShrink: 0 }}>{event.dataset}</span>
    <span
      style={{
        color: INK_MUTED,
        flex: 1,
        minWidth: 0,
        overflow: "hidden",
        textOverflow: "ellipsis",
        whiteSpace: "nowrap",
      }}
    >
      {event.reason}
    </span>
  </div>
);

const POLICY_QUERY_TEXTS: Record<string, string> = {
  "events.web": `SELECT user_id, page_url, event_ts
FROM events.web
WHERE event_type = 'page_view'
  AND event_ts >= NOW() - INTERVAL '24 hours'
LIMIT 1000`,
  "transactions.orders": `SELECT order_id, user_id, total_cents, status
FROM transactions.orders
WHERE created_at >= NOW() - INTERVAL '7 days'
ORDER BY created_at DESC
LIMIT 500`,
  "users.profile": `SELECT user_id, segment, country, created_at
FROM users.profile
WHERE country IN ('US', 'CA', 'GB')
  AND segment IS NOT NULL
LIMIT 2500`,
  "inventory.products": `SELECT sku, category, price_cents, in_stock
FROM inventory.products
WHERE active = true
LIMIT 5000`,
};

const POLICY_DATASET_PURPOSE: Record<string, string> = {
  "events.web": "essential",
  "transactions.orders": "essential",
  "users.profile": "essential",
  "inventory.products": "essential",
};

const POLICY_CONSUMER_PURPOSE: Record<string, string> = {
  "ad-targeting": "marketing.advertising",
  "recommend-engine": "personalization",
  "lookalike-modeler": "marketing.advertising",
  "marketing-attribution": "analytics",
  "churn-predictor": "analytics",
  "fraud-detector": "essential",
};

const pbacDetails = (event: PolicyEvent) => ({
  queryId: `qry_${event.id.toString(16).padStart(6, "0")}`,
  identity: `service:${event.consumer}@svc`,
  consumerPurpose: POLICY_CONSUMER_PURPOSE[event.consumer] ?? "analytics",
  datasetPurpose: POLICY_DATASET_PURPOSE[event.dataset] ?? "essential",
  queryText: POLICY_QUERY_TEXTS[event.dataset] ?? "",
});

const DetailField = ({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) => (
  <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
    <div
      style={{
        fontFamily: MONO,
        fontSize: 9,
        letterSpacing: "1.4px",
        textTransform: "uppercase",
        color: INK_TERTIARY,
        lineHeight: 1,
      }}
    >
      {label}
    </div>
    <div
      style={{
        fontFamily: MONO,
        fontSize: 11,
        color: INK,
        lineHeight: 1.4,
      }}
    >
      {children}
    </div>
  </div>
);

const PolicyDrawer = ({
  event,
  onClose,
}: {
  event: PolicyEvent;
  onClose: () => void;
}) => {
  const details = pbacDetails(event);
  return (
    <motion.div
      initial={{ opacity: 0, x: "100%" }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: "100%" }}
      transition={{ duration: 0.32, ease: [0.22, 1, 0.36, 1] }}
      style={{
        position: "absolute",
        top: 10,
        bottom: 10,
        right: 0,
        width: "70%",
        background: "rgba(248,247,246,0.45)",
        backdropFilter: "blur(18px) saturate(120%)",
        WebkitBackdropFilter: "blur(18px) saturate(120%)",
        borderRadius: 4,
        boxShadow:
          "0 8px 32px rgba(43,46,53,0.10), inset 0 0 0 1px rgba(255,255,255,0.45)",
        padding: 18,
        overflow: "auto",
        zIndex: 10,
        display: "flex",
        flexDirection: "column",
        gap: 14,
      }}
    >
      <button
        type="button"
        aria-label="Close detail"
        onClick={onClose}
        style={{
          position: "absolute",
          top: 10,
          right: 10,
          width: 16,
          height: 16,
          padding: 0,
          border: "none",
          background: "transparent",
          cursor: "pointer",
          color: INK,
          fontFamily: MONO,
          fontSize: 14,
          lineHeight: 1,
          opacity: 0.6,
        }}
      >
        ×
      </button>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 10,
          fontFamily: MONO,
        }}
      >
        <span
          style={{
            fontSize: 11,
            color: INK_TERTIARY,
            fontVariantNumeric: "tabular-nums",
          }}
        >
          {event.ts}
        </span>
        <span
          style={{
            width: 7,
            height: 7,
            background: event.result === "Violation" ? INK : "transparent",
            border: `1px solid ${INK}`,
            boxSizing: "border-box",
          }}
        />
        <span
          style={{
            fontSize: 11,
            letterSpacing: "1.4px",
            textTransform: "uppercase",
            color: INK,
          }}
        >
          {event.result}
        </span>
        <span
          style={{
            fontSize: 11,
            letterSpacing: "1.4px",
            textTransform: "uppercase",
            color: INK,
          }}
        >
          {event.consumer}
        </span>
      </div>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 14,
        }}
      >
        <DetailField label="Query ID">{details.queryId}</DetailField>
        <DetailField label="Identity">{details.identity}</DetailField>
        <DetailField label="Dataset">{event.dataset}</DetailField>
        <DetailField label="Consumer purpose">
          {details.consumerPurpose}
        </DetailField>
      </div>
      <DetailField label={event.reason}>
        {event.result === "Violation"
          ? `Consumer purposes (${details.consumerPurpose}) do not overlap with dataset purposes (${details.datasetPurpose}).`
          : `Dataset ${event.dataset} is missing a purpose declaration; access blocked pending mapping.`}
      </DetailField>
      <DetailField label="Query">
        <pre
          style={{
            margin: 0,
            fontFamily: MONO,
            fontSize: 10,
            lineHeight: 1.5,
            color: INK_MUTED,
            whiteSpace: "pre-wrap",
            wordBreak: "break-word",
            background: "rgba(255,255,255,0.55)",
            padding: "10px 12px",
            borderRadius: 3,
            boxShadow: "inset 0 0 0 1px rgba(255,255,255,0.5)",
          }}
        >
          {details.queryText}
        </pre>
      </DetailField>
      <div
        style={{
          marginTop: "auto",
          display: "flex",
          justifyContent: "flex-end",
          paddingTop: 4,
        }}
      >
        <a
          href="/access-policies"
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 6,
            fontFamily: MONO,
            fontSize: 9,
            letterSpacing: "1.4px",
            textTransform: "uppercase",
            color: "#fff",
            background: INK,
            padding: "8px 14px",
            borderRadius: 2,
            textDecoration: "none",
          }}
        >
          Review policy
          <span aria-hidden style={{ fontSize: 11, lineHeight: 1 }}>
            →
          </span>
        </a>
      </div>
    </motion.div>
  );
};

const ConsumerRow = ({
  slug,
  count,
  max,
}: {
  slug: string;
  count: number;
  max: number;
}) => (
  <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "baseline",
        fontFamily: MONO,
      }}
    >
      <span
        style={{
          fontSize: 9,
          letterSpacing: "1.2px",
          textTransform: "uppercase",
          color: INK,
        }}
      >
        {slug}
      </span>
      <span
        style={{
          fontSize: 13,
          color: INK,
          letterSpacing: 0,
          lineHeight: 1,
        }}
      >
        {count}
      </span>
    </div>
    <div
      style={{
        height: 3,
        background: TRACK,
        borderRadius: 1.5,
        overflow: "hidden",
      }}
    >
      <div
        style={{
          height: "100%",
          width: `${max > 0 ? (count / max) * 100 : 0}%`,
          background: INK,
        }}
      />
    </div>
  </div>
);

const PolicyEnforcementExpanded = () => {
  const [events, setEvents] = useState<PolicyEvent[]>(() =>
    seedPolicyEvents(14),
  );
  const [selectedEventId, setSelectedEventId] = useState<number | null>(null);
  const idRef = useRef(events.length);

  useEffect(() => {
    const tick = () => {
      idRef.current += 1;
      const next = generatePolicyEvent(idRef.current, new Date());
      setEvents((prev) => [next, ...prev].slice(0, 30));
    };
    const interval = setInterval(tick, 2500);
    return () => clearInterval(interval);
  }, []);

  const topConsumers = useMemo(() => {
    const counts = events.reduce((acc, e) => {
      acc.set(e.consumer, (acc.get(e.consumer) ?? 0) + 1);
      return acc;
    }, new Map<string, number>());
    return [...counts.entries()]
      .map(([slug, count]) => ({ slug, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 6);
  }, [events]);

  const maxCount = topConsumers[0]?.count ?? 1;
  const selectedEvent =
    selectedEventId !== null
      ? (events.find((e) => e.id === selectedEventId) ?? null)
      : null;

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        gap: 12,
      }}
    >
      <style>{`
        @keyframes polRowIn { from { opacity: 0.25; transform: translateY(-2px); } to { opacity: 1; transform: translateY(0); } }
        .pol-row { transition: background 0.15s ease-out; border-radius: 2px; }
        .pol-row:hover { background: rgba(43,46,53,0.05); }
      `}</style>
      <div
        style={{
          display: "flex",
          alignItems: "baseline",
          gap: 8,
          flexShrink: 0,
        }}
      >
        <div
          style={{
            fontFamily: MONO,
            fontSize: 32,
            color: INK,
            lineHeight: 1,
            letterSpacing: "-0.02em",
          }}
        >
          47
        </div>
        <div
          style={{
            fontFamily: MONO,
            fontSize: 9,
            letterSpacing: "1.4px",
            textTransform: "uppercase",
            color: INK_TERTIARY,
          }}
        >
          Violations
        </div>
      </div>
      <div
        style={{
          height: POLICY_GLASS_H,
          flexShrink: 0,
          marginLeft: -14,
          marginRight: -14,
          overflow: "hidden",
        }}
      >
        <HourlyBarScroll />
      </div>
      <div
        style={{
          flex: 1,
          minHeight: 0,
          display: "flex",
          gap: 16,
        }}
      >
        <div
          style={{
            flex: 3,
            minWidth: 0,
            display: "flex",
            flexDirection: "column",
            gap: 2,
            marginLeft: -4,
            marginRight: -4,
            overflow: "hidden",
          }}
        >
          {events.slice(0, 25).map((e) => (
            <PolicyLogRow
              key={e.id}
              event={e}
              onClick={(ev) => setSelectedEventId(ev.id)}
            />
          ))}
        </div>
        <div
          style={{
            flex: 2,
            minWidth: 0,
            display: "flex",
            flexDirection: "column",
            gap: 10,
          }}
        >
          {topConsumers.map((c) => (
            <ConsumerRow
              key={c.slug}
              slug={c.slug}
              count={c.count}
              max={maxCount}
            />
          ))}
        </div>
      </div>
      <AnimatePresence>
        {selectedEvent ? (
          <PolicyDrawer
            key={selectedEvent.id}
            event={selectedEvent}
            onClose={() => setSelectedEventId(null)}
          />
        ) : null}
      </AnimatePresence>
    </div>
  );
};

const AiReadiness = () => {
  const ready = 18;
  const partial = 24;
  const notReady = 23;
  const total = ready + partial + notReady;
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 6,
        justifyContent: "flex-end",
        height: "100%",
      }}
    >
      <div
        style={{
          height: 6,
          display: "flex",
          background: TRACK,
          borderRadius: 3,
          overflow: "hidden",
        }}
      >
        <div
          style={{
            width: `${(ready / total) * 100}%`,
            background: INK,
          }}
        />
        <div
          style={{
            width: `${(partial / total) * 100}%`,
            background: INK,
            opacity: 0.65,
          }}
        />
        <div
          style={{
            width: `${(notReady / total) * 100}%`,
            background: INK,
            opacity: 0.3,
          }}
        />
      </div>
      <div
        style={{
          fontFamily: MONO,
          fontSize: 9,
          letterSpacing: "1.4px",
          textTransform: "uppercase",
          color: INK_MUTED,
        }}
      >
        23 missing
      </div>
    </div>
  );
};

const AssessmentCoverage = () => (
  <div
    style={{
      display: "flex",
      alignItems: "center",
      gap: 8,
      height: "100%",
    }}
  >
    <Donut pct={78} size={36} />
    <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
      <div
        style={{
          fontFamily: MONO,
          fontSize: 14,
          color: INK,
          lineHeight: 1,
        }}
      >
        78%
      </div>
      <div
        style={{
          fontFamily: MONO,
          fontSize: 9,
          letterSpacing: "1.2px",
          textTransform: "uppercase",
          color: INK_MUTED,
          lineHeight: 1.2,
        }}
      >
        12 w/o pia
      </div>
    </div>
  </div>
);

// ── Dispatch ────────────────────────────────────────────────────────────────

const PlaceholderL2 = () => (
  <div
    style={{
      width: "100%",
      height: "100%",
      background: "rgba(43,46,53,0.04)",
      borderRadius: 3,
      boxShadow: "inset 0 0 0 1px rgba(43,46,53,0.05)",
    }}
  />
);

const renderL1 = (id: CardSpec["id"]) => {
  switch (id) {
    case "card-tall":
      return <Coverage />;
    case "card-wide-a":
      return <ClassificationHealth />;
    case "card-wide-b":
      return <ConsentAlignment />;
    case "card-unit-a":
      return <DsrCompliance />;
    case "card-unit-b":
      return <PolicyEnforcement />;
    case "card-unit-c":
      return <AiReadiness />;
    case "card-unit-d":
      return <AssessmentCoverage />;
    default:
      return null;
  }
};

const renderL2 = (id: CardSpec["id"]) => {
  switch (id) {
    case "card-unit-b":
      return <PolicyEnforcementExpanded />;
    default:
      return <PlaceholderL2 />;
  }
};

const renderBody = (id: CardSpec["id"], isExpanded: boolean) =>
  isExpanded ? renderL2(id) : renderL1(id);

export const CardContent = ({
  spec,
  isExpanded,
}: {
  spec: CardSpec;
  isExpanded: boolean;
}) => (
  <div style={shellStyle}>
    <div style={headerStyle}>{spec.label}</div>
    <div style={{ flex: 1, minHeight: 0 }}>
      {renderBody(spec.id, isExpanded)}
    </div>
  </div>
);
