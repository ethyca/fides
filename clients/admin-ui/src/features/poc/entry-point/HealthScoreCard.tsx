import { CardProps } from "./types";

const HealthScoreCard = ({ state }: CardProps) => {
  if (state === "compressed") {
    return (
      <div
        style={{
          height: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <div style={{ fontSize: 48, fontWeight: "bold", lineHeight: 1 }}>
          72
        </div>
        <div style={{ fontSize: 14, color: "#555", marginTop: 4 }}>Good</div>
        <div style={{ fontSize: 12, color: "#777", marginTop: 2 }}>
          ↑ 2 points this week
        </div>
      </div>
    );
  }

  return (
    <div
      style={{
        height: "100%",
        display: "flex",
        flexDirection: "column",
        padding: 8,
        boxSizing: "border-box",
      }}
    >
      {/* Top row: score + radar chart */}
      <div style={{ display: "flex", gap: 16, flex: 1, minHeight: 0 }}>
        {/* Left: score */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
            minWidth: 100,
          }}
        >
          <div style={{ fontSize: 48, fontWeight: "bold", lineHeight: 1 }}>
            72
          </div>
          <div style={{ fontSize: 14, color: "#555", marginTop: 4 }}>Good</div>
          <div style={{ fontSize: 12, color: "#777", marginTop: 2 }}>
            ↑ 2 pts this wk
          </div>
        </div>

        {/* Right: radar chart placeholder */}
        <div
          style={{
            flex: 1,
            minHeight: 200,
            background: "#e0e0e0",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 12,
            color: "#888",
          }}
        >
          radar
        </div>
      </div>

      {/* Stat blocks row */}
      <div
        style={{
          display: "flex",
          gap: 8,
          marginTop: 12,
        }}
      >
        {[
          { label: "Data Coverage", value: 85 },
          { label: "Classification", value: 78 },
          { label: "DSR Health", value: 91 },
          { label: "Consent", value: 88 },
        ].map(({ label, value }) => (
          <div
            key={label}
            style={{
              flex: 1,
              textAlign: "center",
              borderTop: "1px solid #e0e0e0",
              paddingTop: 8,
            }}
          >
            <div style={{ fontSize: 12, color: "#555" }}>{label}</div>
            <div style={{ fontSize: 18, fontWeight: "bold" }}>{value}</div>
          </div>
        ))}
      </div>

      {/* Bottom trend note */}
      <div
        style={{
          fontSize: 11,
          color: "#666",
          fontStyle: "italic",
          marginTop: 8,
        }}
      >
        ↑ 2 points, driven by 34 newly approved classifications in Snowflake
      </div>
    </div>
  );
};

export default HealthScoreCard;
