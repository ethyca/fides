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
  useApproveRequestMutation,
  useBulkSoftDeleteRequestMutation,
  useDenyRequestMutation,
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
  const [approveRequest] = useApproveRequestMutation();
  const [denyRequest] = useDenyRequestMutation();
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

    // Filter requests that support this action
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
      `${actionLabel.charAt(0).toUpperCase() + actionLabel.slice(1)}ing ${requestIds.length} privacy ${requestIds.length === 1 ? "request" : "requests"}...`,
      0,
    );

    try {
      let successCount = 0;
      let failedCount = 0;

      // Execute the appropriate bulk action
      if (pendingAction === BulkActionType.DELETE) {
        // Delete has a true bulk endpoint
        const result = await bulkSoftDeleteRequest({
          request_ids: requestIds,
        });

        if ("error" in result) {
          throw new Error(`Failed to ${actionLabel} requests`);
        }

        if ("data" in result) {
          successCount = result.data.succeeded?.length || 0;
          failedCount = result.data.failed?.length || 0;
        }
      } else {
        // Approve and Deny: call the single-request mutation for each request
        const results = await Promise.allSettled(
          supportedRequests.map(async (request) => {
            if (pendingAction === BulkActionType.APPROVE) {
              return approveRequest(request);
            }
            if (pendingAction === BulkActionType.DENY) {
              return denyRequest({ id: request.id, reason: "" });
            }
            return null;
          }),
        );

        // Count successes and failures
        results.forEach((result) => {
          if (
            result.status === "fulfilled" &&
            result.value &&
            !("error" in result.value)
          ) {
            successCount += 1;
          } else {
            failedCount += 1;
          }
        });
      }

      hideLoading();

      // Show appropriate message based on results
      if (failedCount > 0 && successCount > 0) {
        messageApi.warning(
          `Successfully ${actionLabel}d ${successCount} ${successCount === 1 ? "request" : "requests"}. ${failedCount} ${failedCount === 1 ? "request" : "requests"} failed.`,
          5,
        );
      } else if (failedCount > 0) {
        messageApi.error(
          `Failed to ${actionLabel} ${failedCount} ${failedCount === 1 ? "request" : "requests"}.`,
          5,
        );
      } else {
        messageApi.success(
          `Successfully ${actionLabel}d ${successCount} privacy ${successCount === 1 ? "request" : "requests"}`,
          5,
        );
      }
    } catch (error) {
      hideLoading();
      messageApi.error(
        `Failed to ${actionLabel} requests. Please try again.`,
        5,
      );
    }

    setPendingAction(null);
  }, [
    pendingAction,
    selectedRequests,
    messageApi,
    approveRequest,
    denyRequest,
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
    const title = `${actionLabel.charAt(0).toUpperCase() + actionLabel.slice(1)} privacy requests`;

    // Generate message based on whether all requests support the action
    let modalMessage: string;
    if (allSupported) {
      modalMessage = `You are about to ${actionLabel} ${totalCount} privacy ${totalCount === 1 ? "request" : "requests"}. Are you sure you want to continue?`;
    } else {
      modalMessage = `You have selected ${totalCount} ${totalCount === 1 ? "request" : "requests"}, but only ${supportedCount} ${supportedCount === 1 ? "request" : "requests"} can perform this action. If you continue, the bulk action will only be applied to ${supportedCount} ${supportedCount === 1 ? "request" : "requests"}.`;
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
