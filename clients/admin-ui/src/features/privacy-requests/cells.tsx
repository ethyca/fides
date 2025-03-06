import { BadgeProps } from "fidesui";

import { BadgeCell, GroupCountBadgeCell } from "~/features/common/table/v2";
import { SubjectRequestActionTypeMap } from "~/features/privacy-requests/constants";
import { ActionType, PrivacyRequestStatus } from "~/types/api";

import { Rule } from "./types";

export const statusPropMap: {
  [key in PrivacyRequestStatus]: BadgeProps & { label: string };
} = {
  approved: {
    colorScheme: "success",
    label: "Approved",
  },
  complete: {
    label: "Completed",
    colorScheme: "success",
  },
  awaiting_email_send: {
    label: "Awaiting Email Send",
    colorScheme: "marble",
  },
  denied: {
    label: "Denied",
    colorScheme: "warning",
  },
  canceled: {
    label: "Canceled",
    colorScheme: "marble",
  },
  error: {
    label: "Error",
    colorScheme: "error",
  },
  in_processing: {
    label: "In Progress",
    colorScheme: "caution",
  },
  paused: {
    label: "Paused",
    colorScheme: "marble",
  },
  pending: {
    label: "New",
    colorScheme: "info",
  },
  identity_unverified: {
    label: "Unverified",
    colorScheme: "marble",
  },
  requires_input: {
    colorScheme: "alert",
    label: "Requires Input",
  },
};

export const RequestStatusBadgeCell = ({
  value,
}: {
  value: keyof typeof statusPropMap;
}) => (
  <BadgeCell
    color={statusPropMap[value].colorScheme}
    value={statusPropMap[value].label}
    data-testid="request-status-badge"
  />
);

export const RequestDaysLeftCell = ({
  daysLeft, // number of days remaining in the request
  timeframe = 45, // number of days in the policy (US = 45 days, EU = 30 days, etc.)
  status,
  includeText = false,
}: {
  daysLeft: number | undefined;
  timeframe?: number;
  status: PrivacyRequestStatus;
  includeText?: boolean;
}) => {
  if (
    daysLeft === undefined ||
    daysLeft === null ||
    status === PrivacyRequestStatus.COMPLETE ||
    status === PrivacyRequestStatus.CANCELED ||
    status === PrivacyRequestStatus.DENIED ||
    status === PrivacyRequestStatus.IDENTITY_UNVERIFIED
  ) {
    return null;
  }

  const percentage = (100 * daysLeft) / timeframe;

  let colorScheme: string | undefined;
  if (percentage < 25) {
    colorScheme = "error";
  } else if (percentage >= 75) {
    colorScheme = "success";
  } else if (percentage >= 25) {
    colorScheme = "warning";
  }

  return (
    <BadgeCell
      value={includeText ? `${daysLeft} days left` : daysLeft.toString()}
      color={colorScheme}
    />
  );
};

/**
 * Extracts and returns the unique action types from the rules.
 * @param rules Array of Rule objects.
 */
const getActionTypesFromRules = (rules: Rule[]): ActionType[] =>
  Array.from(
    new Set(
      rules
        .filter((rule) => Object.values(ActionType).includes(rule.action_type))
        .map((rule) => rule.action_type),
    ),
  );

export const RequestActionTypeCell = ({ value }: { value: Rule[] }) => {
  const actionTypes = getActionTypesFromRules(value).map((actionType) =>
    SubjectRequestActionTypeMap.get(actionType),
  );
  return (
    <GroupCountBadgeCell value={actionTypes} cellState={{ isExpanded: true }} />
  );
};
