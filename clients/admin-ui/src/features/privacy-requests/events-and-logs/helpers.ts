import { ExecutionLog, ExecutionLogStatus } from "privacy-requests/types";

/**
 *
 * A helper function to determine if the list of execution logs has any unresolved errors.
 * This means any error entries without a subsequent complete entry.
 */
export const hasUnresolvedError = (entries: ExecutionLog[]) => {
  const groupedByCollection = {};

  entries.forEach((entry) => {
    const { collection_name: collectionName, updated_at: updatedAt } = entry;
    if (
      !groupedByCollection[collectionName] ||
      new Date(groupedByCollection[collectionName].updated_at) <
        new Date(updatedAt)
    ) {
      groupedByCollection[collectionName] = entry;
    }
  });

  return Object.values(groupedByCollection).some((entry) => {
    if (entry.collection_name) {
      const latestComplete = entries.find(
        (e) =>
          e.status === ExecutionLogStatus.COMPLETE &&
          !e.collection_name &&
          new Date(e.updated_at) > new Date(entry.updated_at),
      );
      return !latestComplete && entry.status === ExecutionLogStatus.ERROR;
    }
    return entry.status === ExecutionLogStatus.ERROR;
  });
};
