import { CUSTOM_TAG_COLOR } from "fidesui";

import { BadgeCell, GroupCountBadgeCell } from "~/features/common/table/v2";
import { SubjectRequestActionTypeMap } from "~/features/privacy-requests/constants";
import { ActionType, PrivacyRequestStatus } from "~/types/api";

import { Rule } from "./types";

export const statusPropMap: {
  [key in PrivacyRequestStatus]: {
    label: string;
    colorScheme: CUSTOM_TAG_COLOR;
  };
} = {
  approved: {
    colorScheme: CUSTOM_TAG_COLOR.SUCCESS,
    label: "Approved",
  },
  complete: {
    label: "Completed",
    colorScheme: CUSTOM_TAG_COLOR.SUCCESS,
  },
  awaiting_email_send: {
    label: "Awaiting Email Send",
    colorScheme: CUSTOM_TAG_COLOR.MARBLE,
  },
  denied: {
    label: "Denied",
    colorScheme: CUSTOM_TAG_COLOR.WARNING,
  },
  canceled: {
    label: "Canceled",
    colorScheme: CUSTOM_TAG_COLOR.MARBLE,
  },
  error: {
    label: "Error",
    colorScheme: CUSTOM_TAG_COLOR.ERROR,
  },
  in_processing: {
    label: "In Progress",
    colorScheme: CUSTOM_TAG_COLOR.CAUTION,
  },
  paused: {
    label: "Paused",
    colorScheme: CUSTOM_TAG_COLOR.MARBLE,
  },
  pending: {
    label: "New",
    colorScheme: CUSTOM_TAG_COLOR.INFO,
  },
  identity_unverified: {
    label: "Unverified",
    colorScheme: CUSTOM_TAG_COLOR.MARBLE,
  },
  requires_input: {
    colorScheme: CUSTOM_TAG_COLOR.MINOS,
    label: "Requires Input",
  },
  requires_manual_finalization: {
    colorScheme: CUSTOM_TAG_COLOR.MINOS,
    label: "Requires Finalization",
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

  let colorScheme: CUSTOM_TAG_COLOR | undefined;
  if (percentage < 25) {
    colorScheme = CUSTOM_TAG_COLOR.ERROR;
  } else if (percentage >= 75) {
    colorScheme = CUSTOM_TAG_COLOR.SUCCESS;
  } else if (percentage >= 25) {
    colorScheme = CUSTOM_TAG_COLOR.WARNING;
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
