import { AntTag as Tag, AntTagProps as TagProps } from "fidesui";

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
      | "caution";
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
    color: "alert",
    label: "Requires Input",
  },
};

interface RequestBadgeProps {
  status: keyof typeof statusPropMap;
}

const RequestStatusBadge = ({ status }: RequestBadgeProps) => (
  <Tag
    color={statusPropMap[status].color}
    className="w-[120px] justify-center"
    data-testid="request-status-badge"
  >
    {statusPropMap[status].label}
  </Tag>
);

export default RequestStatusBadge;
