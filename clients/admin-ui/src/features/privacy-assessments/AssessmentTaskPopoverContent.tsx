import { Descriptions, Flex, Progress, Space, Spin, Tag, Text } from "fidesui";

import { useRelativeTime } from "~/features/common/hooks/useRelativeTime";

import { AssessmentTaskResponse, TaskStatus } from "./types";

interface AssessmentTaskPopoverContentProps {
  activeTask: AssessmentTaskResponse | null;
  lastCompletedTask: AssessmentTaskResponse | null;
  systemNamesMap?: Record<string, string>;
  templateNamesMap?: Record<string, string>;
}

const formatSystems = (
  systemFidesKeys: string[] | null,
  namesMap?: Record<string, string>,
): string => {
  if (!systemFidesKeys || systemFidesKeys.length === 0) {
    return "All systems";
  }
  return systemFidesKeys.map((key) => namesMap?.[key] ?? key).join(", ");
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
  systemNamesMap,
  templateNamesMap,
}: AssessmentTaskPopoverContentProps) => {
  const task = activeTask ?? lastCompletedTask;
  const activeRelativeTime = useRelativeTime(
    activeTask?.created_at ? new Date(activeTask.created_at) : null,
  );
  const completedRelativeTime = useRelativeTime(
    lastCompletedTask?.updated_at
      ? new Date(lastCompletedTask.updated_at)
      : null,
  );

  if (!task) {
    return (
      <Text type="secondary" size="sm">
        No evaluation history.
      </Text>
    );
  }

  if (activeTask) {
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
                {activeTask.completed_count} of {activeTask.total_count}{" "}
                assessments
              </Text>
              <Progress
                percent={Math.round(activeTask.progress)}
                size="small"
              />
            </Space>
          </Descriptions.Item>
          <Descriptions.Item label="Assessment types">
            {formatTypes(activeTask.assessment_types, templateNamesMap)}
          </Descriptions.Item>
          <Descriptions.Item label="Systems">
            {formatSystems(activeTask.system_fides_keys, systemNamesMap)}
          </Descriptions.Item>
          <Descriptions.Item label="Started">
            {activeRelativeTime}
          </Descriptions.Item>
        </Descriptions>
      </div>
    );
  }

  const isError = lastCompletedTask!.status === TaskStatus.ERROR;

  return (
    <div style={{ width: 320 }}>
      <Descriptions column={1} size="small">
        <Descriptions.Item label="Status">
          {isError ? (
            <Tag color="error">Failed</Tag>
          ) : (
            <Tag color="success">Completed</Tag>
          )}
        </Descriptions.Item>
        <Descriptions.Item label="Assessment types">
          {formatTypes(lastCompletedTask!.assessment_types, templateNamesMap)}
        </Descriptions.Item>
        <Descriptions.Item label="Systems">
          {formatSystems(lastCompletedTask!.system_fides_keys, systemNamesMap)}
        </Descriptions.Item>
        <Descriptions.Item label={isError ? "Failed" : "Completed"}>
          {completedRelativeTime}
        </Descriptions.Item>
      </Descriptions>
    </div>
  );
};
