import RadialScoreChart from "./RadialScoreChart";

const BG = "#0d1419";

const sans = "'Inter', system-ui, sans-serif";
const mono = "'IBM Plex Mono', ui-monospace, monospace";

const DARK_PALETTE = {
  ink: "#e8e3d6",
  muted: "#8a8a8e",
  faint: "#5e6066",
  arcStrong: "#dcd5c5",
  arcWarm: "#d4ad44",
  hairline: "rgba(232, 227, 214, 0.10)",
  hairlineFaint: "rgba(232, 227, 214, 0.06)",
  centerStroke: "rgba(232, 227, 214, 0.35)",
};

const DIMENSIONS = [
  { name: "Coverage", score: 92, weight: 18 },
  { name: "Classification", score: 71, weight: 16 },
  { name: "Health", score: 88, weight: 14 },
  { name: "Consent Alignment", score: 64, weight: 14 },
  { name: "DSR Compliance", score: 76, weight: 12 },
  { name: "Policy Enforcement", score: 58, weight: 16 },
  { name: "AI Readiness", score: 81, weight: 10 },
];

const GovernanceScoreChart = () => (
  <div
    style={{
      width: "100%",
      minHeight: "100vh",
      background: BG,
      color: DARK_PALETTE.ink,
      fontFamily: sans,
      padding: "48px 64px",
      boxSizing: "border-box",
      display: "flex",
      flexDirection: "column",
    }}
  >
    <div style={{ display: "flex", alignItems: "flex-start", gap: 48 }}>
      <div>
        <div style={{ display: "flex", alignItems: "baseline", gap: 6 }}>
          <span
            style={{
              fontFamily: mono,
              fontSize: 88,
              fontWeight: 300,
              lineHeight: 1,
              letterSpacing: "-0.02em",
            }}
          >
            84
          </span>
          <span
            style={{
              fontFamily: mono,
              fontSize: 22,
              color: DARK_PALETTE.muted,
            }}
          >
            /100
          </span>
        </div>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            marginTop: 14,
            fontSize: 15,
            color: DARK_PALETTE.muted,
          }}
        >
          <span>Good</span>
          <span
            style={{
              width: 8,
              height: 8,
              borderRadius: "50%",
              background: DARK_PALETTE.arcWarm,
            }}
          />
        </div>
      </div>

      <div
        style={{
          paddingLeft: 32,
          borderLeft: `1px solid ${DARK_PALETTE.hairline}`,
          maxWidth: 360,
          fontSize: 15,
          lineHeight: 1.45,
          color: DARK_PALETTE.muted,
          paddingTop: 6,
        }}
      >
        Your governance posture is strong. Continue to address gaps to reach
        excellence.
      </div>
    </div>

    <div
      style={{
        flex: 1,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        minHeight: 0,
        marginTop: 24,
      }}
    >
      <RadialScoreChart
        size={720}
        dimensions={DIMENSIONS}
        overallScore={84}
        palette={DARK_PALETTE}
      />
    </div>
  </div>
);

export default GovernanceScoreChart;
