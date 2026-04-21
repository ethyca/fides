import React from "react";

import { CardProps } from "./types";

export const SystemCoverageCard = ({ state }: CardProps) => {
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
          System Coverage
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
            Connect more systems →
          </span>
        )}
      </div>

      {/* Body */}
      {state === "compressed" ? (
        <>
          <div style={{ fontSize: 13, fontWeight: "bold", marginBottom: 6 }}>
            82% · 47 systems
          </div>
          {/* Horizontal meter */}
          <div
            style={{
              height: 8,
              background: "#eee",
              width: "100%",
            }}
          >
            <div
              style={{
                height: "100%",
                width: "82%",
                background: "#999",
              }}
            />
          </div>
        </>
      ) : (
        <div style={{ display: "flex", gap: 16, flex: 1, overflow: "hidden" }}>
          {/* Left: donut placeholder */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
            }}
          >
            <div
              style={{
                width: 140,
                height: 140,
                borderRadius: "50%",
                background: "#e0e0e0",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <span style={{ fontSize: 28, fontWeight: "bold", lineHeight: 1 }}>
                82%
              </span>
              <span style={{ fontSize: 10, marginTop: 4 }}>47 systems</span>
            </div>
          </div>

          {/* Right: breakdown list */}
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              justifyContent: "center",
              gap: 6,
            }}
          >
            {[
              { chip: "#555", label: "Fully classified", count: 36 },
              { chip: "#888", label: "Partially classified", count: 7 },
              { chip: "#bbb", label: "Unclassified", count: 3 },
              { chip: "#ddd", label: "Without steward", count: 1 },
            ].map(({ chip, label, count }) => (
              <div
                key={label}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 6,
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
                <span style={{ color: "#666" }}>{count}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default SystemCoverageCard;
