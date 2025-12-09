import { AntMenuProps as MenuProps } from "fidesui";

import { DiffStatus } from "~/types/api";

interface GetBulkActionsMenuItemsConfig {
  isIgnoredTab: boolean;
  allowIgnore: boolean;
  isBulkActionInProgress: boolean;
  onBulkAction: (action: "add" | "ignore" | "restore") => void;
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
        key: "restore",
        label: "Restore",
        onClick: () => onBulkAction("restore"),
        disabled: isBulkActionInProgress,
      },
    ];
  }

  return [
    ...(allowIgnore
      ? [
          {
            key: "ignore",
            label: "Ignore",
            onClick: () => onBulkAction("ignore"),
            disabled: isBulkActionInProgress,
          },
        ]
      : []),
    {
      key: "add",
      label: "Add",
      onClick: () => onBulkAction("add"),
      disabled: isBulkActionInProgress,
    },
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
