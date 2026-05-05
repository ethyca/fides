import { Descriptions, Flex, Progress, Space, Spin, Tag, Text } from "fidesui";

import { useRelativeTime } from "~/features/common/hooks/useRelativeTime";

import { AssessmentTaskResponse, TaskStatus } from "./types";
import { formatSystems, formatTypes } from "./utils";

interface AssessmentTaskPopoverContentProps {
  activeTask: AssessmentTaskResponse | null;
  lastCompletedTask: AssessmentTaskResponse | null;
  templateNamesMap?: Record<string, string>;
}

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
              <div>
                <Spin size="small" />
              </div>
              <span>In progress</span>
            </Flex>
          </Descriptions.Item>
          <Descriptions.Item label="Progress">
            <Space orientation="vertical" size="small" className="w-full">
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
          <Descriptions.Item label="Type">
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
        <Descriptions.Item label="Type">
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
