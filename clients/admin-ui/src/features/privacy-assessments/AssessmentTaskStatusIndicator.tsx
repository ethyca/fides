import {
  Descriptions,
  Flex,
  Icons,
  Popover,
  Progress,
  Space,
  Spin,
  Tag,
  Text,
} from "fidesui";
import { useMemo } from "react";

import { useRelativeTime } from "~/features/common/hooks/useRelativeTime";

import { AssessmentTaskResponse, TaskStatus } from "./types";

interface AssessmentTaskStatusIndicatorProps {
  activeTask: AssessmentTaskResponse | null;
  lastCompletedTask: AssessmentTaskResponse | null;
  lastAssessmentDate: Date | null;
  className?: string;
}

const formatSystems = (systemFidesKeys: string[] | null): string =>
  systemFidesKeys && systemFidesKeys.length > 0
    ? systemFidesKeys.join(", ")
    : "All systems";

const formatTypes = (assessmentTypes: string[]): string =>
  assessmentTypes.join(", ") || "—";

const ActiveTaskPopoverContent = ({
  task,
}: {
  task: AssessmentTaskResponse;
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
          {formatTypes(task.assessment_types)}
        </Descriptions.Item>
        <Descriptions.Item label="Systems">
          {formatSystems(task.system_fides_keys)}
        </Descriptions.Item>
        <Descriptions.Item label="Started">{startedAgo}</Descriptions.Item>
      </Descriptions>
    </div>
  );
};

const CompletedTaskPopoverContent = ({
  task,
}: {
  task: AssessmentTaskResponse;
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
          {formatTypes(task.assessment_types)}
        </Descriptions.Item>
        <Descriptions.Item label="Systems">
          {formatSystems(task.system_fides_keys)}
        </Descriptions.Item>
        <Descriptions.Item label="Completed">{completedAgo}</Descriptions.Item>
      </Descriptions>
    </div>
  );
};

const ErrorTaskPopoverContent = ({
  task,
}: {
  task: AssessmentTaskResponse;
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
          {formatTypes(task.assessment_types)}
        </Descriptions.Item>
        <Descriptions.Item label="Systems">
          {formatSystems(task.system_fides_keys)}
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
  className,
}: AssessmentTaskStatusIndicatorProps) => {
  const lastAssessmentAgo = useRelativeTime(lastAssessmentDate);

  const hasLastError =
    !activeTask && lastCompletedTask?.status === TaskStatus.ERROR;

  const popoverContent = useMemo(() => {
    if (activeTask) {
      return <ActiveTaskPopoverContent task={activeTask} />;
    }
    if (lastCompletedTask?.status === TaskStatus.ERROR) {
      return <ErrorTaskPopoverContent task={lastCompletedTask} />;
    }
    if (lastCompletedTask) {
      return <CompletedTaskPopoverContent task={lastCompletedTask} />;
    }
    return (
      <Text type="secondary" size="sm">
        No evaluation history.
      </Text>
    );
  }, [activeTask, lastCompletedTask]);

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
    <Popover
      content={popoverContent}
      title="Evaluation details"
      trigger="hover"
      placement="bottomRight"
    >
      <div className={`cursor-pointer${className ? ` ${className}` : ""}`}>
        {inlineContent}
      </div>
    </Popover>
  );
};
