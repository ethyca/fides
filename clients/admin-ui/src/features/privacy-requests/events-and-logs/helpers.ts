import { ExecutionLog, ExecutionLogStatus } from "privacy-requests/types";

/**
 *
 * A helper function to determine if the list of execution logs has any unresolved errors.
 * This means any error logs without a subsequent complete log.
 */
export const hasUnresolvedError = (logs: ExecutionLog[]) => {
  const groupedByCollection: { [key: string]: ExecutionLog } = {};

  logs.forEach((log) => {
    const { collection_name: collectionName, updated_at: updatedAt } = log;
    if (
      !groupedByCollection[collectionName] ||
      new Date(groupedByCollection[collectionName].updated_at) <
        new Date(updatedAt)
    ) {
      groupedByCollection[collectionName] = log;
    }
  });

  return Object.values(groupedByCollection).some((log) => {
    if (log.collection_name) {
      const latestComplete = logs.find(
        (e) =>
          e.status === ExecutionLogStatus.COMPLETE &&
          !e.collection_name &&
          new Date(e.updated_at) > new Date(log.updated_at),
      );
      return !latestComplete && log.status === ExecutionLogStatus.ERROR;
    }
    return log.status === ExecutionLogStatus.ERROR;
  });
};
