import { ExecutionLog, ExecutionLogStatus } from "privacy-requests/types";

export const hasStatus = (
  logs: ExecutionLog[],
  status: ExecutionLogStatus,
): boolean => {
  if (logs.length === 0) {
    return false;
  }

  // Sort by date descending
  const sortedLogs = Array.from(logs).sort(
    (a, b) =>
      new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime(),
  );

  // If latest entry has no collection and has the target status, return true
  if (!sortedLogs[0].collection_name) {
    return sortedLogs[0].status === status;
  }

  // If the latest entry for any collection has the target status, return true
  const latestByCollection: { [key: string]: ExecutionLog } = {};
  sortedLogs.forEach((log) => {
    if (log.collection_name && !latestByCollection[log.collection_name]) {
      latestByCollection[log.collection_name] = log;
    }
  });
  return Object.values(latestByCollection).some((log) => log.status === status);
};

export const hasUnresolvedError = (logs: ExecutionLog[]): boolean => {
  return hasStatus(logs, ExecutionLogStatus.ERROR);
};

export const hasSkippedEntry = (logs: ExecutionLog[]): boolean => {
  return hasStatus(logs, ExecutionLogStatus.SKIPPED);
};
