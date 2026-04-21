import React from "react";

import { CardProps } from "./types";

const MetricRow = ({
  label,
  value,
}: {
  label: string;
  value: React.ReactNode;
}) => (
  <div
    style={{
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center",
      fontSize: 12,
      marginBottom: 5,
    }}
  >
    <span style={{ color: "#444" }}>{label}</span>
    <span style={{ fontWeight: "bold", color: "#222" }}>{value}</span>
  </div>
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

export const AiAgentActivityCard = ({ state }: CardProps) => {
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
          AI Agent Activity
        </span>
      </div>

      {/* Body */}
      <div style={{ flex: 1, overflow: "hidden" }}>
        {state === "compressed" ? (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              fontSize: 12,
              color: "#333",
            }}
          >
            <span
              style={{
                width: 6,
                height: 6,
                borderRadius: "50%",
                background: "#888",
                display: "inline-block",
                marginRight: 7,
                flexShrink: 0,
              }}
            />
            3 active PIA conversations
          </div>
        ) : (
          <>
            <MetricRow
              label="Active Conversations"
              value={
                <span>
                  3{" "}
                  <span
                    style={{
                      display: "inline-block",
                      width: 6,
                      height: 6,
                      borderRadius: "50%",
                      background: "#888",
                      marginLeft: 3,
                      verticalAlign: "middle",
                    }}
                  />
                </span>
              }
            />
            <MetricRow label="Awaiting Response" value="7" />
            <MetricRow label="Completed Assessments" value="24" />
            <MetricRow label="Risks Identified" value="2 ⚠" />

            <div style={{ borderTop: "1px solid #eee", margin: "8px 0" }} />

            <SectionHeader label="Engaged Stewards" />
            {[
              "J. Smith — Salesforce CRM assessment · step 3/5",
              "A. Lee — BigQuery PIA · awaiting legal sign-off",
              "M. Chen — Snowflake prod classification review",
            ].map((line) => (
              <div
                key={line}
                style={{ fontSize: 11, color: "#444", marginBottom: 4 }}
              >
                {line}
              </div>
            ))}

            <SectionHeader label="Systems Under Assessment" />
            <div style={{ fontSize: 11, color: "#444" }}>
              analytics-prod, data-lake-01, Snowflake-prod
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default AiAgentActivityCard;
