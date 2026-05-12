import classNames from "classnames";
import { Flex, Icons, Popover, Spin, Text, useNotification } from "fidesui";
import { useEffect, useMemo, useRef } from "react";

import { useRelativeTime } from "~/features/common/hooks/useRelativeTime";

import { AssessmentTaskPopoverContent } from "./AssessmentTaskPopoverContent";
import {
  useGetAssessmentTasksQuery,
  useGetAssessmentTemplatesQuery,
  useGetPrivacyAssessmentsQuery,
} from "./privacy-assessments.slice";
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
  const notificationApi = useNotification();

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

  // Mirror the task poll on the assessments list while a task is active so
  // freshly-materialized `generating` rows and per-row status flips appear in
  // the page list within ~15s, instead of waiting for the first LLM call to
  // finish (which can be minutes for large prompts). Shares the cache key
  // with the page's `useGetPrivacyAssessmentsQuery()`, so the page list
  // re-renders automatically when this polling fills the cache.
  useGetPrivacyAssessmentsQuery(undefined, {
    pollingInterval: ACTIVE_POLL_INTERVAL,
    skip: !activeTask,
  });

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

  const { data: templatesData } = useGetAssessmentTemplatesQuery({
    page: 1,
    size: 100,
  });

  const templateNamesMap = useMemo(() => {
    const templates = templatesData?.items ?? [];
    return Object.fromEntries(
      templates.flatMap((t) => {
        const entries: [string, string][] = [[t.key, t.name]];
        if (t.assessment_type) {
          entries.push([t.assessment_type, t.name]);
        }
        return entries;
      }),
    );
  }, [templatesData]);

  // Detect active → idle transition for the final completion or error.
  // The list-poll subscription above stops the moment `activeTask` becomes
  // null, so the very last row flip (committed at the same time the task
  // moves to COMPLETE) won't be picked up by polling. Fire one explicit
  // refetch here to surface that final state.
  const hadActiveTaskRef = useRef(false);
  useEffect(() => {
    if (hadActiveTaskRef.current && !activeTask) {
      const isError = lastCompletedTask?.status === TaskStatus.ERROR;

      if (isError) {
        notificationApi.error({
          message: "Assessment evaluation failed",
          description: "An error occurred during evaluation",
          duration: 0,
        });
      } else {
        notificationApi.success({
          message: "Assessment evaluation complete",
        });
      }
      onTaskFinish?.();
    }
    hadActiveTaskRef.current = activeTask !== null;
  }, [activeTask, lastCompletedTask, notificationApi, onTaskFinish]);

  const hasLastError =
    !activeTask && lastCompletedTask?.status === TaskStatus.ERROR;

  const inlineContent = useMemo(() => {
    if (activeTask) {
      return (
        <Flex align="center" gap="small">
          <div>
            <Spin size="small" />
          </div>
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
            Last evaluated {lastAssessmentAgo}
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
          templateNamesMap={templateNamesMap}
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
