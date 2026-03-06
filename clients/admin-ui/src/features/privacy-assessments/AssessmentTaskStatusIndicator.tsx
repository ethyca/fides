import classNames from "classnames";
import {
  Button,
  Flex,
  Icons,
  notification,
  Popover,
  Spin,
  Text,
} from "fidesui";
import { useEffect, useMemo, useRef } from "react";

import { useRelativeTime } from "~/features/common/hooks/useRelativeTime";

import { AssessmentTaskPopoverContent } from "./AssessmentTaskPopoverContent";
import { useGetAssessmentTasksQuery } from "./privacy-assessments.slice";
import { TaskStatus } from "./types";

const ACTIVE_POLL_INTERVAL = 15_000;

interface AssessmentTaskStatusIndicatorProps {
  onTaskFinish?: () => void;
  className?: string;
}

export const AssessmentTaskStatusIndicator = ({
  onTaskFinish,
  className,
}: AssessmentTaskStatusIndicatorProps) => {
  // Fetch once on mount; derive activeTask first without polling so we can
  // use it to gate the polling interval on the same query subscription.
  const { data: tasksData } = useGetAssessmentTasksQuery({ page: 1, size: 10 });

  const activeTask = useMemo(
    () =>
      (tasksData?.items ?? []).find(
        (t) =>
          t.status === TaskStatus.IN_PROCESSING ||
          t.status === TaskStatus.PENDING ||
          t.status === TaskStatus.RETRYING,
      ) ?? null,
    [tasksData],
  );

  // Poll every 15s only while a task is in progress; stop when idle.
  useGetAssessmentTasksQuery(
    { page: 1, size: 10 },
    { pollingInterval: ACTIVE_POLL_INTERVAL, skip: !activeTask },
  );

  const lastCompletedTask = useMemo(
    () =>
      (tasksData?.items ?? []).find(
        (t) =>
          t.status === TaskStatus.COMPLETE || t.status === TaskStatus.ERROR,
      ) ?? null,
    [tasksData],
  );

  const lastCompletedDate = useMemo(
    () =>
      lastCompletedTask?.status === TaskStatus.COMPLETE &&
      lastCompletedTask.updated_at
        ? new Date(lastCompletedTask.updated_at)
        : null,
    [lastCompletedTask],
  );
  const lastAssessmentAgo = useRelativeTime(lastCompletedDate);

  const completedCount = activeTask?.completed_count ?? 0;

  const prevCompletedCountRef = useRef<number | null>(null);
  useEffect(() => {
    if (!activeTask) {
      prevCompletedCountRef.current = null;
      return;
    }
    if (
      prevCompletedCountRef.current !== null &&
      completedCount > prevCompletedCountRef.current
    ) {
      notification.success({
        message: "New assessment results are available",
        btn: onTaskFinish ? (
          <Button
            size="small"
            onClick={() => {
              onTaskFinish();
              notification.destroy();
            }}
          >
            Reload results
          </Button>
        ) : undefined,
        duration: 0,
      });
    }
    prevCompletedCountRef.current = completedCount;
  }, [activeTask, completedCount, onTaskFinish]);

  // Detect active → idle transition for the final completion or error
  const hadActiveTaskRef = useRef(false);
  useEffect(() => {
    if (hadActiveTaskRef.current && !activeTask) {
      const isError = lastCompletedTask?.status === TaskStatus.ERROR;

      if (isError) {
        notification.error({
          message: "Assessment evaluation failed",
          description: "An error occurred during evaluation",
          duration: 0,
        });
      } else {
        notification.success({
          message: "New assessment results are available",
          btn: onTaskFinish ? (
            <Button
              size="small"
              onClick={() => {
                onTaskFinish();
                notification.destroy();
              }}
            >
              Reload results
            </Button>
          ) : undefined,
          duration: 0,
        });
      }
    }
    hadActiveTaskRef.current = activeTask !== null;
  }, [activeTask, lastCompletedTask, onTaskFinish]);

  const hasLastError =
    !activeTask && lastCompletedTask?.status === TaskStatus.ERROR;

  const inlineContent = useMemo(() => {
    if (activeTask) {
      return (
        <Flex align="center" gap="small">
          <Spin size="small" />
          <Text type="secondary" size="sm">
            Evaluation in progress · {Math.round(activeTask.progress)}%
          </Text>
        </Flex>
      );
    }
    if (hasLastError) {
      return (
        <Flex align="center" gap="small">
          <Icons.WarningFilled size={14} className="text-red-500" />
          <Text type="danger" size="sm">
            Last evaluation failed
          </Text>
        </Flex>
      );
    }
    if (lastCompletedDate) {
      return (
        <Flex align="center" gap="small">
          <Icons.CheckmarkFilled size={14} />
          <Text type="secondary" size="sm">
            Last assessment evaluated {lastAssessmentAgo}
          </Text>
        </Flex>
      );
    }
    return null;
  }, [activeTask, hasLastError, lastCompletedDate, lastAssessmentAgo]);

  if (!inlineContent) {
    return null;
  }

  return (
    <Popover
      content={
        <AssessmentTaskPopoverContent
          activeTask={activeTask}
          lastCompletedTask={lastCompletedTask}
        />
      }
      title="Evaluation details"
      trigger="hover"
      placement="bottom"
    >
      <div className={classNames("cursor-pointer", className)}>
        {inlineContent}
      </div>
    </Popover>
  );
};
