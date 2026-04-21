import React from "react";

import { CardProps } from "./types";

const ActionBtn = ({ label }: { label: string }) => (
  <span
    style={{
      border: "1px solid #ccc",
      fontSize: 10,
      padding: "2px 6px",
      marginLeft: 4,
      cursor: "pointer",
    }}
  >
    {label}
  </span>
);

const SectionHeader = ({ label }: { label: string }) => (
  <div
    style={{
      fontSize: 10,
      textTransform: "uppercase",
      letterSpacing: "0.05em",
      color: "#555",
      marginTop: 8,
      marginBottom: 4,
    }}
  >
    {label}
  </div>
);

interface RiskRowProps {
  title: string;
  context: string;
  astralis: string;
  actions: string[];
}

const RiskRow = ({ title, context, astralis, actions }: RiskRowProps) => (
  <div style={{ marginBottom: 8 }}>
    <div
      style={{
        display: "flex",
        alignItems: "flex-start",
        justifyContent: "space-between",
      }}
    >
      <span style={{ fontSize: 11, fontWeight: "bold", flex: 1 }}>{title}</span>
      <span style={{ flexShrink: 0 }}>
        {actions.map((a) => (
          <ActionBtn key={a} label={a} />
        ))}
      </span>
    </div>
    <div style={{ fontSize: 10, color: "#777", marginTop: 1 }}>{context}</div>
    <div
      style={{ fontSize: 10, color: "#777", fontStyle: "italic", marginTop: 2 }}
    >
      {astralis}
    </div>
  </div>
);

export const RisksCard = ({ state }: CardProps) => {
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
      <div style={{ marginBottom: 6 }}>
        <span
          style={{
            fontSize: 10,
            textTransform: "uppercase",
            letterSpacing: "0.05em",
            color: "#666",
          }}
        >
          Risks
        </span>
      </div>

      {/* Body */}
      <div style={{ flex: 1, overflow: "hidden" }}>
        {state === "compressed" ? (
          <>
            <div style={{ fontSize: 12, marginBottom: 4 }}>
              2 critical · 5 high · 8 medium
            </div>
            <div
              style={{
                fontSize: 11,
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
                color: "#444",
              }}
            >
              Biometric data in analytics-prod without PIA binding
            </div>
          </>
        ) : (
          <>
            <SectionHeader label="CRITICAL (2)" />
            <RiskRow
              title="Biometric data in analytics-prod without PIA binding"
              context="3 systems · detected 2d ago"
              astralis="Astralis: High exposure risk due to lack of consent framework"
              actions={["Review", "Resolve"]}
            />
            <RiskRow
              title="Unstructured PII in data-lake-01 without classification"
              context="1 system · detected 5d ago"
              astralis="Astralis: Classification gap flagged in last audit"
              actions={["Review"]}
            />

            <SectionHeader label="HIGH (5)" />
            <div style={{ marginBottom: 4 }}>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                }}
              >
                <div>
                  <span style={{ fontSize: 11, fontWeight: "bold" }}>
                    Consent purposes outdated in CMP
                  </span>
                  <span style={{ fontSize: 10, color: "#777", marginLeft: 6 }}>
                    3 systems
                  </span>
                </div>
                <ActionBtn label="Review" />
              </div>
            </div>
            <div style={{ fontSize: 10, color: "#aaa", marginTop: 4 }}>
              +4 more
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default RisksCard;
