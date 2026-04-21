import { CardProps } from "./types";

const AiBriefingCard = ({ state }: CardProps) => {
  if (state === "compressed") {
    return (
      <div
        style={{
          height: "100%",
          display: "flex",
          alignItems: "center",
          padding: 8,
          boxSizing: "border-box",
        }}
      >
        <p style={{ fontSize: 12, color: "#444", margin: 0 }}>
          Since yesterday: 3 DSRs completed, 1 new critical risk detected in
          BigQuery.
        </p>
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
        position: "relative",
      }}
    >
      {/* Dismiss control */}
      <button
        type="button"
        style={{
          position: "absolute",
          top: 8,
          right: 8,
          background: "none",
          border: "none",
          padding: 0,
          cursor: "pointer",
          fontSize: 10,
          color: "#999",
          lineHeight: 1,
        }}
        onClick={(e) => e.stopPropagation()}
      >
        ✕
      </button>

      {/* Briefing paragraphs */}
      <div style={{ flex: 1, fontSize: 13, color: "#333", lineHeight: 1.5 }}>
        <p style={{ margin: "0 0 10px" }}>
          Your data map now covers 94 active systems across 3 business units.
          Overnight processing completed 3 pending DSRs and flagged 1 new
          critical risk in BigQuery due to unclassified fields containing PII.
        </p>
        <p style={{ margin: "0 0 10px" }}>
          Classification completeness dropped 2 points this week, driven by 12
          newly discovered tables in the Snowflake warehouse that have not yet
          been assigned a data steward. Two privacy assessments are overdue and
          require review before the upcoming audit window closes.
        </p>
        <p style={{ margin: 0 }}>
          Consent signal processing is operating normally. Cross-border transfer
          checks passed for all configured data flows. No policy violations were
          detected in the last 24 hours.
        </p>
      </div>

      {/* Action links */}
      <div style={{ display: "flex", gap: 16, marginTop: 12, flexShrink: 0 }}>
        {["Assign steward →", "Review classifications →", "View risks →"].map(
          (link) => (
            <button
              key={link}
              type="button"
              style={{
                background: "none",
                border: "none",
                padding: 0,
                color: "#1a73e8",
                textDecoration: "underline",
                cursor: "pointer",
                fontSize: 11,
              }}
            >
              {link}
            </button>
          ),
        )}
      </div>
    </div>
  );
};

export default AiBriefingCard;
