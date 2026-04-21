import React from "react";

import { CardProps } from "./types";

interface UnitRow {
  name: string;
  chipColor: string;
  systems: number;
  score: number;
  trend: string;
}

const units: UnitRow[] = [
  { name: "Marketing", chipColor: "#777", systems: 18, score: 54, trend: "↓" },
  { name: "Legal", chipColor: "#888", systems: 7, score: 72, trend: "→" },
  {
    name: "Engineering",
    chipColor: "#999",
    systems: 24,
    score: 83,
    trend: "↑",
  },
  { name: "Finance", chipColor: "#aaa", systems: 11, score: 89, trend: "↑" },
  { name: "Product", chipColor: "#bbb", systems: 9, score: 91, trend: "↑" },
  { name: "HR", chipColor: "#ccc", systems: 6, score: 93, trend: "↑" },
];

export const BusinessUnitsCard = ({ state }: CardProps) => {
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
          Business Units
        </span>
        {state === "expanded" && (
          <span
            style={{
              border: "1px solid #ccc",
              fontSize: 10,
              padding: "1px 6px",
              cursor: "pointer",
            }}
          >
            Sort: Lowest ▾
          </span>
        )}
      </div>

      {/* Body */}
      <div style={{ flex: 1, overflow: "hidden" }}>
        {state === "compressed" ? (
          <div style={{ fontSize: 12, color: "#333" }}>
            12 units · Lowest: Marketing, 54
          </div>
        ) : (
          <div>
            {units.map((unit) => (
              <div
                key={unit.name}
                style={{
                  display: "flex",
                  alignItems: "center",
                  fontSize: 12,
                  paddingTop: 4,
                  paddingBottom: 4,
                  borderBottom: "1px solid #f5f5f5",
                }}
              >
                {/* Color chip */}
                <span
                  style={{
                    width: 8,
                    height: 8,
                    borderRadius: "50%",
                    background: unit.chipColor,
                    display: "inline-block",
                    marginRight: 8,
                    flexShrink: 0,
                  }}
                />
                {/* Name */}
                <span style={{ flex: 1 }}>{unit.name}</span>
                {/* Systems */}
                <span style={{ color: "#777", marginRight: 12, fontSize: 11 }}>
                  {unit.systems} systems
                </span>
                {/* Score */}
                <span style={{ color: "#555", marginRight: 10, fontSize: 11 }}>
                  Score: {unit.score}
                </span>
                {/* Trend */}
                <span style={{ color: "#555", fontSize: 13 }}>
                  {unit.trend}
                </span>
              </div>
            ))}
            <div style={{ fontSize: 10, color: "#bbb", marginTop: 6 }}>
              +6 more units
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default BusinessUnitsCard;
