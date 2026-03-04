import { Descriptions, Flex, Progress, Space, Spin, Tag, Text } from "fidesui";

import { useRelativeTime } from "~/features/common/hooks/useRelativeTime";

import { AssessmentTaskResponse, TaskStatus } from "./types";

interface AssessmentTaskPopoverContentProps {
  activeTask: AssessmentTaskResponse | null;
  lastCompletedTask: AssessmentTaskResponse | null;
  templateNamesMap?: Record<string, string>;
}

const formatSystems = (task: AssessmentTaskResponse | null): string => {
  if (!task) {
    return "—";
  }

  // Prefer system_names if available
  if (task.system_names && task.system_names.length > 0) {
    return task.system_names.join(", ");
  }

  // Fall back to system_fides_keys
  if (task.system_fides_keys && task.system_fides_keys.length > 0) {
    return task.system_fides_keys.join(", ");
  }

  return "All systems";
};

const formatTypes = (
  assessmentTypes: string[],
  namesMap?: Record<string, string>,
): string => {
  if (assessmentTypes.length === 0) {
    return "—";
  }
  return assessmentTypes.map((t) => namesMap?.[t] ?? t).join(", ");
};

export const AssessmentTaskPopoverContent = ({
  activeTask,
  lastCompletedTask,
  templateNamesMap,
}: AssessmentTaskPopoverContentProps) => {
  const activeRelativeTime = useRelativeTime(
    activeTask?.created_at ? new Date(activeTask.created_at) : null,
  );
  const completedRelativeTime = useRelativeTime(
    lastCompletedTask?.updated_at
      ? new Date(lastCompletedTask.updated_at)
      : null,
  );

  if (activeTask) {
    return (
      <div className="w-80">
        <Descriptions column={1} size="small">
          <Descriptions.Item label="Status">
            <Flex align="center" gap="small">
              <Spin size="small" />
              <span>In progress</span>
            </Flex>
          </Descriptions.Item>
          <Descriptions.Item label="Progress">
            <Space direction="vertical" size="small" className="w-full">
              <Text size="sm">
                {activeTask.completed_count} of {activeTask.total_count}{" "}
                assessments
              </Text>
              <Progress
                percent={Math.round(activeTask.progress)}
                size="small"
              />
            </Space>
          </Descriptions.Item>
          <Descriptions.Item label="Types">
            {formatTypes(activeTask.assessment_types, templateNamesMap)}
          </Descriptions.Item>
          <Descriptions.Item label="Systems">
            {formatSystems(activeTask)}
          </Descriptions.Item>
          <Descriptions.Item label="Started">
            {activeRelativeTime}
          </Descriptions.Item>
        </Descriptions>
      </div>
    );
  }

  if (!lastCompletedTask) {
    return (
      <Text type="secondary" size="sm">
        No evaluation history.
      </Text>
    );
  }

  const isError = lastCompletedTask.status === TaskStatus.ERROR;

  return (
    <div className="w-80">
      <Descriptions column={1} size="small">
        <Descriptions.Item label="Status">
          {isError ? (
            <Tag color="error">Failed</Tag>
          ) : (
            <Tag color="success">Completed</Tag>
          )}
        </Descriptions.Item>
        <Descriptions.Item label="Assessment types">
          {formatTypes(lastCompletedTask.assessment_types, templateNamesMap)}
        </Descriptions.Item>
        <Descriptions.Item label="Systems">
          {formatSystems(lastCompletedTask)}
        </Descriptions.Item>
        <Descriptions.Item label={isError ? "Failed" : "Completed"}>
          {completedRelativeTime}
        </Descriptions.Item>
      </Descriptions>
    </div>
  );
};
