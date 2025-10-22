import {
  AntMenuProps as MenuProps,
  AntMessage as message,
  AntModal as modal,
  Icons,
} from "fidesui";
import { useCallback, useEffect, useMemo } from "react";

import { pluralize } from "~/features/common/utils";

import {
  BulkActionType,
  getAvailableActionsForRequest,
  isActionSupportedByRequests,
} from "../../helpers";
import { useDenyPrivacyRequestModal } from "../../hooks/useDenyRequestModal";
import {
  useBulkApproveRequestMutation,
  useBulkDenyRequestMutation,
  useBulkSoftDeleteRequestMutation,
} from "../../privacy-requests.slice";
import { PrivacyRequestEntity } from "../../types";

type MessageInstance = ReturnType<typeof message.useMessage>[0];
type ModalInstance = ReturnType<typeof modal.useModal>[0];

interface UsePrivacyRequestBulkActionsProps {
  requests: PrivacyRequestEntity[];
  selectedIds: React.Key[];
  clearSelectedIds: () => void;
  messageApi: MessageInstance;
  modalApi: ModalInstance;
}

const ACTION_PAST_TENSE: Record<BulkActionType, string> = {
  [BulkActionType.APPROVE]: "approved",
  [BulkActionType.DENY]: "denied",
  [BulkActionType.DELETE]: "deleted",
};

const ACTION_CONFIG: Record<
  BulkActionType,
  { title: string; verb: string; okType?: "danger" }
> = {
  [BulkActionType.APPROVE]: {
    title: "Approve privacy requests",
    verb: "approve",
  },
  [BulkActionType.DENY]: {
    title: "Privacy request denial",
    verb: "deny",
  },
  [BulkActionType.DELETE]: {
    title: "Delete privacy requests",
    verb: "delete",
    okType: "danger",
  },
};

const formatResultMessage = (
  action: BulkActionType,
  successCount: number,
  failedCount: number,
): { type: "success" | "warning" | "error"; message: string } => {
  const actionLabel = action;
  const actionPastTense = ACTION_PAST_TENSE[action];

  if (failedCount > 0 && successCount > 0) {
    return {
      type: "warning",
      message: `Successfully ${actionPastTense} ${successCount} ${pluralize(successCount, "request", "requests")}. ${failedCount} ${pluralize(failedCount, "request", "requests")} failed.`,
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
    message: `Successfully ${actionPastTense} ${successCount} privacy ${pluralize(successCount, "request", "requests")}`,
  };
};

/**
 * Hook to manage bulk actions for privacy requests.
 * Returns menu items with disabled state and handles selection logic.
 */
export const usePrivacyRequestBulkActions = ({
  requests,
  selectedIds,
  clearSelectedIds,
  messageApi,
  modalApi,
}: UsePrivacyRequestBulkActionsProps) => {
  const selectedRequests = useMemo(
    () => requests.filter((request) => selectedIds.includes(request.id)),
    [requests, selectedIds],
  );

  // Clear selected requests when the data changes. eg. with pagination, filters or actions performed
  useEffect(() => {
    clearSelectedIds();
  }, [requests, clearSelectedIds]);

  // Mutation hooks for the actions
  const [bulkApproveRequest] = useBulkApproveRequestMutation();
  const [bulkDenyRequest] = useBulkDenyRequestMutation();
  const [bulkSoftDeleteRequest] = useBulkSoftDeleteRequestMutation();

  // Use the deny modal hook
  const { openDenyPrivacyRequestModal } = useDenyPrivacyRequestModal(
    modalApi as any,
  );

  const handleAction = useCallback(
    async (action: BulkActionType) => {
      const totalCount = selectedRequests.length;
      const supportedRequests = selectedRequests.filter((request) =>
        getAvailableActionsForRequest(request).includes(action),
      );
      const supportedCount = supportedRequests.length;
      const allSupported = supportedCount === totalCount;

      let content: string;
      if (allSupported) {
        content = `You are about to ${ACTION_CONFIG[action].verb} ${totalCount} privacy ${pluralize(totalCount, "request", "requests")}. Are you sure you want to continue?`;
      } else {
        content = `You have selected ${totalCount} ${pluralize(totalCount, "request", "requests")}, but only ${supportedCount} ${pluralize(supportedCount, "request", "requests")} can perform this action. If you continue, the bulk action will only be applied to ${supportedCount} ${pluralize(supportedCount, "request", "requests")}.`;
      }

      const requestIds = supportedRequests.map((r) => r.id);

      // Handle the action based on type
      if (action === BulkActionType.DENY) {
        // Special handling for deny action - open deny modal with warning
        const reason = await openDenyPrivacyRequestModal(content);
        if (!reason) {
          // User cancelled the modal, return early
          return;
        }

        const requestCount = requestIds.length;
        const hideLoading = messageApi.loading(
          `Executing bulk action on ${requestCount} privacy ${pluralize(requestCount, "request", "requests")}...`,
          0,
        );

        const result = await bulkDenyRequest({
          request_ids: requestIds,
          reason,
        });
        hideLoading();

        // Handle result
        if ("error" in result) {
          messageApi.error("Failed to deny requests. Please try again.", 5);
        } else if ("data" in result) {
          const successCount = result.data.succeeded?.length || 0;
          const failedCount = result.data.failed?.length || 0;
          const { type, message: msg } = formatResultMessage(
            action,
            successCount,
            failedCount,
          );
          messageApi[type](msg, 5);
        }
      } else {
        // Handle approve and delete actions with confirmation modal
        modalApi.confirm({
          title: ACTION_CONFIG[action].title,
          content,
          okText: "Continue",
          cancelText: "Cancel",
          okType: ACTION_CONFIG[action].okType,
          onOk: async () => {
            if (requestIds.length === 0) {
              return;
            }

            const requestCount = requestIds.length;
            const hideLoading = messageApi.loading(
              `Executing bulk action on ${requestCount} privacy ${pluralize(requestCount, "request", "requests")}...`,
              0,
            );

            let result;
            if (action === BulkActionType.APPROVE) {
              result = await bulkApproveRequest({ request_ids: requestIds });
            } else if (action === BulkActionType.DELETE) {
              result = await bulkSoftDeleteRequest({ request_ids: requestIds });
            }

            hideLoading();

            // Handle result
            if (!result) {
              return;
            }

            if ("error" in result) {
              const actionVerb =
                action === BulkActionType.APPROVE ? "approve" : "delete";
              messageApi.error(
                `Failed to ${actionVerb} requests. Please try again.`,
                5,
              );
            } else if ("data" in result) {
              const successCount = result.data.succeeded?.length || 0;
              const failedCount = result.data.failed?.length || 0;
              const { type, message: msg } = formatResultMessage(
                action,
                successCount,
                failedCount,
              );
              messageApi[type](msg, 5);
            }
          },
        });
      }
    },
    [
      selectedRequests,
      openDenyPrivacyRequestModal,
      bulkDenyRequest,
      bulkApproveRequest,
      bulkSoftDeleteRequest,
      messageApi,
      modalApi,
    ],
  );

  const bulkActionMenuItems: MenuProps["items"] = useMemo(() => {
    const canApprove = isActionSupportedByRequests(
      BulkActionType.APPROVE,
      selectedRequests,
    );
    const canDeny = isActionSupportedByRequests(
      BulkActionType.DENY,
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
        onClick: () => handleAction(BulkActionType.APPROVE),
        disabled: !canApprove,
      },
      {
        key: BulkActionType.DENY,
        label: "Deny",
        icon: <Icons.Close />,
        onClick: () => handleAction(BulkActionType.DENY),
        disabled: !canDeny,
      },
      {
        type: "divider",
      },
      {
        key: BulkActionType.DELETE,
        label: "Delete",
        icon: <Icons.TrashCan />,
        danger: true,
        onClick: () => handleAction(BulkActionType.DELETE),
        disabled: !canDelete,
      },
    ];
  }, [selectedRequests, handleAction]);

  return {
    bulkActionMenuItems,
  };
};
