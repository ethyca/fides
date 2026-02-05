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
        key: InfrastructureSystemBulkActionType.RESTORE,
        label: "Restore",
        onClick: () => onBulkAction(InfrastructureSystemBulkActionType.RESTORE),
        disabled: isBulkActionInProgress,
      },
    ];
  }

  return [
    {
      key: InfrastructureSystemBulkActionType.ADD,
      label: "Add",
      onClick: () => onBulkAction(InfrastructureSystemBulkActionType.ADD),
      disabled: isBulkActionInProgress,
    },
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
  ];
};

export const shouldAllowIgnore = (activeParams: {
  diff_status?: DiffStatus | DiffStatus[] | null;
}): boolean => {
  return (
    !!activeParams.diff_status &&
    !activeParams.diff_status.includes(DiffStatus.MUTED)
  );
};
