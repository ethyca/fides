import { MenuProps } from "fidesui";

import { DiffStatus } from "~/types/api";

import { InfrastructureSystemBulkActionType } from "../constants";

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
}: GetBulkActionsMenuItemsConfig): MenuProps["items"] => {
  if (isIgnoredTab) {
    return [
      {
        key: InfrastructureSystemBulkActionType.ADD,
        label: "Add",
        onClick: () => onBulkAction(InfrastructureSystemBulkActionType.ADD),
        disabled: isBulkActionInProgress,
      },
      {
        key: InfrastructureSystemBulkActionType.RESTORE,
        label: "Restore",
        onClick: () => onBulkAction(InfrastructureSystemBulkActionType.RESTORE),
        disabled: isBulkActionInProgress,
      },
    ];
  }

  return [
    ...(allowIgnore
      ? [
          {
            key: InfrastructureSystemBulkActionType.IGNORE,
            label: "Ignore",
            onClick: () =>
              onBulkAction(InfrastructureSystemBulkActionType.IGNORE),
            disabled: isBulkActionInProgress,
          },
        ]
      : []),
    {
      key: InfrastructureSystemBulkActionType.ADD,
      label: "Add",
      onClick: () => onBulkAction(InfrastructureSystemBulkActionType.ADD),
      disabled: isBulkActionInProgress,
    },
  ];
};

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
