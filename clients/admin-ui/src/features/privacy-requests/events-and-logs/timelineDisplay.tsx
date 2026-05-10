import { Avatar, Icons } from "fidesui";
import React from "react";

const ICON_SIZE = 24;

const renderIcon = (
  icon: React.ReactNode,
  style?: React.CSSProperties,
) => (
  <Avatar
    shape="square"
    size={ICON_SIZE}
    icon={icon}
    style={{
      backgroundColor: "var(--fidesui-neutral-50)",
      color: "inherit",
      ...style,
    }}
  />
);

export const userTimelineIcon = renderIcon(<Icons.User />, {
  backgroundColor: "var(--fidesui-brand-marble)",
  color: "var(--fidesui-brand-minos)",
});

type AuditStatusGlyph = {
  icon: React.ReactNode;
  style?: React.CSSProperties;
};

// Maps audit-log action statuses (AuditLogAction values) to a Carbon icon.
// For statuses we don't recognize we fall through to a generic system icon.
const auditStatusIcon = (status: string): AuditStatusGlyph => {
  switch (status) {
    case "approved":
    case "pre_approval_eligible":
      return {
        icon: <Icons.Checkmark />,
        style: {
          backgroundColor: "var(--fidesui-brand-olive)",
          color: "var(--fidesui-brand-corinth)",
        },
      };
    case "denied":
    case "pre_approval_not_eligible":
      return { icon: <Icons.Misuse /> };
    case "policy_evaluated":
      return {
        icon: <Icons.FlowData />,
        style: {
          backgroundColor: "var(--fidesui-brand-sandstone)",
          color: "var(--fidesui-brand-minos)",
        },
      };
    case "pre_approval_webhook_triggered":
      return { icon: <Icons.Flow /> };
    case "email_sent":
      return { icon: <Icons.Notification /> };
    case "finished":
      return { icon: <Icons.CheckmarkFilled /> };
    default:
      return { icon: <Icons.Settings /> };
  }
};

// Builds an icon for execution-log groups that are not tied to an integration
// (e.g. audit log rows like "Request approved", or graph events like
// "Dataset traversal" / "Dataset filtering" / "Dataset reference validation").
export const systemEventIcon = (
  groupKey: string,
  status: string,
): React.ReactNode => {
  if (groupKey.startsWith("Dataset")) {
    return renderIcon(<Icons.Process />);
  }
  if (groupKey.startsWith("Request execution plan")) {
    return renderIcon(<Icons.Flow />);
  }
  const { icon, style } = auditStatusIcon(status);
  return renderIcon(icon, style);
};

export const requestReceivedIcon = renderIcon(<Icons.ArrowRight />, {
  backgroundColor: "var(--fidesui-brand-terracotta)",
  color: "var(--fidesui-brand-corinth)",
});

// Humanize a snake_case / kebab-case identifier. Used as a fallback when we
// don't have a friendlier display name (e.g. an integration without a `name`
// or a system event that wasn't mapped on the backend).
export const humanizeIdentifier = (value: string): string => {
  const cleaned = value.replace(/[_-]+/g, " ").replace(/\s+/g, " ").trim();
  if (!cleaned) {
    return value;
  }
  return cleaned.charAt(0).toUpperCase() + cleaned.slice(1);
};
