import React from "react";

import { CardProps } from "./types";

interface FeedEvent {
  message: string;
  time: string;
}

const events: FeedEvent[] = [
  {
    message: "Helios classified 847 fields in Snowflake (via Helios)",
    time: "2m ago",
  },
  {
    message: "DSR-4521 completed, 12 systems processed",
    time: "8m ago",
  },
  {
    message: "Privacy assessment draft submitted for Salesforce CRM",
    time: "23m ago",
  },
  {
    message: "J. Smith updated consent purposes in CMP",
    time: "1h ago",
  },
  {
    message: "3 new unclassified systems detected in GCP",
    time: "2h ago",
  },
  {
    message: "Astralis flagged biometric data risk in analytics-prod",
    time: "3h ago",
  },
  {
    message: "DSR-4488 escalated: deadline in 2 days",
    time: "5h ago",
  },
  {
    message: "System data-lake-01 added to inventory",
    time: "8h ago",
  },
];

export const ActivityFeedCard = ({ state }: CardProps) => {
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
          Activity Feed
        </span>
        {state === "expanded" && (
          <span style={{ fontSize: 11, color: "#444" }}>
            <span style={{ borderBottom: "1px solid #333", paddingBottom: 1 }}>
              All
            </span>
            {" | "}
            <span>Human</span>
            {" | "}
            <span>System</span>
            {" | "}
            <span>Agent</span>
          </span>
        )}
      </div>

      {/* Body */}
      <div style={{ flex: 1, overflow: "hidden" }}>
        {state === "compressed" ? (
          <>
            <div style={{ fontSize: 12, marginBottom: 6 }}>47 events today</div>
            {events.slice(0, 2).map((ev) => (
              <div
                key={ev.message}
                style={{
                  fontSize: 11,
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                  color: "#444",
                  marginBottom: 3,
                }}
              >
                {ev.message} · {ev.time}
              </div>
            ))}
          </>
        ) : (
          <div>
            {events.map((ev) => (
              <div
                key={ev.message}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  marginBottom: 6,
                }}
              >
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    flex: 1,
                    overflow: "hidden",
                  }}
                >
                  {/* Avatar circle */}
                  <span
                    style={{
                      width: 8,
                      height: 8,
                      borderRadius: "50%",
                      background: "#ddd",
                      border: "1px solid #ccc",
                      display: "inline-block",
                      marginRight: 7,
                      flexShrink: 0,
                    }}
                  />
                  <span
                    style={{
                      fontSize: 11,
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                      color: "#333",
                    }}
                  >
                    {ev.message}
                  </span>
                </div>
                <span
                  style={{
                    fontSize: 10,
                    color: "#999",
                    marginLeft: 8,
                    flexShrink: 0,
                  }}
                >
                  {ev.time}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ActivityFeedCard;
