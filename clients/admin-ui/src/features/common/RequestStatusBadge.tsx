import { Badge } from "@fidesui/react";
import { PrivacyRequestStatus } from "privacy-requests/types";
import { ComponentProps } from "react";

export const statusPropMap: {
  [key in PrivacyRequestStatus]: ComponentProps<typeof Badge>;
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
    bg: "gray.400",
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
    bg: "gray.400",
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

const RequestStatusBadge: React.FC<RequestBadgeProps> = ({ status }) => (
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
