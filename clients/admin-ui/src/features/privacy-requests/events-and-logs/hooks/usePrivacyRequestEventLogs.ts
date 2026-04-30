import {
  hasAwaitingProcessing,
  hasPolling,
  hasSkippedEntry,
  hasUnresolvedError,
} from "~/features/privacy-requests/events-and-logs/helpers";
import {
  ActivityTimelineItem,
  ActivityTimelineItemTypeEnum,
  ExecutionLogStatus,
  PrivacyRequestResults,
} from "~/features/privacy-requests/types";

// Dataset name the backend writes on every ExecutionLog produced by duplicate
// detection. Must stay in sync with DUPLICATE_DETECTION_DATASET_NAME defined in
// src/fides/api/service/privacy_request/duplication_detection.py.
export const DUPLICATE_DETECTION_DATASET_NAME = "Duplicate Request Detection";

/**
 * Hook for processing privacy request event logs.
 *
 * When taskStatusByDataset is provided, task statuses are read directly from
 * the RequestTask.status field (via the backend) instead of being inferred
 * from execution log history. This avoids incorrect status display when logs
 * are truncated by the embedded log limit.
 */
export const usePrivacyRequestEventLogs = (
  results?: PrivacyRequestResults,
  taskStatusByDataset?: Record<string, string>,
) => {
  // Determine if results are loading
  const isLoading = !results;

  // Map from source events to ActivityTimelineItems
  const eventItems: ActivityTimelineItem[] = !results
    ? []
    : Object.entries(results).map(([key, logs]) => {
        const taskStatus = taskStatusByDataset?.[key];

        // When we have an authoritative task status from the backend, use it
        // directly. Otherwise fall back to scanning execution logs (needed for
        // audit-log entries like "Request approved" which have no RequestTask).
        const hasUnresolvedErrorStatus =
          taskStatus !== undefined
            ? taskStatus === ExecutionLogStatus.ERROR
            : hasUnresolvedError(logs);
        const hasSkippedEntryStatus =
          taskStatus !== undefined
            ? taskStatus === ExecutionLogStatus.SKIPPED
            : hasSkippedEntry(logs);
        const hasAwaitingProcessingStatus =
          taskStatus !== undefined
            ? taskStatus === ExecutionLogStatus.AWAITING_PROCESSING
            : hasAwaitingProcessing(logs);
        const hasPollingStatus =
          taskStatus !== undefined
            ? taskStatus === ExecutionLogStatus.POLLING
            : hasPolling(logs);

        return {
          author: "Fides",
          title: key,
          date: new Date(logs[0].updated_at),
          type: ActivityTimelineItemTypeEnum.REQUEST_UPDATE,
          showViewLog:
            hasUnresolvedErrorStatus ||
            hasSkippedEntryStatus ||
            hasAwaitingProcessingStatus ||
            hasPollingStatus,
          onClick: () => {}, // This will be overridden in the component
          isError: hasUnresolvedErrorStatus,
          isSkipped: hasSkippedEntryStatus,
          isAwaitingInput: hasAwaitingProcessingStatus,
          isPolling: hasPollingStatus,
          id: `request-${key}`,
          // matches dataset_name set in
          // fides.api.service.privacy_request.duplication_detection.mark_as_duplicate
          isDuplicateDetection: key === DUPLICATE_DETECTION_DATASET_NAME,
        };
      });

  return {
    eventItems,
    isLoading,
  };
};
