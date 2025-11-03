import {
  AntTag as Tag,
  AntTagProps as TagProps,
  CUSTOM_TAG_COLOR,
} from "fidesui";

import { PrivacyRequestStatus } from "~/types/api";

export const statusPropMap: {
  [key in PrivacyRequestStatus]: Omit<TagProps, "color"> & {
    color: CUSTOM_TAG_COLOR;
    label?: string;
  };
} = {
  approved: {
    color: CUSTOM_TAG_COLOR.SUCCESS,
    label: "Approved",
  },
  complete: {
    color: CUSTOM_TAG_COLOR.SUCCESS,
    label: "Completed",
  },
  awaiting_email_send: {
    color: CUSTOM_TAG_COLOR.MARBLE,
    label: "Awaiting Email Send",
  },
  denied: {
    color: CUSTOM_TAG_COLOR.WARNING,
    label: "Denied",
  },
  canceled: {
    color: CUSTOM_TAG_COLOR.MARBLE,
    label: "Canceled",
  },
  error: {
    color: CUSTOM_TAG_COLOR.ERROR,
    label: "Error",
  },
  in_processing: {
    color: CUSTOM_TAG_COLOR.CAUTION,
    label: "In Progress",
  },
  paused: {
    color: CUSTOM_TAG_COLOR.MARBLE,
    label: "Paused",
  },
  pending: {
    color: CUSTOM_TAG_COLOR.INFO,
    label: "New",
  },
  identity_unverified: {
    color: CUSTOM_TAG_COLOR.MARBLE,
    label: "Unverified",
  },
  requires_input: {
    color: CUSTOM_TAG_COLOR.MINOS,
    label: "Requires Input",
  },
  requires_manual_finalization: {
    color: CUSTOM_TAG_COLOR.MINOS,
    label: "Requires Finalization",
  },
};

interface RequestBadgeProps {
  status: keyof typeof statusPropMap;
}

const RequestStatusBadge = ({ status }: RequestBadgeProps) => (
  <Tag
    color={statusPropMap[status].color}
    className="justify-center"
    data-testid="request-status-badge"
  >
    {statusPropMap[status].label}
  </Tag>
);

export default RequestStatusBadge;
