import React from "react";

import { CardProps } from "./types";

export const DsrStatusCard = ({ state }: CardProps) => {
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
      {/* Title bar */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: 6,
        }}
      >
        <span
          style={{
            fontSize: 10,
            textTransform: "uppercase",
            letterSpacing: "0.05em",
            color: "#666",
          }}
        >
          DSR Status
        </span>
        {state === "expanded" && (
          <span
            style={{
              fontSize: 11,
              textDecoration: "underline",
              color: "#444",
              cursor: "pointer",
            }}
          >
            View all requests →
          </span>
        )}
      </div>

      {/* Body */}
      {state === "compressed" ? (
        <>
          <div style={{ fontSize: 12, marginBottom: 6 }}>
            14 active · <span style={{ color: "#c44" }}>2 overdue</span>
          </div>
          {/* Segmented health meter */}
          <div style={{ display: "flex", gap: 2 }}>
            {[0, 1, 2, 3].map((i) => (
              <div
                key={i}
                style={{
                  flex: 1,
                  height: 6,
                  background: i === 3 ? "#c44" : "#999",
                }}
              />
            ))}
          </div>
        </>
      ) : (
        <div style={{ flex: 1, overflow: "hidden" }}>
          {/* Active count hero row */}
          <div style={{ marginBottom: 4 }}>
            <span style={{ fontSize: 22, fontWeight: "bold" }}>14 active</span>
          </div>
          <div style={{ fontSize: 11, color: "#666", marginBottom: 10 }}>
            In Progress: 9 · Pending Action: 3 · Awaiting Approval: 2
          </div>

          {/* Chart placeholder */}
          <div
            style={{
              width: "100%",
              height: 120,
              background: "#e0e0e0",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              marginBottom: 8,
            }}
          >
            <span style={{ fontSize: 11, color: "#666" }}>
              bar chart (stacked, SLA health per DSR type)
            </span>
          </div>

          {/* Legend row */}
          <div style={{ display: "flex", gap: 12 }}>
            {[
              { chip: "#999", label: "On track" },
              { chip: "#bbb", label: "Approaching" },
              { chip: "#c44", label: "Overdue" },
            ].map(({ chip, label }) => (
              <div
                key={label}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 4,
                  fontSize: 11,
                }}
              >
                <span
                  style={{
                    width: 8,
                    height: 8,
                    borderRadius: "50%",
                    background: chip,
                    flexShrink: 0,
                    display: "inline-block",
                  }}
                />
                <span>{label}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default DsrStatusCard;
