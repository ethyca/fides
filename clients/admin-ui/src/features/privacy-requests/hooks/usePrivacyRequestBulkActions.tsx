import {
  AntMenuProps as MenuProps,
  AntMessage as message,
  Icons,
} from "fidesui";
import { useCallback, useMemo, useState } from "react";

import {
  BulkActionType,
  getAvailableActionsForRequest,
  isActionSupportedByRequests,
} from "../helpers";
import {
  useBulkApproveRequestMutation,
  useBulkDenyRequestMutation,
  useBulkSoftDeleteRequestMutation,
} from "../privacy-requests.slice";
import { PrivacyRequestEntity } from "../types";

type MessageInstance = ReturnType<typeof message.useMessage>[0];

interface UsePrivacyRequestBulkActionsProps {
  selectedRequests: PrivacyRequestEntity[];
  messageApi: MessageInstance;
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

const capitalize = (str: string) => str.charAt(0).toUpperCase() + str.slice(1);

const pluralize = (count: number, singular: string, plural: string) =>
  count === 1 ? singular : plural;

const formatResultMessage = (
  actionLabel: string,
  successCount: number,
  failedCount: number,
): { type: "success" | "warning" | "error"; message: string } => {
  if (failedCount > 0 && successCount > 0) {
    return {
      type: "warning",
      message: `Successfully ${actionLabel}d ${successCount} ${pluralize(successCount, "request", "requests")}. ${failedCount} ${pluralize(failedCount, "request", "requests")} failed.`,
    };
  }
  if (failedCount > 0) {
    return {
      type: "error",
      message: `Failed to ${actionLabel} ${failedCount} ${pluralize(failedCount, "request", "requests")}.`,
    };
  }
  return {
    type: "success",
    message: `Successfully ${actionLabel}d ${successCount} privacy ${pluralize(successCount, "request", "requests")}`,
  };
};

/**
 * Hook to manage bulk actions for privacy requests.
 * Returns menu items with disabled state and confirmation modal state.
 */
export const usePrivacyRequestBulkActions = ({
  selectedRequests,
  messageApi,
}: UsePrivacyRequestBulkActionsProps) => {
  const [pendingAction, setPendingAction] = useState<BulkActionType | null>(
    null,
  );

  // Mutation hooks
  const [bulkApproveRequest] = useBulkApproveRequestMutation();
  const [bulkDenyRequest] = useBulkDenyRequestMutation();
  const [bulkSoftDeleteRequest] = useBulkSoftDeleteRequestMutation();

  const handleActionClick = useCallback((action: BulkActionType) => {
    setPendingAction(action);
  }, []);

  const handleCloseModal = useCallback(() => {
    setPendingAction(null);
  }, []);

  const handleConfirm = useCallback(async () => {
    if (!pendingAction) {
      return;
    }

    const supportedRequests = selectedRequests.filter((request) =>
      getAvailableActionsForRequest(request).includes(pendingAction),
    );

    const requestIds = supportedRequests.map((r) => r.id);
    if (requestIds.length === 0) {
      setPendingAction(null);
      return;
    }

    const actionLabel = ACTION_LABELS[pendingAction];
    const hideLoading = messageApi.loading(
      `${capitalize(actionLabel)}ing ${requestIds.length} privacy ${pluralize(requestIds.length, "request", "requests")}...`,
      0,
    );

    // Execute appropriate bulk mutation
    let result;
    switch (pendingAction) {
      case BulkActionType.APPROVE:
        result = await bulkApproveRequest({ request_ids: requestIds });
        break;
      case BulkActionType.DENY:
        result = await bulkDenyRequest({ request_ids: requestIds, reason: "" });
        break;
      case BulkActionType.DELETE:
        result = await bulkSoftDeleteRequest({ request_ids: requestIds });
        break;
      default:
        hideLoading();
        setPendingAction(null);
        return;
    }

    hideLoading();

    // Handle result
    if ("error" in result) {
      messageApi.error(
        `Failed to ${actionLabel} requests. Please try again.`,
        5,
      );
    } else if ("data" in result) {
      const successCount = result.data.succeeded?.length || 0;
      const failedCount = result.data.failed?.length || 0;
      const { type, message: msg } = formatResultMessage(
        actionLabel,
        successCount,
        failedCount,
      );
      messageApi[type](msg, 5);
    }

    setPendingAction(null);
  }, [
    pendingAction,
    selectedRequests,
    messageApi,
    bulkApproveRequest,
    bulkDenyRequest,
    bulkSoftDeleteRequest,
  ]);

  const bulkActionMenuItems: MenuProps["items"] = useMemo(() => {
    const canApprove = isActionSupportedByRequests(
      BulkActionType.APPROVE,
      selectedRequests,
    );
    const canDeny = isActionSupportedByRequests(
      BulkActionType.DENY,
      selectedRequests,
    );
    // const canFinalize = isActionSupportedByRequests(
    //   BulkActionType.FINALIZE,
    //   selectedRequests,
    // );
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
      // To be added when bulk endpoint is available for finalize
      // {
      //   key: BulkActionType.FINALIZE,
      //   label: "Finalize",
      //   icon: <Icons.Stamp />,
      //   onClick: () => handleActionClick(BulkActionType.FINALIZE),
      //   disabled: !canFinalize,
      // },
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
    const title = `${capitalize(actionLabel)} privacy requests`;

    // Generate message based on whether all requests support the action
    let modalMessage: string;
    if (allSupported) {
      modalMessage = `You are about to ${actionLabel} ${totalCount} privacy ${pluralize(totalCount, "request", "requests")}. Are you sure you want to continue?`;
    } else {
      modalMessage = `You have selected ${totalCount} ${pluralize(totalCount, "request", "requests")}, but only ${supportedCount} ${pluralize(supportedCount, "request", "requests")} can perform this action. If you continue, the bulk action will only be applied to ${supportedCount} ${pluralize(supportedCount, "request", "requests")}.`;
    }

    return {
      isOpen: pendingAction !== null,
      onClose: handleCloseModal,
      onConfirm: handleConfirm,
      title,
      message: modalMessage,
    };
  }, [pendingAction, selectedRequests, handleCloseModal, handleConfirm]);

  return {
    bulkActionMenuItems,
    confirmationModalState,
  };
};
