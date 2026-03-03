import {
  Button,
  Descriptions,
  Flex,
  Icons,
  Popover,
  Progress,
  Space,
  Spin,
  Tag,
  Text,
  notification,
} from "fidesui";
import { useEffect, useMemo, useRef } from "react";

import { useRelativeTime } from "~/features/common/hooks/useRelativeTime";

import { AssessmentTaskResponse, TaskStatus } from "./types";

interface AssessmentTaskStatusIndicatorProps {
  activeTask: AssessmentTaskResponse | null;
  lastCompletedTask: AssessmentTaskResponse | null;
  lastAssessmentDate: Date | null;
  systemNamesMap?: Record<string, string>;
  templateNamesMap?: Record<string, string>;
  onTaskFinish?: () => void;
  className?: string;
}

const formatSystems = (
  systemFidesKeys: string[] | null,
  namesMap?: Record<string, string>,
): string => {
  if (!systemFidesKeys || systemFidesKeys.length === 0) {
    return "All systems";
  }
  return systemFidesKeys
    .map((key) => namesMap?.[key] ?? key)
    .join(", ");
};

const formatTypes = (
  assessmentTypes: string[],
  namesMap?: Record<string, string>,
): string => {
  if (assessmentTypes.length === 0) {
    return "—";
  }
  return assessmentTypes
    .map((t) => namesMap?.[t] ?? t)
    .join(", ");
};

const ActiveTaskPopoverContent = ({
  task,
  systemNamesMap,
  templateNamesMap,
}: {
  task: AssessmentTaskResponse;
  systemNamesMap?: Record<string, string>;
  templateNamesMap?: Record<string, string>;
}) => {
  const startedAgo = useRelativeTime(
    task.created_at ? new Date(task.created_at) : null,
  );

  return (
    <div style={{ width: 320 }}>
      <Descriptions column={1} size="small">
        <Descriptions.Item label="Status">
          <Flex align="center" gap="small">
            <Spin size="small" />
            <span>In progress</span>
          </Flex>
        </Descriptions.Item>
        <Descriptions.Item label="Progress">
          <Space direction="vertical" size={4} className="w-full">
            <Text size="sm">
              {task.completed_count} of {task.total_count} assessments
            </Text>
            <Progress percent={Math.round(task.progress)} size="small" />
          </Space>
        </Descriptions.Item>
        <Descriptions.Item label="Assessment types">
          {formatTypes(task.assessment_types, templateNamesMap)}
        </Descriptions.Item>
        <Descriptions.Item label="Systems">
          {formatSystems(task.system_fides_keys, systemNamesMap)}
        </Descriptions.Item>
        <Descriptions.Item label="Started">{startedAgo}</Descriptions.Item>
        {task.status === TaskStatus.ERROR && task.message && (
          <Descriptions.Item label="Error">
            <Text type="danger" size="sm">
              {task.message}
            </Text>
          </Descriptions.Item>
        )}
      </Descriptions>
    </div>
  );
};

const CompletedTaskPopoverContent = ({
  task,
  systemNamesMap,
  templateNamesMap,
}: {
  task: AssessmentTaskResponse;
  systemNamesMap?: Record<string, string>;
  templateNamesMap?: Record<string, string>;
}) => {
  const completedAgo = useRelativeTime(
    task.updated_at ? new Date(task.updated_at) : null,
  );

  return (
    <div style={{ width: 320 }}>
      <Descriptions column={1} size="small">
        <Descriptions.Item label="Status">
          <Tag color="success">Completed</Tag>
        </Descriptions.Item>
        <Descriptions.Item label="Assessment types">
          {formatTypes(task.assessment_types, templateNamesMap)}
        </Descriptions.Item>
        <Descriptions.Item label="Systems">
          {formatSystems(task.system_fides_keys, systemNamesMap)}
        </Descriptions.Item>
        <Descriptions.Item label="Completed">{completedAgo}</Descriptions.Item>
      </Descriptions>
    </div>
  );
};

const ErrorTaskPopoverContent = ({
  task,
  systemNamesMap,
  templateNamesMap,
}: {
  task: AssessmentTaskResponse;
  systemNamesMap?: Record<string, string>;
  templateNamesMap?: Record<string, string>;
}) => {
  const failedAgo = useRelativeTime(
    task.updated_at ? new Date(task.updated_at) : null,
  );

  return (
    <div style={{ width: 320 }}>
      <Descriptions column={1} size="small">
        <Descriptions.Item label="Status">
          <Tag color="error">Failed</Tag>
        </Descriptions.Item>
        <Descriptions.Item label="Assessment types">
          {formatTypes(task.assessment_types, templateNamesMap)}
        </Descriptions.Item>
        <Descriptions.Item label="Systems">
          {formatSystems(task.system_fides_keys, systemNamesMap)}
        </Descriptions.Item>
        <Descriptions.Item label="Failed">{failedAgo}</Descriptions.Item>
        {task.message && (
          <Descriptions.Item label="Error">
            <Text type="danger" size="sm">
              {task.message}
            </Text>
          </Descriptions.Item>
        )}
      </Descriptions>
    </div>
  );
};

export const AssessmentTaskStatusIndicator = ({
  activeTask,
  lastCompletedTask,
  lastAssessmentDate,
  systemNamesMap,
  templateNamesMap,
  onTaskFinish,
  className,
}: AssessmentTaskStatusIndicatorProps) => {
  const lastAssessmentAgo = useRelativeTime(lastAssessmentDate);
  const [notificationApi, notificationHolder] = notification.useNotification();

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

  const popoverContent = useMemo(() => {
    if (activeTask) {
      return (
        <ActiveTaskPopoverContent
          task={activeTask}
          systemNamesMap={systemNamesMap}
          templateNamesMap={templateNamesMap}
        />
      );
    }
    if (lastCompletedTask?.status === TaskStatus.ERROR) {
      return (
        <ErrorTaskPopoverContent
          task={lastCompletedTask}
          systemNamesMap={systemNamesMap}
          templateNamesMap={templateNamesMap}
        />
      );
    }
    if (lastCompletedTask) {
      return (
        <CompletedTaskPopoverContent
          task={lastCompletedTask}
          systemNamesMap={systemNamesMap}
          templateNamesMap={templateNamesMap}
        />
      );
    }
    return (
      <Text type="secondary" size="sm">
        No evaluation history.
      </Text>
    );
  }, [activeTask, lastCompletedTask, systemNamesMap, templateNamesMap]);

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
    if (lastAssessmentDate) {
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
  }, [activeTask, hasLastError, lastAssessmentDate, lastAssessmentAgo]);

  if (!inlineContent) {
    return null;
  }

  return (
    <>
      {notificationHolder}
      <Popover
        content={popoverContent}
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
