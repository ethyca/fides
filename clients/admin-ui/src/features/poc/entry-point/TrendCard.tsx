import { CardProps } from "./types";

type TrendMetric =
  | "governance-posture"
  | "dsr-volume"
  | "system-coverage"
  | "classification-health";

const METRICS: Record<
  TrendMetric,
  { label: string; value: string; delta: string }
> = {
  "governance-posture": {
    label: "Governance Posture",
    value: "92%",
    delta: "↑ 3",
  },
  "dsr-volume": { label: "DSR Volume", value: "148", delta: "↑ 12" },
  "system-coverage": {
    label: "System Coverage",
    value: "82%",
    delta: "↑ 5",
  },
  "classification-health": {
    label: "Classification Health",
    value: "78%",
    delta: "↓ 2",
  },
};

interface TrendCardProps extends CardProps {
  metric: TrendMetric;
}

const TrendCard = ({ state, metric }: TrendCardProps) => {
  const { label, value, delta } = METRICS[metric];

  if (state === "compressed") {
    return (
      <div
        style={{
          height: "100%",
          border: "1px solid #e0e0e0",
          boxSizing: "border-box",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          padding: 8,
        }}
      >
        <div style={{ fontSize: 16, fontWeight: "bold" }}>
          {value} {delta}
        </div>
        <div
          style={{
            fontSize: 10,
            opacity: 0.5,
            marginTop: 4,
            textAlign: "center",
          }}
        >
          {label}
        </div>
      </div>
    );
  }

  return (
    <div
      style={{
        height: "100%",
        border: "1px solid #e0e0e0",
        boxSizing: "border-box",
        display: "flex",
        flexDirection: "column",
        padding: 8,
      }}
    >
      {/* Title bar */}
      <div
        style={{
          fontSize: 10,
          textTransform: "uppercase",
          color: "#666",
          letterSpacing: "0.05em",
          marginBottom: 4,
        }}
      >
        {label}
      </div>

      {/* Value + delta */}
      <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
        <span style={{ fontSize: 28, fontWeight: "bold" }}>{value}</span>
        <span style={{ fontSize: 14, color: "#666" }}>{delta}</span>
      </div>

      {/* Sparkline placeholder */}
      <div
        style={{
          flex: 1,
          background: "#e0e0e0",
          marginTop: 8,
          minHeight: 100,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 12,
          color: "#888",
        }}
      >
        sparkline
      </div>
    </div>
  );
};

export default TrendCard;
