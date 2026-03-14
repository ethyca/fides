import { MenuProps } from "fidesui";

import { DiffStatus } from "~/types/api";

import { InfrastructureSystemBulkActionType } from "../constants";

const { APPROVE, RESTORE, IGNORE } = InfrastructureSystemBulkActionType;

interface GetBulkActionsMenuItemsConfig {
  isIgnoredTab: boolean;
  allowIgnore: boolean;
  isBulkActionInProgress: boolean;
  onBulkAction: (action: InfrastructureSystemBulkActionType) => void;
}

export const getBulkActionsMenuItems = ({
  isIgnoredTab,
  allowIgnore,
  isBulkActionInProgress,
  onBulkAction,
}: GetBulkActionsMenuItemsConfig): MenuProps["items"] => [
  {
    key: APPROVE,
    label: "Approve",
    onClick: () => onBulkAction(APPROVE),
    disabled: isBulkActionInProgress,
  },
  ...(isIgnoredTab
    ? [
        {
          key: RESTORE,
          label: "Restore",
          onClick: () => onBulkAction(RESTORE),
          disabled: isBulkActionInProgress,
        },
      ]
    : []),
  ...(allowIgnore
    ? [
        {
          key: IGNORE,
          label: "Ignore",
          onClick: () => onBulkAction(IGNORE),
          disabled: isBulkActionInProgress,
        },
      ]
    : []),
];

export const shouldAllowIgnore = (
  activeDiffStatusFilters: DiffStatus[] | DiffStatus | undefined,
): boolean => {
  if (!activeDiffStatusFilters) {
    return false;
  }
  if (Array.isArray(activeDiffStatusFilters)) {
    return !activeDiffStatusFilters.includes(DiffStatus.MUTED);
  }
  return activeDiffStatusFilters !== DiffStatus.MUTED;
};

export const shouldAllowRestore = (
  activeDiffStatusFilters: DiffStatus[] | DiffStatus | undefined,
): boolean => {
  if (!activeDiffStatusFilters) {
    return false;
  }
  if (Array.isArray(activeDiffStatusFilters)) {
    return activeDiffStatusFilters.includes(DiffStatus.MUTED);
  }
  return activeDiffStatusFilters === DiffStatus.MUTED;
};
