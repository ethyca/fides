import React from "react";

import { CardProps } from "./types";

const Tag = ({ label }: { label: string }) => (
  <span
    style={{
      border: "1px solid #ccc",
      fontSize: 10,
      padding: "1px 4px",
      marginLeft: 4,
    }}
  >
    {label}
  </span>
);

const ActionRowCompressed = ({
  title,
  tags,
}: {
  title: string;
  tags: string[];
}) => (
  <div
    style={{
      display: "flex",
      alignItems: "center",
      fontSize: 11,
      marginTop: 4,
      overflow: "hidden",
    }}
  >
    <span
      style={{
        flex: 1,
        overflow: "hidden",
        textOverflow: "ellipsis",
        whiteSpace: "nowrap",
      }}
    >
      {title}
    </span>
    <span style={{ flexShrink: 0, display: "flex" }}>
      {tags.map((t) => (
        <Tag key={t} label={t} />
      ))}
    </span>
  </div>
);

const ActionRowExpanded = ({
  title,
  context,
  tags,
}: {
  title: string;
  context: string;
  tags: string[];
}) => (
  <div style={{ marginTop: 5 }}>
    <div
      style={{
        display: "flex",
        alignItems: "flex-start",
        justifyContent: "space-between",
      }}
    >
      <span style={{ fontSize: 12, fontWeight: "bold", flex: 1 }}>{title}</span>
      <span style={{ flexShrink: 0, display: "flex" }}>
        {tags.map((t) => (
          <Tag key={t} label={t} />
        ))}
      </span>
    </div>
    <div style={{ fontSize: 10, color: "#777", marginTop: 1 }}>{context}</div>
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
      marginBottom: 2,
    }}
  >
    {label}
  </div>
);

export const PriorityActionsCard = ({ state }: CardProps) => {
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
          Priority Actions
        </span>
        {state === "expanded" && (
          <span style={{ display: "flex", gap: 4 }}>
            <span
              style={{
                border: "1px solid #ccc",
                fontSize: 10,
                padding: "1px 6px",
                cursor: "pointer",
              }}
            >
              Status ▾
            </span>
            <span
              style={{
                border: "1px solid #ccc",
                fontSize: 10,
                padding: "1px 6px",
                cursor: "pointer",
              }}
            >
              Severity ▾
            </span>
          </span>
        )}
      </div>

      {/* Body */}
      <div style={{ flex: 1, overflow: "hidden" }}>
        {state === "compressed" ? (
          <>
            <div style={{ fontSize: 13, fontWeight: "bold", marginBottom: 4 }}>
              7 actions · 2 overdue
            </div>
            <ActionRowCompressed
              title="Review 12 classifications in Salesforce"
              tags={["Critical", "2d overdue"]}
            />
            <ActionRowCompressed
              title="Resolve PIA for analytics-prod"
              tags={["Critical", "1d overdue"]}
            />
          </>
        ) : (
          <>
            <SectionHeader label="ACT NOW" />
            <ActionRowExpanded
              title="Review 12 classifications in Salesforce"
              context="Unclassified biometric fields require immediate review"
              tags={["Critical", "2d overdue"]}
            />
            <ActionRowExpanded
              title="Resolve PIA for analytics-prod"
              context="Privacy assessment missing required approvals"
              tags={["Critical", "1d overdue"]}
            />

            <SectionHeader label="THIS WEEK" />
            <ActionRowExpanded
              title="Update DSR handling for rectification"
              context="Workflow inconsistent across regions"
              tags={["High", "4d"]}
            />
            <ActionRowExpanded
              title="Review consent purposes in CMP"
              context="3 purposes lack clear language"
              tags={["High", "3d"]}
            />

            <SectionHeader label="WHEN YOU'RE READY" />
            <ActionRowExpanded
              title="Add system description for data-lake-01"
              context="Missing steward assignment"
              tags={["Medium", "7d"]}
            />
          </>
        )}
      </div>
    </div>
  );
};

export default PriorityActionsCard;
