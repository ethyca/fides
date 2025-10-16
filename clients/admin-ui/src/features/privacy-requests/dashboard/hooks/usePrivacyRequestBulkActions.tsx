import {
  AntMenuProps as MenuProps,
  AntMessage as message,
  Icons,
} from "fidesui";
import { useCallback, useEffect, useMemo } from "react";

import {
  BulkActionType,
  getAvailableActionsForRequest,
  isActionSupportedByRequests,
} from "../../helpers";
import {
  useBulkApproveRequestMutation,
  useBulkDenyRequestMutation,
  useBulkSoftDeleteRequestMutation,
} from "../../privacy-requests.slice";
import { PrivacyRequestEntity } from "../../types";

type MessageInstance = ReturnType<typeof message.useMessage>[0];

interface UsePrivacyRequestBulkActionsProps {
  requests: PrivacyRequestEntity[];
  selectedIds: React.Key[];
  clearSelectedIds: () => void;
  messageApi: MessageInstance;
}

const ACTION_LABELS: Record<BulkActionType, string> = {
  [BulkActionType.APPROVE]: "approve",
  [BulkActionType.DENY]: "deny",
  [BulkActionType.DELETE]: "delete",
};

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
 * Returns menu items with disabled state and handles selection logic.
 */
export const usePrivacyRequestBulkActions = ({
  requests,
  selectedIds,
  clearSelectedIds,
  messageApi,
}: UsePrivacyRequestBulkActionsProps) => {
  const selectedRequests = useMemo(
    () => requests.filter((request) => selectedIds.includes(request.id)),
    [requests, selectedIds],
  );

  // Clear selected requests when the data changes
  // eg. with pagination, filters or actions performed
  useEffect(() => {
    clearSelectedIds();
  }, [requests, clearSelectedIds]);

  // Mutation hooks for the actions
  const [bulkApproveRequest] = useBulkApproveRequestMutation();
  const [bulkDenyRequest] = useBulkDenyRequestMutation();
  const [bulkSoftDeleteRequest] = useBulkSoftDeleteRequestMutation();

  const handleActionClick = useCallback(
    async (action: BulkActionType) => {
      // Filter out requests that don't support the action that was chosen
      // We will later add a warning modal for this
      const supportedRequests = selectedRequests.filter((request) =>
        getAvailableActionsForRequest(request).includes(action),
      );

      const requestIds = supportedRequests.map((r) => r.id);
      const requestCount = requestIds.length;

      const actionLabel = ACTION_LABELS[action];
      const hideLoading = messageApi.loading(
        `Executing bulk action on ${requestCount} privacy ${pluralize(requestCount, "request", "requests")}...`,
        0,
      );

      // Execute appropriate bulk mutation
      let result;
      switch (action) {
        case BulkActionType.APPROVE:
          result = await bulkApproveRequest({ request_ids: requestIds });
          break;
        case BulkActionType.DENY:
          result = await bulkDenyRequest({
            request_ids: requestIds,
            reason: "",
          });
          break;
        case BulkActionType.DELETE:
          result = await bulkSoftDeleteRequest({ request_ids: requestIds });
          break;
        default:
          hideLoading();
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
    },
    [
      selectedRequests,
      messageApi,
      bulkApproveRequest,
      bulkDenyRequest,
      bulkSoftDeleteRequest,
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
        key: BulkActionType.DELETE,
        label: "Delete",
        icon: <Icons.TrashCan />,
        danger: true,
        onClick: () => handleActionClick(BulkActionType.DELETE),
        disabled: !canDelete,
      },
    ];
  }, [selectedRequests, handleActionClick]);

  return {
    bulkActionMenuItems,
  };
};
