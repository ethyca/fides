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
import { useGetSystemsQuery } from "~/features/system/system.slice";

import { AssessmentTaskPopoverContent } from "./AssessmentTaskPopoverContent";
import {
  useGetAssessmentTasksQuery,
  useGetAssessmentTemplatesQuery,
} from "./privacy-assessments.slice";
import { TaskStatus } from "./types";

const ACTIVE_POLL_INTERVAL = 5000;

interface AssessmentTaskStatusIndicatorProps {
  onTaskFinish?: () => void;
  className?: string;
}

export const AssessmentTaskStatusIndicator = ({
  onTaskFinish,
  className,
}: AssessmentTaskStatusIndicatorProps) => {
  const [notificationApi, notificationHolder] = notification.useNotification();

  const { data: tasksData } = useGetAssessmentTasksQuery(
    { page: 1, size: 10 },
    { pollingInterval: ACTIVE_POLL_INTERVAL },
  );

  const activeTask = useMemo(
    () =>
      (tasksData?.items ?? []).find(
        (t) =>
          t.status === TaskStatus.IN_PROCESSING ||
          t.status === TaskStatus.PENDING,
      ) ?? null,
    [tasksData],
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

  const { data: systemsData } = useGetSystemsQuery({ page: 1, size: 1000 });

  const systemNamesMap = useMemo(
    () =>
      Object.fromEntries(
        (systemsData?.items ?? [])
          .filter((s) => s.name !== null && s.name !== undefined)
          .map((s) => [s.fides_key, s.name as string]),
      ),
    [systemsData],
  );

  // Detect active → idle transition and fire the completion notification
  const hadActiveTaskRef = useRef(false);
  useEffect(() => {
    if (hadActiveTaskRef.current && !activeTask) {
      notificationApi.success({
        message: "New assessment results are available",
        btn: onTaskFinish ? (
          <Button
            size="small"
            onClick={() => {
              onTaskFinish();
              notificationApi.destroy();
            }}
          >
            Reload results
          </Button>
        ) : undefined,
        duration: 0,
      });
    }
    hadActiveTaskRef.current = activeTask !== null;
  }, [activeTask, notificationApi, onTaskFinish]);

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
            Last assessment {lastAssessmentAgo}
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
    <>
      {notificationHolder}
      <Popover
        content={
          <AssessmentTaskPopoverContent
            activeTask={activeTask}
            lastCompletedTask={lastCompletedTask}
            systemNamesMap={systemNamesMap}
            templateNamesMap={templateNamesMap}
          />
        }
        title="Evaluation details"
        trigger="hover"
        placement="bottom"
      >
        <div className={`cursor-pointer${className ? ` ${className}` : ""}`}>
          {inlineContent}
        </div>
      </Popover>
    </>
  );
};
