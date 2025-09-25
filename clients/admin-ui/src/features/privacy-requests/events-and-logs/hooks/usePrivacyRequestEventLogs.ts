import {
  hasAwaitingProcessing,
  hasPolling,
  hasSkippedEntry,
  hasUnresolvedError,
} from "~/features/privacy-requests/events-and-logs/helpers";
import {
  ActivityTimelineItem,
  ActivityTimelineItemTypeEnum,
  PrivacyRequestResults,
} from "~/features/privacy-requests/types";

/**
 * Hook for processing privacy request event logs
 */
export const usePrivacyRequestEventLogs = (results?: PrivacyRequestResults) => {
  // Determine if results are loading
  const isLoading = !results;

  // Map from source events to ActivityTimelineItems
  const eventItems: ActivityTimelineItem[] = !results
    ? []
    : Object.entries(results).map(([key, logs]) => {
        // Use the proper helper functions that handle collection-level grouping
        const hasUnresolvedErrorStatus = hasUnresolvedError(logs);
        const hasSkippedEntryStatus = hasSkippedEntry(logs);
        const hasAwaitingProcessingStatus = hasAwaitingProcessing(logs);
        const hasPollingStatus = hasPolling(logs);

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
        };
      });

  return {
    eventItems,
    isLoading,
  };
};
