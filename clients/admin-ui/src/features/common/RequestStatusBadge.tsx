import { Badge, BadgeProps } from "fidesui";

import { PrivacyRequestStatus } from "~/types/api";

export const statusPropMap: {
  [key in PrivacyRequestStatus]: BadgeProps & { label?: string };
} = {
  approved: {
    bg: "yellow.500",
    label: "Approved",
  },
  complete: {
    bg: "green.500",
    label: "Completed",
  },
  awaiting_email_send: {
    bg: "neutral.400",
    label: "Awaiting Email Send",
  },
  denied: {
    bg: "red.500",
    label: "Denied",
  },
  canceled: {
    bg: "red.600",
    label: "Canceled",
  },
  error: {
    bg: "red.800",
    label: "Error",
  },
  in_processing: {
    bg: "orange.500",
    label: "In Progress",
  },
  paused: {
    bg: "neutral.400",
    label: "Paused",
  },
  pending: {
    bg: "blue.400",
    label: "New",
  },
  identity_unverified: {
    bg: "red.400",
    label: "Unverified",
  },
  requires_input: {
    bg: "yellow.400",
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
    lineHeight="18px"
    textAlign="center"
    data-testid="request-status-badge"
  >
    {statusPropMap[status].label}
  </Badge>
);

export default RequestStatusBadge;
