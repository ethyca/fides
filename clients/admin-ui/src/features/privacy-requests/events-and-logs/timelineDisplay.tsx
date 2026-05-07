import { Avatar, Icons } from "fidesui";
import React from "react";

const ICON_SIZE = 20;

const renderIcon = (icon: React.ReactNode) => (
  <Avatar
    shape="square"
    size={ICON_SIZE}
    icon={icon}
    style={{ backgroundColor: "var(--fidesui-neutral-50)", color: "inherit" }}
  />
);

export const userTimelineIcon = renderIcon(<Icons.User />);

// Maps audit-log action statuses (AuditLogAction values) to a Carbon icon.
// For statuses we don't recognize we fall through to a generic system icon.
const auditStatusIcon = (status: string): React.ReactNode => {
  switch (status) {
    case "approved":
    case "pre_approval_eligible":
      return <Icons.CheckmarkOutline />;
    case "denied":
    case "pre_approval_not_eligible":
      return <Icons.Misuse />;
    case "policy_evaluated":
      return <Icons.Policy />;
    case "pre_approval_webhook_triggered":
      return <Icons.Flow />;
    case "email_sent":
      return <Icons.Notification />;
    case "finished":
      return <Icons.CheckmarkFilled />;
    default:
      return <Icons.Settings />;
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
    return renderIcon(<Icons.Flow />);
  }
  if (groupKey.startsWith("Request execution plan")) {
    return renderIcon(<Icons.Flow />);
  }
  return renderIcon(auditStatusIcon(status));
};

export const requestReceivedIcon = renderIcon(<Icons.Notification />);

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
