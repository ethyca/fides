import { AntMenuProps as MenuProps, Icons } from "fidesui";
import { useMemo } from "react";

import { BulkActionType, isActionSupportedByRequests } from "../helpers";
import { PrivacyRequestEntity } from "../types";

interface UsePrivacyRequestBulkActionsProps {
  selectedRequests: PrivacyRequestEntity[];
  onApprove: () => void;
  onDeny: () => void;
  onFinalize: () => void;
  onDelete: () => void;
}

/**
 * Hook to manage bulk actions for privacy requests.
 * Returns menu items with disabled state based on whether any selected requests support the action.
 */
export const usePrivacyRequestBulkActions = ({
  selectedRequests,
  onApprove,
  onDeny,
  onFinalize,
  onDelete,
}: UsePrivacyRequestBulkActionsProps) => {
  const bulkActionMenuItems: MenuProps["items"] = useMemo(() => {
    const canApprove = isActionSupportedByRequests(
      BulkActionType.APPROVE,
      selectedRequests,
    );
    const canDeny = isActionSupportedByRequests(
      BulkActionType.DENY,
      selectedRequests,
    );
    const canFinalize = isActionSupportedByRequests(
      BulkActionType.FINALIZE,
      selectedRequests,
    );
    const canDelete = isActionSupportedByRequests(
      BulkActionType.DELETE,
      selectedRequests,
    );

    return [
      {
        key: BulkActionType.APPROVE,
        label: "Approve",
        icon: <Icons.Checkmark />,
        onClick: onApprove,
        disabled: !canApprove,
      },
      {
        key: BulkActionType.DENY,
        label: "Deny",
        icon: <Icons.Close />,
        onClick: onDeny,
        disabled: !canDeny,
      },
      {
        type: "divider",
      },
      {
        key: BulkActionType.FINALIZE,
        label: "Finalize",
        icon: <Icons.Stamp />,
        onClick: onFinalize,
        disabled: !canFinalize,
      },
      {
        key: BulkActionType.DELETE,
        label: "Delete",
        icon: <Icons.TrashCan />,
        danger: true,
        onClick: onDelete,
        disabled: !canDelete,
      },
    ];
  }, [selectedRequests, onApprove, onDeny, onFinalize, onDelete]);

  return {
    bulkActionMenuItems,
  };
};
