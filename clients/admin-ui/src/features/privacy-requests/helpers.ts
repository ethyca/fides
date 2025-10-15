import { PrivacyRequestStatus } from "~/types/api";

import { PrivacyRequestEntity } from "./types";

/**
 * Enum for bulk actions that can be performed on privacy requests
 */
export enum BulkActionType {
  APPROVE = "approve",
  DENY = "deny",
  FINALIZE = "finalize",
  DELETE = "delete",
}

/**
 * Determines which bulk actions are available for a given privacy request
 * based on its current status
 */
export const getAvailableActionsForRequest = (
  request: PrivacyRequestEntity,
): BulkActionType[] => {
  const availableActions: BulkActionType[] = [];

  // Approve and Deny are only available for pending requests
  if (request.status === PrivacyRequestStatus.PENDING) {
    availableActions.push(BulkActionType.APPROVE, BulkActionType.DENY);
  }

  // Finalize is only available for requests requiring manual finalization
  if (request.status === PrivacyRequestStatus.REQUIRES_MANUAL_FINALIZATION) {
    availableActions.push(BulkActionType.FINALIZE);
  }

  // Delete is always available (no status restriction)
  availableActions.push(BulkActionType.DELETE);

  return availableActions;
};

/**
 * Checks if a bulk action is supported by at least one of the selected requests
 */
export const isActionSupportedByRequests = (
  action: BulkActionType,
  requests: PrivacyRequestEntity[],
): boolean => {
  return requests.some((request) =>
    getAvailableActionsForRequest(request).includes(action),
  );
};
