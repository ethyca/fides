import { useState, useEffect, useRef, useCallback } from "react";

// ─── Data ────────────────────────────────────────────────────────────────────
const DIMENSIONS = [
  { key: "coverage", label: "Coverage", weight: 0.20, score: 72, icon: "🗂", area: "/systems", color: "#6366f1" },
  { key: "classification", label: "Classification Health", weight: 0.15, score: 85, icon: "🏷", area: "/datasets", color: "#8b5cf6" },
  { key: "consent", label: "Consent Alignment", weight: 0.15, score: 58, icon: "✋", area: "/consent", color: "#a78bfa" },
  { key: "dsr", label: "DSR Compliance", weight: 0.15, score: 44, icon: "📋", area: "/dsr", color: "#c084fc" },
  { key: "policy", label: "Policy Enforcement", weight: 0.15, score: 67, icon: "🛡", area: "/policies", color: "#7c3aed" },
  { key: "ai", label: "AI Readiness", weight: 0.10, score: 31, icon: "🤖", area: "/ai", color: "#4f46e5" },
  { key: "assessment", label: "Assessment Coverage", weight: 0.10, score: 76, icon: "📝", area: "/assessments", color: "#818cf8" },
];

const TREND_DATA = [62, 59, 61, 63, 60, 64, 65, 63, 67, 66, 68, 65];
const COMPOSITE = Math.round(DIMENSIONS.reduce((s, d) => s + d.score * d.weight, 0));

const bandFor = (s) =>
  s >= 80 ? { label: "Excellent", bg: "bg-emerald-500", text: "text-emerald-400", ring: "#10b981", grad: ["#059669","#10b981"] }
  : s >= 60 ? { label: "Good", bg: "bg-blue-500", text: "text-blue-400", ring: "#3b82f6", grad: ["#2563eb","#3b82f6"] }
  : s >= 40 ? { label: "At Risk", bg: "bg-amber-500", text: "text-amber-400", ring: "#f59e0b", grad: ["#d97706","#f59e0b"] }
  : { label: "Critical", bg: "bg-red-500", text: "text-red-400", ring: "#ef4444", grad: ["#dc2626","#ef4444"] };

const NARRATIVE = "Classification Health improved +8 pts after last week's scan. Consent Alignment dropped — 12 processing activities now lack matching consent records.";

// ─── Animated Number ─────────────────────────────────────────────────────────
function AnimatedNumber({ value, duration = 1400 }) {
  const [display, setDisplay] = useState(0);
  useEffect(() => {
    let start = null;
    const step = (ts) => {
      if (!start) start = ts;
      const p = Math.min((ts - start) / duration, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      setDisplay(Math.round(eased * value));
      if (p < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }, [value, duration]);
  return <>{display}</>;
}

// ─── Sparkline ───────────────────────────────────────────────────────────────
function Sparkline({ data, width = 160, height = 40, color = "#3b82f6" }) {
  const min = Math.min(...data) - 2;
  const max = Math.max(...data) + 2;
  const points = data.map((v, i) => {
    const x = (i / (data.length - 1)) * width;
    const y = height - ((v - min) / (max - min)) * height;
    return `${x},${y}`;
  }).join(" ");
  const last = data[data.length - 1];
  const prev = data[data.length - 2];
  const delta = last - prev;
  return (
    <div className="flex items-center gap-2">
      <svg width={width} height={height} className="overflow-visible">
        <defs>
          <linearGradient id="sparkGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="0.3" />
            <stop offset="100%" stopColor={color} stopOpacity="0" />
          </linearGradient>
        </defs>
        <polyline fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" points={points} />
        <polygon
          fill="url(#sparkGrad)"
          points={`0,${height} ${points} ${width},${height}`}
        />
      </svg>
      <span className={`text-sm font-semibold ${delta >= 0 ? "text-emerald-400" : "text-red-400"}`}>
        {delta >= 0 ? "↑" : "↓"} {Math.abs(delta)}
      </span>
    </div>
  );
}

// ─── Dimension Ring (SVG donut) ──────────────────────────────────────────────
function DimensionRing({ dimensions, size = 280, thickness = 28, hovered, onHover }) {
  const radius = (size - thickness) / 2;
  const circumference = 2 * Math.PI * radius;
  const gap = 4;
  const totalGap = gap * dimensions.length;
  const usable = circumference - totalGap;

  let offset = 0;
  const segments = dimensions.map((d) => {
    const len = usable * d.weight;
    const seg = { ...d, offset, len, band: bandFor(d.score) };
    offset += len + gap;
    return seg;
  });

  return (
    <svg width={size} height={size} className="drop-shadow-lg" style={{ filter: "drop-shadow(0 0 24px rgba(99,102,241,0.15))" }}>
      {segments.map((s) => {
        const isHovered = hovered === s.key;
        return (
          <circle
            key={s.key}
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={s.band.ring}
            strokeWidth={isHovered ? thickness + 6 : thickness}
            strokeDasharray={`${s.len} ${circumference - s.len}`}
            strokeDashoffset={-s.offset}
            strokeLinecap="round"
            opacity={hovered && !isHovered ? 0.3 : 1}
            style={{ transition: "all 0.3s ease", cursor: "pointer", transformOrigin: "center" }}
            onMouseEnter={() => onHover(s.key)}
            onMouseLeave={() => onHover(null)}
          />
        );
      })}
    </svg>
  );
}

// ─── Horizontal Bar Gauge ────────────────────────────────────────────────────
function BarGauge({ dimension, expanded, onToggle }) {
  const band = bandFor(dimension.score);
  return (
    <div
      className="group cursor-pointer"
      onClick={onToggle}
    >
      <div className="flex items-center justify-between mb-1">
        <span className="text-sm text-gray-300 flex items-center gap-1.5">
          <span>{dimension.icon}</span>
          <span>{dimension.label}</span>
          <span className="text-xs text-gray-500">({Math.round(dimension.weight * 100)}%)</span>
        </span>
        <span className={`text-sm font-bold ${band.text}`}>{dimension.score}</span>
      </div>
      <div className="w-full h-2 bg-gray-800 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700 ease-out"
          style={{
            width: `${dimension.score}%`,
            background: `linear-gradient(90deg, ${band.grad[0]}, ${band.grad[1]})`,
          }}
        />
      </div>
      {expanded && (
        <div className="mt-2 ml-6 text-xs text-gray-400 space-y-1 animate-fadeIn">
          <div>→ Signals contributing to this score are tracked in real-time</div>
          <a href="#" className="text-indigo-400 hover:text-indigo-300 underline">
            Take action in {dimension.label} →
          </a>
        </div>
      )}
    </div>
  );
}

// ─── Petal / Radar Hybrid ────────────────────────────────────────────────────
function PetalChart({ dimensions, size = 260, hovered, onHover }) {
  const cx = size / 2, cy = size / 2;
  const maxR = size / 2 - 20;
  const n = dimensions.length;

  return (
    <svg width={size} height={size} className="drop-shadow-lg">
      {/* Grid circles */}
      {[0.25, 0.5, 0.75, 1].map((f) => (
        <circle key={f} cx={cx} cy={cy} r={maxR * f} fill="none" stroke="#374151" strokeWidth="1" strokeDasharray="2,4" />
      ))}
      {/* Petals */}
      {dimensions.map((d, i) => {
        const angle1 = (2 * Math.PI * i) / n - Math.PI / 2;
        const angle2 = (2 * Math.PI * (i + 1)) / n - Math.PI / 2;
        const angleMid = (angle1 + angle2) / 2;
        const r = maxR * (d.score / 100);
        const band = bandFor(d.score);
        const isHovered = hovered === d.key;

        const x1 = cx + r * Math.cos(angle1) * 0.6;
        const y1 = cy + r * Math.sin(angle1) * 0.6;
        const xm = cx + r * Math.cos(angleMid);
        const ym = cy + r * Math.sin(angleMid);
        const x2 = cx + r * Math.cos(angle2) * 0.6;
        const y2 = cy + r * Math.sin(angle2) * 0.6;

        const labelR = maxR + 12;
        const lx = cx + labelR * Math.cos(angleMid);
        const ly = cy + labelR * Math.sin(angleMid);

        return (
          <g key={d.key} style={{ cursor: "pointer" }} onMouseEnter={() => onHover(d.key)} onMouseLeave={() => onHover(null)}>
            <path
              d={`M ${cx} ${cy} Q ${x1} ${y1} ${xm} ${ym} Q ${x2} ${y2} ${cx} ${cy}`}
              fill={band.ring}
              fillOpacity={isHovered ? 0.5 : 0.25}
              stroke={band.ring}
              strokeWidth={isHovered ? 2 : 1}
              style={{ transition: "all 0.3s ease" }}
            />
            <text x={lx} y={ly} textAnchor="middle" dominantBaseline="middle" fill="#9ca3af" fontSize="9">
              {d.icon}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

// ─── Honeycomb / Hex Grid ────────────────────────────────────────────────────
function HexCell({ cx, cy, size, dimension, isHovered, onHover }) {
  const band = bandFor(dimension.score);
  const points = Array.from({ length: 6 }, (_, i) => {
    const angle = (Math.PI / 3) * i - Math.PI / 6;
    return `${cx + size * Math.cos(angle)},${cy + size * Math.sin(angle)}`;
  }).join(" ");

  const innerSize = size * (dimension.score / 100) * 0.85;
  const innerPoints = Array.from({ length: 6 }, (_, i) => {
    const angle = (Math.PI / 3) * i - Math.PI / 6;
    return `${cx + innerSize * Math.cos(angle)},${cy + innerSize * Math.sin(angle)}`;
  }).join(" ");

  return (
    <g style={{ cursor: "pointer" }} onMouseEnter={() => onHover(dimension.key)} onMouseLeave={() => onHover(null)}>
      <polygon points={points} fill="#1f2937" stroke="#374151" strokeWidth="1.5" />
      <polygon
        points={innerPoints}
        fill={band.ring}
        fillOpacity={isHovered ? 0.6 : 0.3}
        stroke={band.ring}
        strokeWidth={isHovered ? 2 : 1}
        style={{ transition: "all 0.3s ease" }}
      />
      <text x={cx} y={cy - 6} textAnchor="middle" fill="white" fontSize="14" fontWeight="bold">{dimension.score}</text>
      <text x={cx} y={cy + 10} textAnchor="middle" fill="#9ca3af" fontSize="8">{dimension.icon} {dimension.label.split(" ")[0]}</text>
    </g>
  );
}

function HexGrid({ dimensions, hovered, onHover }) {
  const hexSize = 48;
  const w = hexSize * Math.sqrt(3);
  const h = hexSize * 2;
  // Layout: row 0 has 3, row 1 has 4 (shifted)
  const positions = [
    // top row
    { x: 160, y: 60 }, { x: 160 + w, y: 60 }, { x: 160 + w * 2, y: 60 },
    // bottom row (shifted)
    { x: 160 - w / 2, y: 60 + h * 0.75 }, { x: 160 + w / 2, y: 60 + h * 0.75 },
    { x: 160 + w * 1.5, y: 60 + h * 0.75 }, { x: 160 + w * 2.5, y: 60 + h * 0.75 },
  ];

  return (
    <svg width={480} height={200} className="drop-shadow-lg">
      {dimensions.map((d, i) => (
        <HexCell key={d.key} cx={positions[i].x} cy={positions[i].y} size={hexSize} dimension={d} isHovered={hovered === d.key} onHover={onHover} />
      ))}
    </svg>
  );
}

// ─── Arc Gauge (speedometer style) ───────────────────────────────────────────
function ArcGauge({ score, size = 240 }) {
  const band = bandFor(score);
  const cx = size / 2, cy = size / 2 + 20;
  const r = size / 2 - 30;
  const startAngle = Math.PI * 0.8;
  const endAngle = Math.PI * 0.2;
  const totalArc = 2 * Math.PI - (startAngle - endAngle);

  const arcPath = (startA, endA) => {
    const x1 = cx + r * Math.cos(startA);
    const y1 = cy - r * Math.sin(startA);
    const x2 = cx + r * Math.cos(endA);
    const y2 = cy - r * Math.sin(endA);
    const sweep = endA < startA ? 1 : 0;
    return `M ${x1} ${y1} A ${r} ${r} 0 1 ${sweep} ${x2} ${y2}`;
  };

  const progress = score / 100;
  const progressAngle = startAngle - totalArc * progress;

  // Needle
  const needleAngle = startAngle - totalArc * progress;
  const needleLen = r - 10;
  const nx = cx + needleLen * Math.cos(needleAngle);
  const ny = cy - needleLen * Math.sin(needleAngle);

  return (
    <svg width={size} height={size - 20} className="drop-shadow-lg">
      {/* Background arc */}
      <path d={arcPath(startAngle, endAngle)} fill="none" stroke="#1f2937" strokeWidth="20" strokeLinecap="round" />
      {/* Band markers */}
      {[
        { pct: 0.39, color: "#ef4444" },
        { pct: 0.59, color: "#f59e0b" },
        { pct: 0.79, color: "#3b82f6" },
        { pct: 1.0, color: "#10b981" },
      ].map((b, i, arr) => {
        const from = i === 0 ? 0 : arr[i - 1].pct;
        const sa = startAngle - totalArc * from;
        const ea = startAngle - totalArc * b.pct;
        const x1 = cx + r * Math.cos(sa);
        const y1 = cy - r * Math.sin(sa);
        const x2 = cx + r * Math.cos(ea);
        const y2 = cy - r * Math.sin(ea);
        return (
          <path
            key={i}
            d={`M ${x1} ${y1} A ${r} ${r} 0 0 0 ${x2} ${y2}`}
            fill="none"
            stroke={b.color}
            strokeWidth="20"
            strokeLinecap="butt"
            opacity="0.2"
          />
        );
      })}
      {/* Progress arc */}
      <path
        d={(() => {
          const x1 = cx + r * Math.cos(startAngle);
          const y1 = cy - r * Math.sin(startAngle);
          const x2 = cx + r * Math.cos(progressAngle);
          const y2 = cy - r * Math.sin(progressAngle);
          const large = progress > 0.5 ? 1 : 0;
          return `M ${x1} ${y1} A ${r} ${r} 0 ${large} 0 ${x2} ${y2}`;
        })()}
        fill="none"
        stroke={band.ring}
        strokeWidth="20"
        strokeLinecap="round"
      />
      {/* Needle */}
      <line x1={cx} y1={cy} x2={nx} y2={ny} stroke="white" strokeWidth="2.5" strokeLinecap="round" />
      <circle cx={cx} cy={cy} r="6" fill="#111827" stroke="white" strokeWidth="2" />
    </svg>
  );
}

// ─── Breakdown Panel ─────────────────────────────────────────────────────────
function BreakdownPanel({ dimension, onClose }) {
  if (!dimension) return null;
  const band = bandFor(dimension.score);
  const signals = {
    coverage: ["78% of known systems connected", "62% of datasets classified", "14 systems with no steward"],
    classification: ["3 unreviewed classifications", "Last scan: 2 days ago", "5 low-confidence labels"],
    consent: ["12 consent-to-processing gaps", "2 monitoring failures", "Opt-out rate ↑ 8%"],
    dsr: ["3 overdue DSRs", "7 pending manual steps", "2 approaching SLA breach"],
    policy: ["9 systems with no policy", "4 violations detected", "2 unresolved"],
    ai: ["Per-system checklist: 31% complete", "De-ID strategy missing on 12 systems", "3 PIAs incomplete"],
    assessment: ["5 activities without PIAs", "2 overdue assessments", "1 awaiting response"],
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-gray-900 border border-gray-700 rounded-2xl p-6 max-w-md w-full mx-4 shadow-2xl" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <span>{dimension.icon}</span> {dimension.label}
          </h3>
          <button onClick={onClose} className="text-gray-400 hover:text-white text-xl">×</button>
        </div>
        <div className="flex items-center gap-3 mb-4">
          <span className={`text-4xl font-black ${band.text}`}>{dimension.score}</span>
          <span className={`text-xs px-2 py-1 rounded-full ${band.bg} text-white font-medium`}>{band.label}</span>
          <span className="text-xs text-gray-500">Weight: {Math.round(dimension.weight * 100)}%</span>
        </div>
        <div className="space-y-2 mb-4">
          <p className="text-xs text-gray-500 uppercase tracking-wider font-semibold">Contributing Signals</p>
          {(signals[dimension.key] || []).map((s, i) => (
            <div key={i} className="text-sm text-gray-300 flex items-start gap-2">
              <span className="text-gray-600 mt-0.5">•</span> {s}
            </div>
          ))}
        </div>
        <a href="#" className="inline-flex items-center gap-1 text-sm text-indigo-400 hover:text-indigo-300 font-medium">
          Take action → Go to {dimension.label}
        </a>
      </div>
    </div>
  );
}

// ─── Layout Options ──────────────────────────────────────────────────────────
const LAYOUTS = [
  { key: "ring", label: "Dimension Ring", desc: "Segmented donut — weight = arc length, color = health band" },
  { key: "petal", label: "Petal Radar", desc: "Organic radar — each petal's reach = score, angle = weight" },
  { key: "hex", label: "Hex Grid", desc: "Honeycomb cells — filled area = score, scannable at a glance" },
  { key: "gauge", label: "Arc Gauge", desc: "Speedometer — needle + colored bands, classic exec dashboard" },
];

// ─── Main Component ──────────────────────────────────────────────────────────
export default function GPSScoreViz() {
  const [layout, setLayout] = useState("ring");
  const [hovered, setHovered] = useState(null);
  const [expandedDim, setExpandedDim] = useState(null);
  const [breakdownDim, setBreakdownDim] = useState(null);
  const band = bandFor(COMPOSITE);

  const hoveredDim = DIMENSIONS.find((d) => d.key === hovered);

  return (
    <div className="min-h-screen bg-gray-950 text-white p-6">
      <style>{`
        @keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }
        .animate-fadeIn { animation: fadeIn 0.3s ease-out; }
        @keyframes pulse-glow { 0%, 100% { box-shadow: 0 0 20px rgba(99,102,241,0.15); } 50% { box-shadow: 0 0 40px rgba(99,102,241,0.3); } }
      `}</style>

      {/* Header */}
      <div className="max-w-5xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-white mb-1">Governance Posture Score</h1>
          <p className="text-sm text-gray-500">Composite health metric across 7 governance dimensions</p>
        </div>

        {/* Layout Switcher */}
        <div className="flex flex-wrap gap-2 mb-8">
          {LAYOUTS.map((l) => (
            <button
              key={l.key}
              onClick={() => setLayout(l.key)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                layout === l.key
                  ? "bg-indigo-600 text-white"
                  : "bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-gray-200"
              }`}
            >
              {l.label}
            </button>
          ))}
        </div>

        <p className="text-xs text-gray-600 mb-6 italic">{LAYOUTS.find((l) => l.key === layout)?.desc}</p>

        {/* Main Score Area */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Left: Visualization */}
          <div className="flex flex-col items-center justify-center">
            <div className="relative flex items-center justify-center">
              {layout === "ring" && (
                <>
                  <DimensionRing dimensions={DIMENSIONS} hovered={hovered} onHover={setHovered} />
                  {/* Center score */}
                  <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                    <div className={`text-6xl font-black ${band.text}`}>
                      <AnimatedNumber value={COMPOSITE} />
                    </div>
                    <div className={`text-xs font-semibold px-2 py-0.5 rounded-full ${band.bg} text-white mt-1`}>
                      {band.label}
                    </div>
                  </div>
                </>
              )}

              {layout === "petal" && (
                <>
                  <PetalChart dimensions={DIMENSIONS} hovered={hovered} onHover={setHovered} />
                  <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                    <div className={`text-5xl font-black ${band.text}`}>
                      <AnimatedNumber value={COMPOSITE} />
                    </div>
                    <div className={`text-xs font-semibold px-2 py-0.5 rounded-full ${band.bg} text-white mt-1`}>
                      {band.label}
                    </div>
                  </div>
                </>
              )}

              {layout === "gauge" && (
                <div className="flex flex-col items-center">
                  <ArcGauge score={COMPOSITE} />
                  <div className="-mt-16 flex flex-col items-center">
                    <div className={`text-5xl font-black ${band.text}`}>
                      <AnimatedNumber value={COMPOSITE} />
                    </div>
                    <div className={`text-xs font-semibold px-2 py-0.5 rounded-full ${band.bg} text-white mt-1`}>
                      {band.label}
                    </div>
                  </div>
                </div>
              )}

              {layout === "hex" && (
                <div className="flex flex-col items-center gap-4">
                  <div className="flex items-center gap-3">
                    <span className={`text-5xl font-black ${band.text}`}>
                      <AnimatedNumber value={COMPOSITE} />
                    </span>
                    <div>
                      <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${band.bg} text-white`}>
                        {band.label}
                      </span>
                    </div>
                  </div>
                  <HexGrid dimensions={DIMENSIONS} hovered={hovered} onHover={setHovered} />
                </div>
              )}
            </div>

            {/* Hover tooltip */}
            <div className="h-12 mt-4 flex items-center">
              {hoveredDim ? (
                <div className="text-center animate-fadeIn">
                  <span className="text-sm font-medium text-white">{hoveredDim.icon} {hoveredDim.label}</span>
                  <span className={`ml-2 text-sm font-bold ${bandFor(hoveredDim.score).text}`}>{hoveredDim.score}</span>
                  <span className="ml-2 text-xs text-gray-500">({Math.round(hoveredDim.weight * 100)}% weight)</span>
                </div>
              ) : (
                <span className="text-xs text-gray-600">Hover a segment to inspect</span>
              )}
            </div>

            {/* Trend */}
            <div className="mt-2 flex flex-col items-center gap-2">
              <Sparkline data={TREND_DATA} color={band.ring} />
              <p className="text-xs text-gray-500 max-w-xs text-center leading-relaxed">{NARRATIVE}</p>
            </div>
          </div>

          {/* Right: Dimension Breakdown */}
          <div className="space-y-3">
            <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">Dimensions</h2>
            {DIMENSIONS.map((d) => (
              <div
                key={d.key}
                onMouseEnter={() => setHovered(d.key)}
                onMouseLeave={() => setHovered(null)}
                onClick={() => setBreakdownDim(d)}
                className={`p-3 rounded-xl transition-all cursor-pointer ${
                  hovered === d.key ? "bg-gray-800/80 ring-1 ring-gray-700" : "bg-transparent hover:bg-gray-900"
                }`}
              >
                <BarGauge
                  dimension={d}
                  expanded={expandedDim === d.key}
                  onToggle={() => setExpandedDim(expandedDim === d.key ? null : d.key)}
                />
              </div>
            ))}

            {/* Band Legend */}
            <div className="flex gap-3 mt-4 pt-4 border-t border-gray-800">
              {[
                { label: "Critical", range: "0–39", color: "bg-red-500" },
                { label: "At Risk", range: "40–59", color: "bg-amber-500" },
                { label: "Good", range: "60–79", color: "bg-blue-500" },
                { label: "Excellent", range: "80–100", color: "bg-emerald-500" },
              ].map((b) => (
                <div key={b.label} className="flex items-center gap-1.5 text-xs text-gray-500">
                  <div className={`w-2 h-2 rounded-full ${b.color}`} />
                  {b.label} <span className="text-gray-700">{b.range}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Breakdown modal */}
      <BreakdownPanel dimension={breakdownDim} onClose={() => setBreakdownDim(null)} />
    </div>
  );
}