import { Badge, BadgeProps, Spinner } from "fidesui";

import { PrivacyRequestStatus } from "~/types/api";

export const statusPropMap: {
  [key in PrivacyRequestStatus]: BadgeProps & { label?: string };
} = {
  approved: {
    bg: "warn.500",
    label: "Approved",
  },
  complete: {
    bg: "success.500",
    label: "Completed",
  },
  awaiting_email_send: {
    bg: "gray.400",
    label: "Awaiting Email Send",
  },
  denied: {
    bg: "error.500",
    label: "Denied",
  },
  canceled: {
    bg: "error.600",
    label: "Canceled",
  },
  error: {
    bg: "error.800",
    label: "Error",
  },
  in_processing: {
    bg: "warn.500",
    label: "In Progress",
  },
  paused: {
    bg: "gray.400",
    label: "Paused",
  },
  pending: {
    bg: "info.400",
    label: "New",
  },
  identity_unverified: {
    bg: "error.400",
    label: "Unverified",
  },
  requires_input: {
    bg: "warn.400",
    label: "Requires Input",
  },
};

interface RequestBadgeProps {
  status: keyof typeof statusPropMap;
}

const RequestStatusBadge = ({ status }: RequestBadgeProps) => (
  <Badge
    color="white"
    bg={statusPropMap[status].bg}
    width="100%"
    minWidth="120px"
    lineHeight="22px"
    textAlign="center"
    data-testid="request-status-badge"
  >
    <span
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      {statusPropMap[status].label}
      {status === PrivacyRequestStatus.IN_PROCESSING && (
        <Spinner size="xs" color="white" ml={2} />
      )}
    </span>
  </Badge>
);

export default RequestStatusBadge;
