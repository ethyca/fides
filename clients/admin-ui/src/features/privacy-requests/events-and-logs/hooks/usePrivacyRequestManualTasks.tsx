import { AntMessage as message } from "fidesui";
import { useEffect } from "react";

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
          const author = formatUser({
            first_name: task.completed_by_user_first_name,
            last_name: task.completed_by_user_last_name,
            email_address: task.completed_by_user_email_address,
          });

          // Create title based on completion status
          const isSkipped = task.status === ManualFieldStatus.SKIPPED;
          const actionText = isSkipped ? "skipped" : "completed";
          const title = `Task ${actionText} - ${task.name}`;

          // Use completion comment if available
          const description = task.completion_comment?.comment_text;

          // Create attachments array
          const attachments = task.completion_attachment
            ? [task.completion_attachment]
            : [];

          return {
            author,
            title,
            date: new Date(task.completed_at || task.updated_at),
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

  return {
    manualTaskItems,
    isLoading,
  };
};
