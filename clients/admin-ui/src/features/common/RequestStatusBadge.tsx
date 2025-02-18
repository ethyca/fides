import { AntTag as Tag, AntTagProps as TagProps } from "fidesui";

import { PrivacyRequestStatus } from "~/types/api";

export const statusPropMap: {
  [key in PrivacyRequestStatus]: Omit<TagProps, "color"> & {
    color: "success" | "marble" | "error" | "warning" | "info" | "alert";
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
    color: "error",
    label: "Denied",
  },
  canceled: {
    color: "marble",
    label: "Canceled",
  },
  error: {
    color: "warning",
    label: "Error",
  },
  in_processing: {
    color: "warning",
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
    className="w-full min-w-[120px] text-center leading-[22px]"
    data-testid="request-status-badge"
  >
    <span className="flex items-center justify-center">
      {statusPropMap[status].label}
    </span>
  </Tag>
);

export default RequestStatusBadge;
