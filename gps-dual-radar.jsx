import { useState, useEffect, useMemo } from "react";
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

// ─── Data ────────────────────────────────────────────────────────────────────
const DIMENSIONS = [
  { key: "coverage", label: "Coverage", shortLabel: "COV", weight: 20, score: 72, icon: "🗂" },
  { key: "classification", label: "Classification", shortLabel: "CLS", weight: 15, score: 85, icon: "🏷" },
  { key: "consent", label: "Consent", shortLabel: "CNS", weight: 15, score: 58, icon: "✋" },
  { key: "dsr", label: "DSR", shortLabel: "DSR", weight: 15, score: 44, icon: "📋" },
  { key: "policy", label: "Policy", shortLabel: "POL", weight: 15, score: 67, icon: "🛡" },
  { key: "ai", label: "AI Ready", shortLabel: "AI", weight: 10, score: 31, icon: "🤖" },
  { key: "assessment", label: "Assess.", shortLabel: "PIA", weight: 10, score: 76, icon: "📝" },
];

const COMPOSITE = Math.round(DIMENSIONS.reduce((s, d) => s + d.score * (d.weight / 100), 0));

const bandFor = (s) =>
  s >= 80 ? { label: "Excellent", color: "#10b981", bg: "bg-emerald-500", text: "text-emerald-400" }
  : s >= 60 ? { label: "Good", color: "#3b82f6", bg: "bg-blue-500", text: "text-blue-400" }
  : s >= 40 ? { label: "At Risk", color: "#f59e0b", bg: "bg-amber-500", text: "text-amber-400" }
  : { label: "Critical", color: "#ef4444", bg: "bg-red-500", text: "text-red-400" };

// ─── Animated number ─────────────────────────────────────────────────────────
function AnimatedNumber({ value, duration = 1200 }) {
  const [display, setDisplay] = useState(0);
  useEffect(() => {
    let start = null;
    const step = (ts) => {
      if (!start) start = ts;
      const p = Math.min((ts - start) / duration, 1);
      setDisplay(Math.round((1 - Math.pow(1 - p, 3)) * value));
      if (p < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }, [value, duration]);
  return <>{display}</>;
}

// ─── Custom rounded radar shape ──────────────────────────────────────────────
// Attempt to create a smoothed version via catmull-rom → cubic bezier
function RoundedRadarShape({ points, fillColor, fillOpacity, strokeColor, strokeWidth = 2 }) {
  if (!points || points.length < 3) return null;

  // Close the loop by wrapping around
  const pts = [...points, points[0], points[1]];

  // Catmull-Rom to cubic Bézier conversion
  const tension = 0.35;
  let d = `M ${points[0].x} ${points[0].y}`;

  for (let i = 0; i < points.length; i++) {
    const p0 = pts[i];
    const p1 = pts[i + 1];
    const p2 = pts[i + 2];
    const pPrev = i === 0 ? pts[pts.length - 3] : pts[i - 1]; // wrap around

    const cp1x = p0.x + (p1.x - pPrev.x) * tension;
    const cp1y = p0.y + (p1.y - pPrev.y) * tension;
    const cp2x = p1.x - (p2.x - p0.x) * tension;
    const cp2y = p1.y - (p2.y - p0.y) * tension;

    d += ` C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${p1.x} ${p1.y}`;
  }

  return (
    <path
      d={d}
      fill={fillColor}
      fillOpacity={fillOpacity}
      stroke={strokeColor}
      strokeWidth={strokeWidth}
      strokeLinejoin="round"
    />
  );
}

// ─── Custom axis tick ────────────────────────────────────────────────────────
function CustomTick({ payload, x, y, cx, cy, hoveredKey, onHover }) {
  const dim = DIMENSIONS.find((d) => d.shortLabel === payload.value);
  if (!dim) return null;
  const band = bandFor(dim.score);
  const isHovered = hoveredKey === dim.key;

  // Push label outward
  const dx = x - cx;
  const dy = y - cy;
  const dist = Math.sqrt(dx * dx + dy * dy);
  const nudge = 18;
  const nx = x + (dx / dist) * nudge;
  const ny = y + (dy / dist) * nudge;

  return (
    <g
      style={{ cursor: "pointer" }}
      onMouseEnter={() => onHover(dim.key)}
      onMouseLeave={() => onHover(null)}
    >
      <text
        x={nx}
        y={ny - 7}
        textAnchor="middle"
        fill={isHovered ? "white" : "#9ca3af"}
        fontSize={11}
        fontWeight={isHovered ? 700 : 500}
        style={{ transition: "all 0.2s" }}
      >
        {dim.icon} {dim.shortLabel}
      </text>
      <text
        x={nx}
        y={ny + 8}
        textAnchor="middle"
        fill={isHovered ? band.color : "#6b7280"}
        fontSize={10}
        fontWeight={600}
        style={{ transition: "all 0.2s" }}
      >
        {dim.score}
      </text>
    </g>
  );
}

// ─── Custom tooltip ──────────────────────────────────────────────────────────
function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  const dim = DIMENSIONS.find((d) => d.shortLabel === label);
  if (!dim) return null;
  const band = bandFor(dim.score);

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl px-4 py-3 shadow-xl">
      <div className="text-sm font-semibold text-white mb-1">{dim.icon} {dim.label}</div>
      <div className="flex items-center gap-3 text-xs">
        <span className="text-gray-400">
          Weight: <span className="text-white font-medium">{dim.weight}%</span>
        </span>
        <span className="text-gray-400">
          Score: <span style={{ color: band.color }} className="font-bold">{dim.score}</span>
        </span>
      </div>
      <div className="mt-1 text-xs text-gray-500">
        Gap: {dim.weight - Math.round(dim.score * dim.weight / 100)} pts of potential
      </div>
    </div>
  );
}

// ─── Variant A: Classic Dual Overlay ─────────────────────────────────────────
// Weight = outer "budget" boundary (rounded), Score = filled inner area
function VariantA({ data, hoveredKey, onHover }) {
  return (
    <ResponsiveContainer width="100%" height={380}>
      <RadarChart data={data} cx="50%" cy="50%" outerRadius="72%">
        <PolarGrid stroke="#1f2937" />
        <PolarAngleAxis
          dataKey="shortLabel"
          tick={(props) => <CustomTick {...props} hoveredKey={hoveredKey} onHover={onHover} />}
        />
        <PolarRadiusAxis angle={90} domain={[0, 100]} tick={false} axisLine={false} />

        {/* Weight envelope — rounded, translucent */}
        <Radar
          name="Weight"
          dataKey="weight_scaled"
          stroke="#6366f1"
          strokeWidth={2}
          strokeDasharray="6 3"
          fill="#6366f1"
          fillOpacity={0.06}
          shape={(props) => (
            <RoundedRadarShape
              points={props.points}
              fillColor="#6366f1"
              fillOpacity={0.06}
              strokeColor="#6366f1"
              strokeWidth={2}
            />
          )}
        />

        {/* Score fill — rounded, colored by composite band */}
        <Radar
          name="Score"
          dataKey="score"
          stroke={bandFor(COMPOSITE).color}
          strokeWidth={2.5}
          fill={bandFor(COMPOSITE).color}
          fillOpacity={0.2}
          shape={(props) => (
            <RoundedRadarShape
              points={props.points}
              fillColor={bandFor(COMPOSITE).color}
              fillOpacity={0.2}
              strokeColor={bandFor(COMPOSITE).color}
              strokeWidth={2.5}
            />
          )}
        />

        <Tooltip content={<CustomTooltip />} />
      </RadarChart>
    </ResponsiveContainer>
  );
}

// ─── Variant B: Per-dimension band coloring ──────────────────────────────────
// Same dual-radar structure but the score radar is drawn as individual
// wedge-colored segments via a custom shape
function PerDimColorShape({ points, cx, cy }) {
  if (!points || points.length < 2) return null;

  return (
    <g>
      {points.map((pt, i) => {
        const next = points[(i + 1) % points.length];
        const dim = DIMENSIONS[i];
        const band = bandFor(dim.score);

        return (
          <polygon
            key={dim.key}
            points={`${cx},${cy} ${pt.x},${pt.y} ${next.x},${next.y}`}
            fill={band.color}
            fillOpacity={0.25}
            stroke={band.color}
            strokeWidth={1.5}
            strokeLinejoin="round"
          />
        );
      })}
    </g>
  );
}

function VariantB({ data, hoveredKey, onHover }) {
  return (
    <ResponsiveContainer width="100%" height={380}>
      <RadarChart data={data} cx="50%" cy="50%" outerRadius="72%">
        <PolarGrid stroke="#1f2937" />
        <PolarAngleAxis
          dataKey="shortLabel"
          tick={(props) => <CustomTick {...props} hoveredKey={hoveredKey} onHover={onHover} />}
        />
        <PolarRadiusAxis angle={90} domain={[0, 100]} tick={false} axisLine={false} />

        {/* Weight envelope */}
        <Radar
          name="Weight"
          dataKey="weight_scaled"
          stroke="#6366f1"
          strokeWidth={2}
          strokeDasharray="6 3"
          fill="#6366f1"
          fillOpacity={0.06}
          shape={(props) => (
            <RoundedRadarShape
              points={props.points}
              fillColor="#6366f1"
              fillOpacity={0.06}
              strokeColor="#6366f1"
              strokeWidth={2}
            />
          )}
        />

        {/* Score — per-dimension colored wedges */}
        <Radar
          name="Score"
          dataKey="score"
          fill="transparent"
          stroke="transparent"
          shape={(props) => <PerDimColorShape points={props.points} cx={props.cx} cy={props.cy} />}
        />

        <Tooltip content={<CustomTooltip />} />
      </RadarChart>
    </ResponsiveContainer>
  );
}

// ─── Variant C: Gap visualization ────────────────────────────────────────────
// Weight envelope + score fill + explicit "gap" shading between them
function GapShape({ scorePoints, weightPoints, cx, cy }) {
  if (!scorePoints || !weightPoints || scorePoints.length < 3) return null;

  // Draw individual gap triangles per dimension
  return (
    <g>
      {scorePoints.map((sp, i) => {
        const wp = weightPoints[i];
        const spNext = scorePoints[(i + 1) % scorePoints.length];
        const wpNext = weightPoints[(i + 1) % weightPoints.length];

        return (
          <polygon
            key={i}
            points={`${sp.x},${sp.y} ${wp.x},${wp.y} ${wpNext.x},${wpNext.y} ${spNext.x},${spNext.y}`}
            fill="#ef4444"
            fillOpacity={0.08}
            stroke="#ef4444"
            strokeWidth={0.5}
            strokeDasharray="2 2"
          />
        );
      })}
    </g>
  );
}

function VariantC({ data, hoveredKey, onHover }) {
  // We need to capture points from both radars — Recharts doesn't expose this easily,
  // so we compute them manually for the gap overlay
  const outerRadius = 130; // approximate
  const cx = 0, cy = 0; // will be relative

  return (
    <ResponsiveContainer width="100%" height={380}>
      <RadarChart data={data} cx="50%" cy="50%" outerRadius="72%">
        <PolarGrid stroke="#1f2937" />
        <PolarAngleAxis
          dataKey="shortLabel"
          tick={(props) => <CustomTick {...props} hoveredKey={hoveredKey} onHover={onHover} />}
        />
        <PolarRadiusAxis angle={90} domain={[0, 100]} tick={false} axisLine={false} />

        {/* Gap layer — shows as red between weight and score */}
        <Radar
          name="Gap"
          dataKey="gap"
          stroke="#ef4444"
          strokeWidth={0}
          fill="#ef4444"
          fillOpacity={0.08}
          shape={(props) => (
            <RoundedRadarShape
              points={props.points}
              fillColor="#ef4444"
              fillOpacity={0.08}
              strokeColor="#ef4444"
              strokeWidth={0.5}
            />
          )}
        />

        {/* Weight envelope */}
        <Radar
          name="Weight"
          dataKey="weight_scaled"
          stroke="#6366f1"
          strokeWidth={2}
          strokeDasharray="6 3"
          fill="transparent"
          fillOpacity={0}
          shape={(props) => (
            <RoundedRadarShape
              points={props.points}
              fillColor="transparent"
              fillOpacity={0}
              strokeColor="#6366f1"
              strokeWidth={2}
            />
          )}
        />

        {/* Score fill */}
        <Radar
          name="Score"
          dataKey="score"
          stroke={bandFor(COMPOSITE).color}
          strokeWidth={2.5}
          fill={bandFor(COMPOSITE).color}
          fillOpacity={0.2}
          shape={(props) => (
            <RoundedRadarShape
              points={props.points}
              fillColor={bandFor(COMPOSITE).color}
              fillOpacity={0.2}
              strokeColor={bandFor(COMPOSITE).color}
              strokeWidth={2.5}
            />
          )}
        />

        <Tooltip content={<CustomTooltip />} />
      </RadarChart>
    </ResponsiveContainer>
  );
}

// ─── Variant D: Minimal "target ring" ────────────────────────────────────────
// Weight shown as dots/markers on the outer ring, score as filled rounded radar
function TargetDotShape({ points }) {
  if (!points) return null;
  return (
    <g>
      {points.map((pt, i) => (
        <g key={i}>
          <circle cx={pt.x} cy={pt.y} r={5} fill="#6366f1" fillOpacity={0.3} stroke="#6366f1" strokeWidth={1.5} />
          <circle cx={pt.x} cy={pt.y} r={2} fill="#6366f1" />
        </g>
      ))}
      {/* Connect dots with dashed line */}
      <polygon
        points={points.map((p) => `${p.x},${p.y}`).join(" ")}
        fill="none"
        stroke="#6366f1"
        strokeWidth={1}
        strokeDasharray="4 4"
        strokeOpacity={0.5}
      />
    </g>
  );
}

function VariantD({ data, hoveredKey, onHover }) {
  return (
    <ResponsiveContainer width="100%" height={380}>
      <RadarChart data={data} cx="50%" cy="50%" outerRadius="72%">
        <PolarGrid stroke="#1f2937" />
        <PolarAngleAxis
          dataKey="shortLabel"
          tick={(props) => <CustomTick {...props} hoveredKey={hoveredKey} onHover={onHover} />}
        />
        <PolarRadiusAxis angle={90} domain={[0, 100]} tick={false} axisLine={false} />

        {/* Weight as target markers */}
        <Radar
          name="Weight Target"
          dataKey="weight_scaled"
          fill="transparent"
          stroke="transparent"
          shape={(props) => <TargetDotShape points={props.points} />}
        />

        {/* Score — rounded filled area */}
        <Radar
          name="Score"
          dataKey="score"
          stroke={bandFor(COMPOSITE).color}
          strokeWidth={2.5}
          fill={bandFor(COMPOSITE).color}
          fillOpacity={0.2}
          shape={(props) => (
            <RoundedRadarShape
              points={props.points}
              fillColor={bandFor(COMPOSITE).color}
              fillOpacity={0.2}
              strokeColor={bandFor(COMPOSITE).color}
              strokeWidth={2.5}
            />
          )}
          dot={{ r: 4, fill: bandFor(COMPOSITE).color, strokeWidth: 0 }}
        />

        <Tooltip content={<CustomTooltip />} />
      </RadarChart>
    </ResponsiveContainer>
  );
}

// ─── Sparkline ───────────────────────────────────────────────────────────────
const TREND = [62, 59, 61, 63, 60, 64, 65, 63, 67, 66, 68, 65];

function Sparkline({ data, width = 140, height = 36, color }) {
  const min = Math.min(...data) - 2, max = Math.max(...data) + 2;
  const pts = data.map((v, i) => `${(i / (data.length - 1)) * width},${height - ((v - min) / (max - min)) * height}`).join(" ");
  const delta = data[data.length - 1] - data[data.length - 2];
  return (
    <div className="flex items-center gap-2">
      <svg width={width} height={height} className="overflow-visible">
        <polyline fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" points={pts} />
      </svg>
      <span className={`text-sm font-semibold ${delta >= 0 ? "text-emerald-400" : "text-red-400"}`}>
        {delta >= 0 ? "↑" : "↓"}{Math.abs(delta)}
      </span>
    </div>
  );
}

// ─── Variant configs ─────────────────────────────────────────────────────────
const VARIANTS = [
  {
    key: "A",
    label: "Dual Overlay",
    desc: "Rounded weight envelope (dashed) with score fill inside — clean layering, easy to read the gap at each axis",
    Component: VariantA,
  },
  {
    key: "B",
    label: "Band-Colored Wedges",
    desc: "Weight envelope + per-dimension colored wedges — immediately shows which dimensions are healthy vs critical",
    Component: VariantB,
  },
  {
    key: "C",
    label: "Gap Highlight",
    desc: "Explicit red gap shading between weight target and score — draws the eye to improvement opportunities",
    Component: VariantC,
  },
  {
    key: "D",
    label: "Target Markers",
    desc: "Weight shown as target dots, score as rounded fill — minimal, less visual noise, focus stays on the score shape",
    Component: VariantD,
  },
];

// ─── Main ────────────────────────────────────────────────────────────────────
export default function GPSDualRadar() {
  const [variant, setVariant] = useState("A");
  const [hoveredKey, setHoveredKey] = useState(null);

  // Recharts data: weight_scaled maps weight% to the 0-100 radar scale
  // e.g., 20% weight → shows at 100 on the axis (full reach for that dimension)
  // This makes the weight envelope represent "this dimension's share of your attention"
  const chartData = useMemo(() =>
    DIMENSIONS.map((d) => ({
      ...d,
      shortLabel: d.shortLabel,
      score: d.score,
      weight_scaled: d.weight * 5, // 20% → 100, 15% → 75, 10% → 50
      gap: d.weight * 5, // for the gap layer underlay
    })),
    []
  );

  const band = bandFor(COMPOSITE);
  const CurrentVariant = VARIANTS.find((v) => v.key === variant).Component;
  const hoveredDim = DIMENSIONS.find((d) => d.key === hoveredKey);

  return (
    <div className="min-h-screen bg-gray-950 text-white p-6">
      <style>{`
        @keyframes fadeIn { from { opacity:0; transform:translateY(4px) } to { opacity:1; transform:translateY(0) } }
        .animate-fadeIn { animation: fadeIn 0.25s ease-out }
      `}</style>

      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold mb-1">GPS — Dual Radar Explorer</h1>
          <p className="text-sm text-gray-500">
            Weight envelope (dashed) = how much each dimension matters · Score fill = how you're actually doing
          </p>
        </div>

        {/* Variant switcher */}
        <div className="flex flex-wrap gap-2 mb-2">
          {VARIANTS.map((v) => (
            <button
              key={v.key}
              onClick={() => setVariant(v.key)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                variant === v.key
                  ? "bg-indigo-600 text-white"
                  : "bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-gray-200"
              }`}
            >
              {v.key}. {v.label}
            </button>
          ))}
        </div>
        <p className="text-xs text-gray-600 mb-6 italic">
          {VARIANTS.find((v) => v.key === variant)?.desc}
        </p>

        {/* Main layout */}
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          {/* Radar — 3 cols */}
          <div className="lg:col-span-3 bg-gray-900/50 rounded-2xl border border-gray-800 p-4">
            {/* Center score overlay */}
            <div className="relative">
              <CurrentVariant data={chartData} hoveredKey={hoveredKey} onHover={setHoveredKey} />

              {/* Floating center score */}
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none" style={{ top: "-10px" }}>
                <div className="text-center">
                  <div className={`text-5xl font-black ${band.text}`}>
                    <AnimatedNumber value={COMPOSITE} />
                  </div>
                  <div className={`text-xs font-semibold px-2 py-0.5 rounded-full ${band.bg} text-white mt-1 inline-block`}>
                    {band.label}
                  </div>
                </div>
              </div>
            </div>

            {/* Hover detail + trend */}
            <div className="flex items-center justify-between mt-2 px-2">
              <div className="h-8 flex items-center">
                {hoveredDim ? (
                  <div className="animate-fadeIn text-sm">
                    <span className="text-white font-medium">{hoveredDim.icon} {hoveredDim.label}</span>
                    <span className={`ml-2 font-bold`} style={{ color: bandFor(hoveredDim.score).color }}>{hoveredDim.score}</span>
                    <span className="ml-1 text-gray-500 text-xs">/ target {hoveredDim.weight * 5}</span>
                  </div>
                ) : (
                  <span className="text-xs text-gray-600">Hover an axis to inspect</span>
                )}
              </div>
              <Sparkline data={TREND} color={band.color} />
            </div>
          </div>

          {/* Dimension list — 2 cols */}
          <div className="lg:col-span-2 space-y-2">
            <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Dimensions</h2>
            {DIMENSIONS.map((d) => {
              const db = bandFor(d.score);
              const target = d.weight * 5;
              const isHovered = hoveredKey === d.key;
              const gap = target - d.score;
              return (
                <div
                  key={d.key}
                  className={`p-3 rounded-xl transition-all cursor-pointer ${
                    isHovered ? "bg-gray-800/80 ring-1 ring-gray-700" : "hover:bg-gray-900/50"
                  }`}
                  onMouseEnter={() => setHoveredKey(d.key)}
                  onMouseLeave={() => setHoveredKey(null)}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-sm text-gray-300 flex items-center gap-1.5">
                      {d.icon} {d.label}
                      <span className="text-xs text-gray-600">({d.weight}%)</span>
                    </span>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-bold" style={{ color: db.color }}>{d.score}</span>
                      {gap > 0 && (
                        <span className="text-xs text-gray-600">
                          −{gap} to target
                        </span>
                      )}
                    </div>
                  </div>
                  {/* Dual bar: target background + score fill */}
                  <div className="relative w-full h-2 bg-gray-800 rounded-full overflow-hidden">
                    {/* Target marker */}
                    <div
                      className="absolute top-0 h-full rounded-full bg-indigo-500/20"
                      style={{ width: `${target}%` }}
                    />
                    {/* Score fill */}
                    <div
                      className="absolute top-0 h-full rounded-full transition-all duration-500"
                      style={{
                        width: `${d.score}%`,
                        background: `linear-gradient(90deg, ${db.color}88, ${db.color})`,
                      }}
                    />
                    {/* Target tick */}
                    <div
                      className="absolute top-0 h-full w-0.5 bg-indigo-400"
                      style={{ left: `${target}%` }}
                    />
                  </div>
                </div>
              );
            })}

            {/* Legend */}
            <div className="pt-4 mt-2 border-t border-gray-800 space-y-2">
              <div className="flex items-center gap-4 text-xs text-gray-500">
                <span className="flex items-center gap-1.5">
                  <span className="w-4 border-t-2 border-dashed border-indigo-500 inline-block" /> Weight target
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-4 border-t-2 border-blue-500 inline-block" /> Score
                </span>
              </div>
              <div className="flex gap-3">
                {[
                  { label: "Critical", range: "0–39", color: "bg-red-500" },
                  { label: "At Risk", range: "40–59", color: "bg-amber-500" },
                  { label: "Good", range: "60–79", color: "bg-blue-500" },
                  { label: "Excellent", range: "80+", color: "bg-emerald-500" },
                ].map((b) => (
                  <span key={b.label} className="flex items-center gap-1 text-xs text-gray-600">
                    <span className={`w-2 h-2 rounded-full ${b.color}`} /> {b.label}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Astralis narrative */}
        <div className="mt-6 bg-gray-900/40 rounded-xl border border-gray-800 p-4 max-w-3xl">
          <p className="text-xs text-gray-500 uppercase tracking-wider font-semibold mb-1">Astralis Insight</p>
          <p className="text-sm text-gray-300 leading-relaxed">
            Classification Health improved +8 pts after last week's scan, closing the gap to its weight target.
            Consent Alignment dropped — 12 processing activities now lack matching consent records, making it
            your highest-leverage improvement area.
          </p>
        </div>
      </div>
    </div>
  );
}