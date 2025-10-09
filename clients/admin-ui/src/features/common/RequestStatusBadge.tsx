import { AntTag as Tag, AntTagProps as TagProps } from "fidesui";
import React from "react";

import { PrivacyRequestStatus } from "~/types/api";

export const statusPropMap: {
  [key in PrivacyRequestStatus]: Omit<TagProps, "color"> & {
    color:
      | "success"
      | "marble"
      | "error"
      | "warning"
      | "info"
      | "alert"
      | "caution"
      | "minos";
    label?: string;
  };
} = {
  approved: {
    color: "success",
    label: "Approved",
  },
  complete: {
    color: "success",
    label: "Completed",
  },
  awaiting_email_send: {
    color: "marble",
    label: "Awaiting Email Send",
  },
  denied: {
    color: "warning",
    label: "Denied",
  },
  canceled: {
    color: "marble",
    label: "Canceled",
  },
  error: {
    color: "error",
    label: "Error",
  },
  in_processing: {
    color: "caution",
    label: "In Progress",
  },
  paused: {
    color: "marble",
    label: "Paused",
  },
  pending: {
    color: "info",
    label: "New",
  },
  identity_unverified: {
    color: "marble",
    label: "Unverified",
  },
  requires_input: {
    color: "minos",
    label: "Requires Input",
  },
  requires_manual_finalization: {
    color: "minos",
    label: "Requires Finalization",
  },
};

interface RequestBadgeProps {
  status: keyof typeof statusPropMap;
  style?: React.ComponentProps<typeof Tag>["style"];
}

const RequestStatusBadge = ({ status, style }: RequestBadgeProps) => (
  <Tag
    color={statusPropMap[status].color}
    className="justify-center"
    data-testid="request-status-badge"
    style={style}
  >
    {statusPropMap[status].label}
  </Tag>
);

export default RequestStatusBadge;
