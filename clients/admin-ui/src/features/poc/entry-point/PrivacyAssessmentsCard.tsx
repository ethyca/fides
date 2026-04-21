import React from "react";

import { CardProps } from "./types";

const colWidths = {
  assessment: 130,
  system: 110,
  steward: 60,
  status: 90,
  days: 40,
  lastInteraction: 130,
};

const StatusBadge = ({ label }: { label: string }) => (
  <span
    style={{
      border: "1px solid #ccc",
      fontSize: 10,
      padding: "1px 4px",
      whiteSpace: "nowrap",
    }}
  >
    {label}
  </span>
);

interface AssessmentRow {
  assessment: string;
  system: string;
  steward: string;
  status: string;
  days: string;
  lastInteraction: string;
}

const rows: AssessmentRow[] = [
  {
    assessment: "DPIA: Salesforce CRM",
    system: "SF",
    steward: "J. Smith",
    status: "In Progress",
    days: "12d",
    lastInteraction: "Awaiting steward · 3d",
  },
  {
    assessment: "PIA: BigQuery analytics",
    system: "BQ",
    steward: "A. Lee",
    status: "Awaiting Legal",
    days: "8d",
    lastInteraction: "Sent to legal review",
  },
  {
    assessment: "DPIA: data-lake-01",
    system: "DL",
    steward: "—",
    status: "Overdue",
    days: "21d",
    lastInteraction: "No response in 14d",
  },
  {
    assessment: "PIA: Snowflake prod",
    system: "SF",
    steward: "M. Chen",
    status: "In Progress",
    days: "4d",
    lastInteraction: "Astralis completed draft",
  },
];

export const PrivacyAssessmentsCard = ({ state }: CardProps) => {
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
          Privacy Assessments
        </span>
        {state === "expanded" && (
          <span
            style={{
              fontSize: 11,
              textDecoration: "underline",
              cursor: "pointer",
              color: "#333",
            }}
          >
            Start new assessment →
          </span>
        )}
      </div>

      {/* Body */}
      <div style={{ flex: 1, overflow: "hidden" }}>
        {state === "compressed" ? (
          <div style={{ fontSize: 12, color: "#333" }}>
            4 in progress · 2 awaiting legal · 1 overdue
          </div>
        ) : (
          <div style={{ fontSize: 11 }}>
            {/* Header row */}
            <div
              style={{
                display: "flex",
                fontSize: 10,
                textTransform: "uppercase",
                color: "#999",
                letterSpacing: "0.04em",
                marginBottom: 4,
                borderBottom: "1px solid #eee",
                paddingBottom: 3,
              }}
            >
              <span style={{ minWidth: colWidths.assessment }}>Assessment</span>
              <span style={{ minWidth: colWidths.system }}>System</span>
              <span style={{ minWidth: colWidths.steward }}>Steward</span>
              <span style={{ minWidth: colWidths.status }}>Status</span>
              <span style={{ minWidth: colWidths.days }}>Days</span>
              <span style={{ minWidth: colWidths.lastInteraction }}>
                Last Interaction
              </span>
            </div>

            {/* Data rows */}
            {rows.map((row) => (
              <div
                key={row.assessment}
                style={{
                  display: "flex",
                  alignItems: "center",
                  paddingTop: 4,
                  paddingBottom: 4,
                  borderBottom: "1px solid #f5f5f5",
                }}
              >
                <span
                  style={{
                    minWidth: colWidths.assessment,
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                >
                  {row.assessment}
                </span>
                <span style={{ minWidth: colWidths.system, color: "#555" }}>
                  {row.system}
                </span>
                <span style={{ minWidth: colWidths.steward, color: "#555" }}>
                  {row.steward}
                </span>
                <span style={{ minWidth: colWidths.status }}>
                  <StatusBadge label={row.status} />
                </span>
                <span style={{ minWidth: colWidths.days, color: "#555" }}>
                  {row.days}
                </span>
                <span
                  style={{
                    minWidth: colWidths.lastInteraction,
                    color: "#777",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                >
                  {row.lastInteraction}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default PrivacyAssessmentsCard;
