import { AntMenuProps as MenuProps, Icons } from "fidesui";
import { useCallback, useMemo, useState } from "react";

import {
  BulkActionType,
  getAvailableActionsForRequest,
  isActionSupportedByRequests,
} from "../helpers";
import { PrivacyRequestEntity } from "../types";

interface UsePrivacyRequestBulkActionsProps {
  selectedRequests: PrivacyRequestEntity[];
}

interface ConfirmationModalState {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
}

const ACTION_LABELS: Record<BulkActionType, string> = {
  [BulkActionType.APPROVE]: "approve",
  [BulkActionType.DENY]: "deny",
  [BulkActionType.FINALIZE]: "finalize",
  [BulkActionType.DELETE]: "delete",
};

/**
 * Hook to manage bulk actions for privacy requests.
 * Returns menu items with disabled state and confirmation modal state.
 */
export const usePrivacyRequestBulkActions = ({
  selectedRequests,
}: UsePrivacyRequestBulkActionsProps) => {
  const [pendingAction, setPendingAction] = useState<BulkActionType | null>(
    null,
  );

  const handleActionClick = useCallback((action: BulkActionType) => {
    setPendingAction(action);
  }, []);

  const handleCloseModal = useCallback(() => {
    setPendingAction(null);
  }, []);

  const handleConfirm = useCallback(() => {
    // TODO: Implement actual bulk action
    // eslint-disable-next-line no-console
    console.log(
      `Performing ${pendingAction} on ${selectedRequests.length} requests`,
    );
    setPendingAction(null);
  }, [pendingAction, selectedRequests.length]);

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
        onClick: () => handleActionClick(BulkActionType.APPROVE),
        disabled: !canApprove,
      },
      {
        key: BulkActionType.DENY,
        label: "Deny",
        icon: <Icons.Close />,
        onClick: () => handleActionClick(BulkActionType.DENY),
        disabled: !canDeny,
      },
      {
        type: "divider",
      },
      {
        key: BulkActionType.FINALIZE,
        label: "Finalize",
        icon: <Icons.Stamp />,
        onClick: () => handleActionClick(BulkActionType.FINALIZE),
        disabled: !canFinalize,
      },
      {
        key: BulkActionType.DELETE,
        label: "Delete",
        icon: <Icons.TrashCan />,
        danger: true,
        onClick: () => handleActionClick(BulkActionType.DELETE),
        disabled: !canDelete,
      },
    ];
  }, [selectedRequests, handleActionClick]);

  const confirmationModalState: ConfirmationModalState = useMemo(() => {
    const totalCount = selectedRequests.length;
    const actionLabel = pendingAction ? ACTION_LABELS[pendingAction] : "";

    // Count how many requests actually support this action
    const supportedCount = pendingAction
      ? selectedRequests.filter((request) =>
          getAvailableActionsForRequest(request).includes(pendingAction),
        ).length
      : 0;

    const allSupported = supportedCount === totalCount;

    // Generate title
    const title = `${actionLabel.charAt(0).toUpperCase() + actionLabel.slice(1)} privacy requests`;

    // Generate message based on whether all requests support the action
    let message: string;
    if (allSupported) {
      message = `You are about to ${actionLabel} ${totalCount} privacy ${totalCount === 1 ? "request" : "requests"}. Are you sure you want to continue?`;
    } else {
      message = `You have selected ${totalCount} ${totalCount === 1 ? "request" : "requests"}, but only ${supportedCount} ${supportedCount === 1 ? "request" : "requests"} can perform this action. If you continue, the bulk action will only be applied to ${supportedCount} ${supportedCount === 1 ? "request" : "requests"}.`;
    }

    return {
      isOpen: pendingAction !== null,
      onClose: handleCloseModal,
      onConfirm: handleConfirm,
      title,
      message,
    };
  }, [pendingAction, selectedRequests, handleCloseModal, handleConfirm]);

  return {
    bulkActionMenuItems,
    confirmationModalState,
  };
};
