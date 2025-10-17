import { PrivacyRequestStatus } from "~/types/api";

import { PrivacyRequestEntity } from "./types";

/**
 * Enum for bulk actions that can be performed on privacy requests
 */
export enum BulkActionType {
  APPROVE = "approve",
  DENY = "deny",
  DELETE = "delete",
}

/**
 * Maps each privacy request status to its available bulk actions
 * Using readonly mapping for type safety and performance
 */
const AVAILABLE_ACTIONS_BY_STATUS: Record<
  PrivacyRequestStatus,
  readonly BulkActionType[]
> = {
  [PrivacyRequestStatus.PENDING]: [
    BulkActionType.APPROVE,
    BulkActionType.DENY,
    BulkActionType.DELETE,
  ],
  [PrivacyRequestStatus.IDENTITY_UNVERIFIED]: [BulkActionType.DELETE],
  [PrivacyRequestStatus.REQUIRES_INPUT]: [BulkActionType.DELETE],
  [PrivacyRequestStatus.APPROVED]: [BulkActionType.DELETE],
  [PrivacyRequestStatus.DENIED]: [BulkActionType.DELETE],
  [PrivacyRequestStatus.IN_PROCESSING]: [BulkActionType.DELETE],
  [PrivacyRequestStatus.COMPLETE]: [BulkActionType.DELETE],
  [PrivacyRequestStatus.PAUSED]: [BulkActionType.DELETE],
  [PrivacyRequestStatus.AWAITING_EMAIL_SEND]: [BulkActionType.DELETE],
  [PrivacyRequestStatus.REQUIRES_MANUAL_FINALIZATION]: [BulkActionType.DELETE],
  [PrivacyRequestStatus.CANCELED]: [BulkActionType.DELETE],
  [PrivacyRequestStatus.ERROR]: [BulkActionType.DELETE],
} as const;

/**
 * Determines which bulk actions are available for a given privacy request
 * based on its current status
 */
export const getAvailableActionsForRequest = (
  request: PrivacyRequestEntity,
): readonly BulkActionType[] => {
  return AVAILABLE_ACTIONS_BY_STATUS[request.status];
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
