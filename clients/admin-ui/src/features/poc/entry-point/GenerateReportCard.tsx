import React from "react";

import { CardProps } from "./types";

export const GenerateReportCard = ({ state }: CardProps) => {
  return (
    <div
      style={{
        height: "100%",
        border: "1px solid #e0e0e0",
        overflow: "hidden",
        display: "flex",
        flexDirection: "column",
        padding: 8,
        background: "white",
      }}
    >
      {state === "compressed" ? (
        /* Compressed: centered button-like div, no title */
        <div
          style={{
            flex: 1,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <div
            style={{
              border: "1px solid #999",
              padding: "6px 12px",
              fontSize: 12,
              textAlign: "center",
            }}
          >
            Generate executive report
          </div>
        </div>
      ) : (
        <>
          {/* Title bar */}
          <div style={{ marginBottom: 6 }}>
            <span
              style={{
                fontSize: 10,
                textTransform: "uppercase",
                letterSpacing: "0.05em",
                color: "#666",
              }}
            >
              Generate Report
            </span>
          </div>

          {/* Preview panel */}
          <div
            style={{
              border: "1px solid #eee",
              padding: 8,
              marginBottom: 8,
            }}
          >
            <div
              style={{
                fontSize: 10,
                textTransform: "uppercase",
                color: "#666",
                marginBottom: 6,
              }}
            >
              Report contents
            </div>
            <div style={{ fontSize: 11, marginBottom: 4 }}>
              Governance Posture Score: 72
            </div>
            <div style={{ fontSize: 11, marginBottom: 4 }}>
              Top trends: Governance +3, DSR Volume +12, Classification -2
            </div>
            <div style={{ fontSize: 11, marginBottom: 8 }}>
              Top risks: 2 critical, 5 high
            </div>

            {/* Date range selector */}
            <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
              {[
                { label: "Last 7 days", active: false },
                { label: "Last 30 days", active: true },
                { label: "Last 90 days", active: false },
              ].map(({ label, active }) => (
                <span
                  key={label}
                  style={{
                    fontSize: 11,
                    padding: "3px 8px",
                    display: "inline-block",
                    border: "1px solid #ccc",
                    borderBottom: active ? "1px solid #333" : "1px solid #ccc",
                    fontWeight: active ? "bold" : "normal",
                    cursor: "pointer",
                  }}
                >
                  {label}
                </span>
              ))}
            </div>
          </div>

          {/* Primary button */}
          <div
            style={{
              border: "1px solid #333",
              background: "#333",
              color: "white",
              padding: "6px 12px",
              fontSize: 12,
              textAlign: "center",
              cursor: "pointer",
            }}
          >
            Generate executive report
          </div>

          {/* Secondary button */}
          <div
            style={{
              border: "1px solid #999",
              padding: "6px 12px",
              fontSize: 11,
              textAlign: "center",
              marginTop: 6,
              cursor: "pointer",
            }}
          >
            Share via Slack
          </div>
        </>
      )}
    </div>
  );
};

export default GenerateReportCard;
