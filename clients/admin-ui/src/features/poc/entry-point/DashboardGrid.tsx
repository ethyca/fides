import { AnimatePresence, motion } from "framer-motion";

const serif = "'Eliza', Georgia, serif";
const sans = "'Basier Square', system-ui, sans-serif";
const mono = "'Basier Square Mono', ui-monospace, monospace";

const glass = {
  background: "rgba(255,255,255,0.55)",
  backdropFilter: "blur(14px)",
  WebkitBackdropFilter: "blur(14px)",
  border: "1px solid rgba(32,28,24,0.08)",
  boxShadow: "0 2px 12px rgba(32,28,24,0.04)",
  overflow: "hidden" as const,
  borderRadius: 2,
};

const glassGlow = {
  ...glass,
  border: "1px solid rgba(200,176,138,0.42)",
  boxShadow:
    "0 0 0 1px rgba(200,176,138,0.18), 0 0 22px rgba(200,176,138,0.10), inset 0 0 36px rgba(200,176,138,0.025)",
};

const EASE: [number, number, number, number] = [0.22, 1, 0.36, 1];
const LAYOUT_TRANS = { layout: { duration: 0.45, ease: EASE } };

type Urg = "high" | "med" | "low";
type CardKey = "privacy-requests" | "system-coverage" | "ai-readiness" | "consent";

interface Action {
  urg: Urg;
  verb: string;
  verbHigh?: boolean;
  target: string;
  why: string;
  btns: { label: string; primary?: boolean }[];
}

interface SumCell {
  k: string;
  n: string;
  delta?: string;
  deltaUp?: boolean;
}

const urgColor = (u: Urg) => {
  if (u === "high") return "#c8b08a";
  if (u === "med") return "#6a6a6a";
  return "rgba(32,28,24,0.2)";
};

// ─── Card definitions ──────────────────────────────────────────────────────

const CARDS = [
  {
    key: "privacy-requests" as CardKey,
    title: "Privacy requests",
    big: "14",
    delta: "+3 wk",
    deltaUp: false,
    ctx: "8 in progress · 2 ready · 2 overdue",
    callout: "4 critical actions",
    calloutAmber: true,
    glow: true,
  },
  {
    key: "system-coverage" as CardKey,
    title: "System coverage",
    big: "82%",
    delta: "+4 wk",
    deltaUp: true,
    ctx: "38 classified · 5 unclassified · 4 excluded",
    callout: "1 bulk review · 847 fields",
    calloutAmber: false,
    glow: false,
  },
  {
    key: "ai-readiness" as CardKey,
    title: "AI readiness",
    big: "58",
    delta: "−4 wk",
    deltaUp: false,
    ctx: "3 high-risk · 2 PIAs incomplete",
    callout: "1 launch blocker · resume-screener-v2",
    calloutAmber: false,
    glow: false,
  },
  {
    key: "consent" as CardKey,
    title: "Consent",
    big: "94%",
    delta: "−1 wk",
    deltaUp: false,
    ctx: "DE dropped to 72% after CMP deploy",
    callout: "3 anomalies flagged",
    calloutAmber: false,
    glow: false,
  },
];

type CardDef = (typeof CARDS)[number];

// ─── L card data ───────────────────────────────────────────────────────────

const SUMMARY: Record<CardKey, SumCell[]> = {
  "privacy-requests": [
    { k: "In progress", n: "8" },
    { k: "Ready", n: "2", delta: "approvable", deltaUp: true },
    { k: "At risk", n: "3", delta: "≤72h SLA" },
    { k: "Overdue", n: "2" },
  ],
  "system-coverage": [
    { k: "Classified", n: "38" },
    { k: "Needs review", n: "5" },
    { k: "Excluded", n: "4" },
    { k: "Pending steward", n: "23" },
  ],
  "ai-readiness": [
    { k: "Compliant", n: "6" },
    { k: "High risk", n: "3" },
    { k: "Incomplete PIAs", n: "2" },
    { k: "Blocked", n: "1" },
  ],
  consent: [
    { k: "Opt-in rate", n: "94%", delta: "global" },
    { k: "At risk", n: "3" },
    { k: "DE region", n: "72%", delta: "↓ warning" },
    { k: "Anomalies", n: "3" },
  ],
};

const ACTIONS: Record<CardKey, Action[]> = {
  "privacy-requests": [
    {
      urg: "high",
      verb: "Approve",
      verbHigh: true,
      target: "DSR-4488 · Rectification · ready",
      why: "Astralis · all tasks complete, SLA expires 18h",
      btns: [{ label: "Approve", primary: true }],
    },
    {
      urg: "high",
      verb: "Escalate",
      verbHigh: true,
      target: "DSR-4521 · Erasure · blocked 6d on legal",
      why: "Astralis · two other erasures share upstream lineage, propose batching",
      btns: [{ label: "Escalate", primary: true }, { label: "Batch" }],
    },
    {
      urg: "med",
      verb: "Resolve",
      target: "DSR-4491 · Erasure · enforcement failed ×2",
      why: "Astralis · likely cause: stale Salesforce connector token, rotated 12d ago",
      btns: [{ label: "Retry" }],
    },
    {
      urg: "med",
      verb: "Assign",
      target: "DSR-4504 · Access · unclaimed 4d",
      why: "Astralis · similar prior requests routed to C. Nguyen",
      btns: [{ label: "Assign" }],
    },
    {
      urg: "low",
      verb: "Review",
      target: "7 new requests · auto-triaged",
      why: "3 Access · 2 Erasure · 1 Portability · 1 Rectification · all routine",
      btns: [{ label: "Open" }],
    },
  ],
  "system-coverage": [
    {
      urg: "high",
      verb: "Classify",
      verbHigh: true,
      target: "bq-analytics-prod · 12 unclassified tables",
      why: "Astralis · likely PII in events and user_sessions tables",
      btns: [{ label: "Start", primary: true }],
    },
    {
      urg: "med",
      verb: "Assign",
      target: "snowflake-warehouse-staging · no steward",
      why: "Astralis · 23 pending tables, suggest: data-platform team",
      btns: [{ label: "Assign" }],
    },
    {
      urg: "med",
      verb: "Review",
      target: "Stripe integration · 4 fields need retention policy",
      why: "Astralis · newly mapped last Thursday, retention unset",
      btns: [{ label: "Review" }],
    },
  ],
  "ai-readiness": [
    {
      urg: "high",
      verb: "Unblock",
      verbHigh: true,
      target: "resume-screener-v2 · 3 steward inputs needed",
      why: "Astralis · PIA 14/17 complete, launch review blocked",
      btns: [{ label: "Open PIA", primary: true }],
    },
    {
      urg: "high",
      verb: "Review",
      verbHigh: true,
      target: "sentiment-model-v3 · high-risk flag",
      why: "Astralis · processes EU candidates, no DPA review on file",
      btns: [{ label: "Review" }],
    },
    {
      urg: "med",
      verb: "Update",
      target: "hiring-signals · outdated data flows",
      why: "Astralis · Workday integration changed 3 weeks ago",
      btns: [{ label: "Update" }],
    },
  ],
  consent: [
    {
      urg: "high",
      verb: "Investigate",
      verbHigh: true,
      target: "DE region · opt-in dropped to 72%",
      why: "Astralis · CMP deploy Monday may have broken consent signal",
      btns: [{ label: "Investigate", primary: true }],
    },
    {
      urg: "high",
      verb: "Fix",
      verbHigh: true,
      target: "Segment integration · no consent coverage",
      why: "Astralis · ~40K users affected, same DE regional gap",
      btns: [{ label: "Fix" }],
    },
    {
      urg: "med",
      verb: "Review",
      target: "CMP config · banner shown to consented users",
      why: "Astralis · 3 anomalies, affects re-consent flow",
      btns: [{ label: "Review" }],
    },
  ],
};

// ─── Visualizations ────────────────────────────────────────────────────────

const PrivacyViz = () => {
  const heights = [20, 24, 16, 28, 22, 18, 26, 30, 24, 28, 32, 26];
  return (
    <div style={{ marginTop: "auto", paddingTop: 10, width: "100%", height: 38 }}>
      <svg
        viewBox="0 0 140 38"
        preserveAspectRatio="none"
        style={{ display: "block", width: "100%", height: "100%" }}
      >
        <g fill="rgba(32,28,24,0.15)">
          {heights.map((h, i) => (
            <rect key={i} x={i * 10} y={38 - h} width={7} height={h} />
          ))}
        </g>
        <g fill="#c8b08a">
          <rect x={120} y={4} width={7} height={34} />
          <rect x={130} y={2} width={7} height={36} />
        </g>
        <line
          x1={0}
          y1={37.5}
          x2={140}
          y2={37.5}
          stroke="rgba(32,28,24,0.08)"
          strokeWidth={1}
        />
      </svg>
    </div>
  );
};

const CoverageViz = () => (
  <div style={{ marginTop: "auto", paddingTop: 10 }}>
    <div
      style={{ display: "flex", height: 5, borderRadius: 1, overflow: "hidden" }}
    >
      <div style={{ flex: 38, background: "rgba(32,28,24,0.25)" }} />
      <div style={{ flex: 5, background: "#c8b08a" }} />
      <div style={{ flex: 4, background: "rgba(32,28,24,0.08)" }} />
    </div>
    <div style={{ display: "flex", gap: 12, marginTop: 6 }}>
      {[
        { label: "classified", color: "rgba(32,28,24,0.25)" },
        { label: "needs review", color: "#c8b08a" },
        { label: "excluded", color: "rgba(32,28,24,0.08)" },
      ].map(({ label, color }) => (
        <div
          key={label}
          style={{
            display: "flex",
            alignItems: "center",
            gap: 5,
            fontFamily: mono,
            fontSize: 8,
            color: "#8b8175",
          }}
        >
          <span
            style={{
              width: 6,
              height: 6,
              background: color,
              display: "inline-block",
            }}
          />
          {label}
        </div>
      ))}
    </div>
  </div>
);

const AiViz = () => (
  <div style={{ marginTop: "auto", paddingTop: 10, width: "100%", height: 38 }}>
    <svg
      viewBox="0 0 140 38"
      preserveAspectRatio="none"
      style={{ display: "block", width: "100%", height: "100%" }}
    >
      <polyline
        fill="none"
        stroke="rgba(32,28,24,0.2)"
        strokeWidth={1.2}
        points="0,10 14,12 28,10 42,14 56,13 70,16 84,18 98,20"
      />
      <polyline
        fill="none"
        stroke="#c8b08a"
        strokeWidth={1.4}
        points="98,20 112,22 126,24 140,26"
      />
      <circle cx={140} cy={26} r={2.5} fill="#c8b08a" />
      <line
        x1={0}
        y1={37.5}
        x2={140}
        y2={37.5}
        stroke="rgba(32,28,24,0.08)"
        strokeWidth={1}
      />
    </svg>
  </div>
);

const ConsentViz = () => {
  const bars = [
    { lbl: "US", pct: 96, val: "96%", warn: false },
    { lbl: "EU", pct: 92, val: "92%", warn: false },
    { lbl: "DE", pct: 72, val: "72%", warn: true },
    { lbl: "APAC", pct: 94, val: "94%", warn: false },
  ];
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 5,
        marginTop: "auto",
        paddingTop: 10,
      }}
    >
      {bars.map(({ lbl, pct, val, warn }) => (
        <div
          key={lbl}
          style={{
            display: "grid",
            gridTemplateColumns: "28px 1fr 28px",
            alignItems: "center",
            gap: 8,
          }}
        >
          <span
            style={{
              fontFamily: mono,
              fontSize: 8.5,
              color: "#8b8175",
              letterSpacing: "0.08em",
            }}
          >
            {lbl}
          </span>
          <div
            style={{
              height: 3,
              background: "rgba(32,28,24,0.08)",
              borderRadius: 1,
              position: "relative",
              overflow: "hidden",
            }}
          >
            <div
              style={{
                position: "absolute",
                top: 0,
                left: 0,
                bottom: 0,
                width: `${pct}%`,
                background: warn ? "#c8b08a" : "rgba(32,28,24,0.3)",
              }}
            />
          </div>
          <span
            style={{
              fontFamily: mono,
              fontSize: 8.5,
              color: warn ? "#c8b08a" : "#201c18",
              textAlign: "right",
            }}
          >
            {val}
          </span>
        </div>
      ))}
    </div>
  );
};

// ─── GPS Radar ─────────────────────────────────────────────────────────────

const GpsRadar = ({ size }: { size: number }) => {
  const cx = size / 2;
  const radii = [size / 2 - 1, size / 2 - size * 0.11, size / 2 - size * 0.27];
  return (
    <svg
      width={size}
      height={size}
      viewBox={`0 0 ${size} ${size}`}
      style={{ display: "block" }}
    >
      {radii.map((r, i) => (
        <circle
          key={i}
          cx={cx}
          cy={cx}
          r={r}
          fill="none"
          stroke="rgba(32,28,24,0.1)"
          strokeWidth={1}
        />
      ))}
      <line
        x1={cx}
        y1={1}
        x2={cx}
        y2={size - 1}
        stroke="rgba(32,28,24,0.1)"
        strokeWidth={1}
      />
      <line
        x1={1}
        y1={cx}
        x2={size - 1}
        y2={cx}
        stroke="rgba(32,28,24,0.1)"
        strokeWidth={1}
      />
    </svg>
  );
};

// ─── GPS Section ───────────────────────────────────────────────────────────

const GPS_FULL = [
  { label: "Coverage", value: "84" },
  { label: "Classification", value: "71" },
  { label: "Consent", value: "68" },
  { label: "DSR", value: "79" },
  { label: "Policy", value: "62" },
  { label: "AI readiness", value: "58" },
];

const GpsSection = ({ compressed }: { compressed: boolean }) => {
  const radarSize = compressed ? 110 : 140;
  const scoreSize = compressed ? 44 : 56;
  const rows = compressed ? GPS_FULL.slice(0, 4) : GPS_FULL;

  return (
    <motion.div layout transition={LAYOUT_TRANS} style={{ padding: "4px" }}>
      <div
        style={{
          fontFamily: mono,
          fontSize: 9,
          color: "#8b8175",
          letterSpacing: "0.2em",
          textTransform: "uppercase",
          marginBottom: 14,
        }}
      >
        Governance posture
      </div>
      <div
        style={{
          fontFamily: mono,
          fontSize: scoreSize,
          color: "#201c18",
          fontWeight: 300,
          lineHeight: 1,
          letterSpacing: "-0.02em",
          transition: "font-size 0.35s ease",
        }}
      >
        72
      </div>
      <div
        style={{
          fontFamily: mono,
          fontSize: 9.5,
          color: "#544e45",
          letterSpacing: "0.14em",
          textTransform: "uppercase",
          marginTop: 8,
        }}
      >
        Good · ↑ 2 since last week
      </div>
      <div style={{ marginTop: 18 }}>
        <GpsRadar size={radarSize} />
      </div>
      <div
        style={{
          marginTop: 16,
          display: "grid",
          gridTemplateColumns: "repeat(2, 1fr)",
          gap: "7px 18px",
        }}
      >
        {rows.map(({ label, value }) => (
          <div
            key={label}
            style={{
              display: "flex",
              justifyContent: "space-between",
              borderBottom: "1px solid rgba(32,28,24,0.06)",
              paddingBottom: 4,
            }}
          >
            <span
              style={{
                fontFamily: sans,
                fontSize: 9.5,
                color: "#8b8175",
                letterSpacing: "0.1em",
                textTransform: "uppercase",
              }}
            >
              {label}
            </span>
            <span style={{ fontFamily: mono, fontSize: 10, color: "#201c18" }}>
              {value}
            </span>
          </div>
        ))}
      </div>
    </motion.div>
  );
};

// ─── Card content: S ───────────────────────────────────────────────────────

const SContent = ({ card }: { card: CardDef }) => (
  <motion.div
    key="s"
    initial={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    exit={{ opacity: 0 }}
    transition={{ duration: 0.15 }}
    style={{
      padding: "10px 12px",
      height: "100%",
      display: "flex",
      flexDirection: "column",
      gap: 4,
    }}
  >
    <div
      style={{
        fontFamily: mono,
        fontSize: 8.5,
        color: "#8b8175",
        letterSpacing: "0.18em",
        textTransform: "uppercase",
      }}
    >
      {card.title}
    </div>
    <div
      style={{
        fontFamily: mono,
        fontSize: 18,
        color: "#201c18",
        fontWeight: 300,
        lineHeight: 1,
      }}
    >
      {card.big}
    </div>
  </motion.div>
);

// ─── Card content: M ───────────────────────────────────────────────────────

const MContent = ({ card }: { card: CardDef }) => (
  <motion.div
    key="m"
    initial={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    exit={{ opacity: 0 }}
    transition={{ duration: 0.15 }}
    style={{
      padding: "14px 16px",
      height: "100%",
      display: "flex",
      flexDirection: "column",
      gap: 8,
    }}
  >
    <div
      style={{
        fontFamily: mono,
        fontSize: 8.5,
        color: "#8b8175",
        letterSpacing: "0.18em",
        textTransform: "uppercase",
      }}
    >
      {card.title}
    </div>
    <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
      <span
        style={{
          fontFamily: mono,
          fontSize: 28,
          color: "#201c18",
          fontWeight: 300,
          lineHeight: 1,
        }}
      >
        {card.big}
      </span>
      <span
        style={{
          fontFamily: mono,
          fontSize: 9.5,
          color: card.deltaUp ? "#c8b08a" : "#8b8175",
        }}
      >
        {card.delta}
      </span>
    </div>
    <div style={{ fontFamily: sans, fontSize: 9.5, color: "#544e45" }}>
      {card.ctx}
    </div>
    {card.key === "privacy-requests" && <PrivacyViz />}
    {card.key === "system-coverage" && <CoverageViz />}
    {card.key === "ai-readiness" && <AiViz />}
    {card.key === "consent" && <ConsentViz />}
    <div
      style={{
        fontFamily: mono,
        fontSize: 9,
        letterSpacing: "0.14em",
        textTransform: "uppercase",
        color: card.calloutAmber ? "#c8b08a" : "#8b8175",
        marginTop: "auto",
        paddingTop: 8,
        borderTop: "1px solid rgba(32,28,24,0.06)",
      }}
    >
      {card.callout}
    </div>
  </motion.div>
);

// ─── Card content: L ───────────────────────────────────────────────────────

const LContent = ({ cardKey }: { cardKey: CardKey }) => {
  const card = CARDS.find((c) => c.key === cardKey)!;
  const summary = SUMMARY[cardKey];
  const actions = ACTIONS[cardKey];

  return (
    <motion.div
      key="l"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.15 }}
      style={{
        padding: "14px 18px",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
      }}
    >
      {/* Title */}
      <div
        style={{
          fontFamily: mono,
          fontSize: 9,
          color: "#8b8175",
          letterSpacing: "0.18em",
          textTransform: "uppercase",
          marginBottom: 12,
        }}
      >
        {card.title} · {card.big} · {actions.length} actions
      </div>

      {/* Summary strip */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(4, 1fr)",
          gap: "8px 12px",
          paddingBottom: 12,
          borderBottom: "1px solid rgba(32,28,24,0.08)",
        }}
      >
        {summary.map((cell) => (
          <div key={cell.k} style={{ minWidth: 0, overflow: "hidden" }}>
            <div
              style={{
                fontFamily: sans,
                fontSize: 8,
                color: "#8b8175",
                letterSpacing: "0.12em",
                textTransform: "uppercase",
                whiteSpace: "nowrap",
                overflow: "hidden",
                textOverflow: "ellipsis",
              }}
            >
              {cell.k}
            </div>
            <span
              style={{
                fontFamily: mono,
                color: "#201c18",
                fontSize: 18,
                fontWeight: 300,
                display: "block",
                marginTop: 3,
              }}
            >
              {cell.n}
            </span>
            {cell.delta && (
              <span
                style={{
                  fontFamily: sans,
                  fontSize: 8.5,
                  color: cell.deltaUp ? "#c8b08a" : "#8b8175",
                  display: "block",
                  marginTop: 2,
                }}
              >
                {cell.delta}
              </span>
            )}
          </div>
        ))}
      </div>

      {/* Queue header */}
      <div
        style={{
          display: "flex",
          alignItems: "baseline",
          justifyContent: "space-between",
          fontFamily: mono,
          fontSize: 8.5,
          letterSpacing: "0.22em",
          textTransform: "uppercase",
          color: "#8b8175",
          padding: "8px 0 6px",
          borderBottom: "1px solid rgba(32,28,24,0.08)",
        }}
      >
        <span>Action queue</span>
        <span style={{ color: "#c8b08a", letterSpacing: "normal", fontSize: 10 }}>
          {actions.length}
        </span>
      </div>

      {/* Action rows */}
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          display: "flex",
          flexDirection: "column",
        }}
      >
        {actions.map((action, i) => (
          <div
            key={i}
            style={{
              display: "grid",
              gridTemplateColumns: "8px 1fr auto",
              columnGap: 10,
              alignItems: "start",
              padding: i === 0 ? "7px 8px" : "7px 0",
              margin: i === 0 ? "2px 0" : "0",
              borderBottom:
                i < actions.length - 1 && i !== 0
                  ? "1px solid rgba(32,28,24,0.06)"
                  : "none",
              borderRadius: i === 0 ? 3 : 0,
              ...(i === 0
                ? {
                    boxShadow:
                      "inset 0 0 0 1px rgba(200,176,138,0.32), 0 0 14px rgba(200,176,138,0.08)",
                    background: "rgba(200,176,138,0.03)",
                  }
                : {}),
            }}
          >
            <div
              style={{
                width: 6,
                height: 6,
                borderRadius: "50%",
                background: urgColor(action.urg),
                boxShadow:
                  action.urg === "high"
                    ? "0 0 0 2px rgba(200,176,138,0.1)"
                    : "none",
                marginTop: 5,
                justifySelf: "center",
              }}
            />
            <div style={{ minWidth: 0 }}>
              <div
                style={{
                  fontFamily: sans,
                  fontSize: 10,
                  color: "#201c18",
                  lineHeight: 1.4,
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                }}
              >
                <span
                  style={{
                    display: "inline-block",
                    fontFamily: mono,
                    fontSize: 8,
                    letterSpacing: "0.12em",
                    textTransform: "uppercase",
                    padding: "2px 6px",
                    border: action.verbHigh
                      ? "1px solid rgba(200,176,138,0.5)"
                      : "1px solid rgba(32,28,24,0.12)",
                    borderRadius: 2,
                    marginRight: 8,
                    color: action.verbHigh ? "#c8b08a" : "#201c18",
                    background: action.verbHigh
                      ? "rgba(200,176,138,0.04)"
                      : "transparent",
                    verticalAlign: "1px",
                  }}
                >
                  {action.verb}
                </span>
                {action.target}
              </div>
              <div
                style={{
                  fontFamily: sans,
                  fontSize: 9,
                  color: "#8b8175",
                  marginTop: 2,
                  lineHeight: 1.35,
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                }}
              >
                <span style={{ color: "#544e45", fontStyle: "italic" }}>
                  Astralis ·{" "}
                </span>
                {action.why.replace("Astralis · ", "")}
              </div>
            </div>
            <div
              style={{ display: "flex", gap: 4, flexShrink: 0, paddingTop: 1 }}
            >
              {action.btns.map((btn) => (
                <button
                  key={btn.label}
                  type="button"
                  onClick={(e) => e.stopPropagation()}
                  style={{
                    border: btn.primary
                      ? "1px solid rgba(200,176,138,0.5)"
                      : "1px solid rgba(32,28,24,0.12)",
                    background: btn.primary
                      ? "rgba(200,176,138,0.06)"
                      : "rgba(255,255,255,0.4)",
                    color: btn.primary ? "#c8b08a" : "#544e45",
                    padding: "4px 8px",
                    fontSize: 8,
                    letterSpacing: "0.12em",
                    textTransform: "uppercase",
                    borderRadius: 2,
                    fontFamily: mono,
                    cursor: "pointer",
                    whiteSpace: "nowrap",
                  }}
                >
                  {btn.label}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </motion.div>
  );
};

// ─── Pillar Card ───────────────────────────────────────────────────────────

const PillarCard = ({
  card,
  state,
  onToggle,
}: {
  card: CardDef;
  state: "s" | "m" | "l";
  onToggle: () => void;
}) => {
  const isL = state === "l";
  const isGlowing = state === "m" && card.glow;
  const { border, boxShadow } = isGlowing ? glassGlow : glass;

  return (
    <motion.div
      layout
      layoutId={card.key}
      transition={LAYOUT_TRANS}
      onClick={onToggle}
      style={{
        gridColumn: isL ? "span 4" : undefined,
        cursor: "pointer",
        background: "rgba(255,255,255,0.55)",
        backdropFilter: "blur(14px)",
        WebkitBackdropFilter: "blur(14px)",
        border,
        boxShadow,
        borderRadius: 2,
        overflow: "hidden" as const,
        display: "flex",
        flexDirection: "column" as const,
      }}
    >
      <AnimatePresence mode="wait">
        {isL ? (
          <LContent cardKey={card.key} />
        ) : state === "s" ? (
          <SContent card={card} />
        ) : (
          <MContent card={card} />
        )}
      </AnimatePresence>
    </motion.div>
  );
};

// ─── Activity Log ──────────────────────────────────────────────────────────

const EVENTS = [
  { text: "Helios classified 847 fields", time: "2m ago" },
  { text: "DSR-4521 completed", time: "5m ago" },
  { text: "Astralis proposed PIA", time: "9m ago" },
  { text: "Classification batch approved", time: "14m ago" },
  { text: "New BigQuery dataset detected", time: "22m ago" },
  { text: "Consent anomaly · DE region", time: "34m ago" },
  { text: "Janus monitor recovered", time: "47m ago" },
];

const ActivityLog = () => (
  <div
    style={{
      position: "absolute",
      top: 0,
      right: 0,
      bottom: 80,
      width: 168,
      borderLeft: "1px solid rgba(32,28,24,0.08)",
      padding: "22px 14px",
      display: "flex",
      flexDirection: "column",
      gap: 14,
    }}
  >
    <div
      style={{
        fontFamily: sans,
        fontSize: 8.5,
        color: "#8b8175",
        letterSpacing: "0.18em",
        textTransform: "uppercase",
        marginBottom: 4,
      }}
    >
      Activity
    </div>
    {EVENTS.map((ev) => (
      <div
        key={ev.text}
        style={{
          borderLeft: "1px solid rgba(32,28,24,0.1)",
          paddingLeft: 9,
          lineHeight: 1.5,
        }}
      >
        <div style={{ fontFamily: sans, fontSize: 9, color: "#544e45" }}>
          {ev.text}
        </div>
        <div
          style={{ fontFamily: mono, fontSize: 8, color: "#8b8175", marginTop: 2 }}
        >
          {ev.time}
        </div>
      </div>
    ))}
  </div>
);

// ─── Dashboard Grid ────────────────────────────────────────────────────────

const DashboardGrid = ({
  expanded,
  setExpanded,
}: {
  expanded: string | null;
  setExpanded: (key: string | null) => void;
}) => {
  const isExpanded = expanded !== null;

  const getState = (key: string): "s" | "m" | "l" => {
    if (!isExpanded) return "m";
    return expanded === key ? "l" : "s";
  };

  const handleToggle = (key: string) => {
    setExpanded(expanded === key ? null : key);
  };

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        padding: "28px 216px 108px 52px",
        display: "grid",
        gridTemplateColumns: "5fr 8fr",
        gap: 28,
      }}
    >
      {/* GPS */}
      <div style={{ overflow: "hidden" }}>
        <GpsSection compressed={isExpanded} />
      </div>

      {/* Card grid */}
      <motion.div
        layout
        transition={LAYOUT_TRANS}
        style={{
          display: "grid",
          gridTemplateColumns: isExpanded ? "repeat(4, 1fr)" : "1fr 1fr",
          gridTemplateRows: isExpanded ? "auto 1fr" : "1fr 1fr",
          gap: 10,
          alignContent: isExpanded ? "start" : "stretch",
        }}
      >
        {CARDS.map((card) => (
          <PillarCard
            key={card.key}
            card={card}
            state={getState(card.key)}
            onToggle={() => handleToggle(card.key)}
          />
        ))}
      </motion.div>

      {/* Activity log */}
      <ActivityLog />
    </div>
  );
};

export default DashboardGrid;
