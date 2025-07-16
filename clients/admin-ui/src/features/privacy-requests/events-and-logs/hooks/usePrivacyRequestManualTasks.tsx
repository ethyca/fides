import { AntMessage as message } from "fidesui";
import { useEffect, useMemo } from "react";

import { formatUser } from "~/features/common/utils";
import { useGetTasksQuery } from "~/features/manual-tasks/manual-tasks.slice";
import {
  ActivityTimelineItem,
  ActivityTimelineItemTypeEnum,
} from "~/features/privacy-requests/types";
import { ManualFieldListItem, ManualFieldStatus } from "~/types/api";

export const usePrivacyRequestManualTasks = (privacyRequestId: string) => {
  const {
    data: tasksData,
    isLoading,
    error,
  } = useGetTasksQuery({
    page: 1,
    size: 100,
    privacyRequestId,
    status: undefined, // Get all statuses, we'll filter for completed/skipped
    includeFullSubmissionDetails: true,
  });

  useEffect(() => {
    if (error) {
      message.error("Failed to fetch manual tasks");
    }
  }, [error]);

  // Filter and map completed/skipped tasks to ActivityTimelineItem
  const manualTaskItems: ActivityTimelineItem[] = !tasksData
    ? []
    : tasksData.items
        .filter(
          (task: ManualFieldListItem) =>
            task.status === ManualFieldStatus.COMPLETED ||
            task.status === ManualFieldStatus.SKIPPED,
        )
        .map((task: ManualFieldListItem) => {
          // Format the user who completed the task
          let author = task.submission_user
            ? formatUser(task.submission_user)
            : "Unknown User";

          const isRootUser =
            task.submission_user?.id &&
            !task.submission_user?.id.startsWith("fid_");
          if (isRootUser) {
            author = task.submission_user?.id || "Unknown User";
          }

          // Create title based on completion status
          const isSkipped = task.status === ManualFieldStatus.SKIPPED;
          const actionText = isSkipped ? "skipped" : "completed";
          const title = `Task ${actionText} - ${task.name}`;

          // Use the most recent comment if available
          const description =
            task.comments && task.comments.length > 0
              ? task.comments[task.comments.length - 1].comment_text
              : undefined;

          // Use attachments array directly
          const attachments = task.attachments || [];

          return {
            author,
            title,
            date: new Date(task.updated_at),
            type: ActivityTimelineItemTypeEnum.MANUAL_TASK,
            showViewLog: false, // Manual tasks don't have logs
            description,
            isError: false,
            isSkipped,
            isAwaitingInput: false,
            id: `manual-task-${task.manual_field_id}`,
            attachments,
          };
        });

  // Collect all comment IDs that are part of manual tasks
  // to avoid duplicate display in the timeline
  const taskCommentIds = useMemo(() => {
    const commentIds = new Set<string>();
    if (tasksData?.items) {
      tasksData.items
        .filter(
          (task: ManualFieldListItem) =>
            task.status === ManualFieldStatus.COMPLETED ||
            task.status === ManualFieldStatus.SKIPPED,
        )
        .forEach((task: ManualFieldListItem) => {
          task.comments?.forEach((comment) => {
            commentIds.add(comment.id);
          });
        });
    }
    return commentIds;
  }, [tasksData]);

  return {
    manualTaskItems,
    taskCommentIds,
    isLoading,
  };
};
