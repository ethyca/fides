import {
  ActivityTimelineItem,
  ActivityTimelineItemTypeEnum,
  ExecutionLogStatus,
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
        const hasUnresolvedError = logs.some(
          (log) => log.status === ExecutionLogStatus.ERROR,
        );
        const hasSkippedEntry = logs.some(
          (log) => log.status === ExecutionLogStatus.SKIPPED,
        );
        const hasAwaitingProcessing = logs.some(
          (log) => log.status === ExecutionLogStatus.AWAITING_PROCESSING,
        );

        return {
          author: "Fides",
          title: key,
          date: new Date(logs[0].updated_at),
          type: ActivityTimelineItemTypeEnum.REQUEST_UPDATE,
          showViewLog: hasUnresolvedError || hasSkippedEntry || hasAwaitingProcessing,
          onClick: () => {}, // This will be overridden in the component
          isError: hasUnresolvedError,
          isSkipped: hasSkippedEntry,
          isAwaitingInput: hasAwaitingProcessing,
          id: `request-${key}`,
        };
      });

  return {
    eventItems,
    isLoading,
  };
};
