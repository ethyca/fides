import { BadgeProps } from "fidesui";

import { BadgeCell, GroupCountBadgeCell } from "~/features/common/table/v2";
import { capitalize } from "~/features/common/utils";
import { PrivacyRequestStatus as PRIVACY_REQUEST_STATUS } from "~/types/api/models/PrivacyRequestStatus";

import { ActionType, PrivacyRequestStatus, Rule } from "./types";

export const statusPropMap: {
  [key in PrivacyRequestStatus]: BadgeProps & { label: string };
} = {
  approved: {
    colorScheme: "green",
    label: "Approved",
  },
  complete: {
    label: "Completed",
  },
  awaiting_email_send: {
    label: "Awaiting Email Send",
  },
  denied: {
    label: "Denied",
  },
  canceled: {
    label: "Canceled",
  },
  error: {
    colorScheme: "red",
    label: "Error",
  },
  in_processing: {
    colorScheme: "yellow",
    label: "In Progress",
  },
  paused: {
    label: "Paused",
  },
  pending: {
    colorScheme: "blue",
    label: "New",
  },
  identity_unverified: {
    colorScheme: "red",
    label: "Unverified",
  },
  requires_input: {
    colorScheme: "orange",
    label: "Requires Input",
  },
};

export const RequestStatusBadgeCell = ({
  value,
}: {
  value: keyof typeof statusPropMap;
}) => (
  <BadgeCell
    colorScheme={statusPropMap[value].colorScheme}
    value={statusPropMap[value].label}
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
    status === PRIVACY_REQUEST_STATUS.COMPLETE ||
    status === PRIVACY_REQUEST_STATUS.CANCELED ||
    status === PRIVACY_REQUEST_STATUS.DENIED ||
    status === PRIVACY_REQUEST_STATUS.IDENTITY_UNVERIFIED
  ) {
    return null;
  }

  const percentage = (100 * daysLeft) / timeframe;

  let colorScheme: string | undefined;
  if (percentage < 25) {
    colorScheme = "red";
  } else if (percentage >= 75) {
    colorScheme = "green";
  } else if (percentage >= 25) {
    colorScheme = "orange";
  }

  return (
    <BadgeCell
      value={includeText ? `${daysLeft} days left` : daysLeft.toString()}
      colorScheme={colorScheme}
    />
  );
};

/**
 * Extracts and returns the unique action types from the rules.
 * @param rules Array of Rule objects.
 */
export const getActionTypes = (rules: Rule[]): ActionType[] =>
  Array.from(
    new Set(
      rules
        .filter((d) => Object.values(ActionType).includes(d.action_type))
        .map((d) => d.action_type)
    )
  );

export const RequestTypeCell = ({ value }: { value: Rule[] }) => {
  const actionTypes = getActionTypes(value).map((action) => capitalize(action));
  return <GroupCountBadgeCell value={actionTypes} isDisplayAll />;
};
