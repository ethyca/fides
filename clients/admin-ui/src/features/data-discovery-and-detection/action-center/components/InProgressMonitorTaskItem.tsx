import {
  AntFlex as Flex,
  AntListItemProps as ListItemProps,
  AntTag as Tag,
  AntTypography as Typography,
} from "fidesui";

import { formatDate } from "~/features/common/utils";
import { MonitorTaskInProgressResponse } from "~/types/api";

const { Text, Title } = Typography;

interface InProgressMonitorTaskItemProps extends ListItemProps {
  task: MonitorTaskInProgressResponse;
}

export const InProgressMonitorTaskItem = ({
  task,
  ...props
}: InProgressMonitorTaskItemProps) => {
  const getTaskTypeColor = (taskType?: string) => {
    switch (taskType) {
      case "classification":
        return "blue";
      case "promotion":
        return "green";
      default:
        return "gray";
    }
  };

  const getStatusColor = (status?: string) => {
    switch (status) {
      case "pending":
        return "orange";
      case "in_processing":
        return "processing";
      case "complete":
        return "green";
      case "error":
        return "red";
      default:
        return "gray";
    }
  };

  const formatText = (text?: string) => {
    if (!text) return "Unknown";
    return text.charAt(0).toUpperCase() + text.slice(1);
  };

  return (
    <div {...props} style={{ width: "100%" }}>
      {/* Line 1: Monitor name + all tags */}
      <div style={{ marginBottom: "4px" }}>
        <Flex gap={8} align="center" wrap="wrap">
          <Title level={5} style={{ margin: 0, marginRight: "8px" }}>
            {task.monitor_name || "Unknown Monitor"}
          </Title>

          <Tag color={getTaskTypeColor(task.action_type)}>
            {formatText(task.action_type)}
          </Tag>

          <Tag color={getStatusColor(task.status)}>
            {formatText(task.status)}
          </Tag>

          {task.connection_type && (
            <Tag color="default">
              {task.connection_type}
            </Tag>
          )}

          {task.staged_resource_urns && task.staged_resource_urns.length > 0 && (
            <Tag color="orange">
              Staged Resources: {task.staged_resource_urns.length}
            </Tag>
          )}
        </Flex>
      </div>

      {/* Line 2: Date */}
      <div>
        <Text type="secondary" style={{ fontSize: "12px" }}>
          {formatDate(task.updated_at)}
        </Text>
      </div>

      {/* Message line - if present */}
      {task.message && (
        <div style={{ marginTop: "4px" }}>
          <Text type="secondary" style={{ fontSize: "11px", fontStyle: "italic" }}>
            {task.message}
          </Text>
        </div>
      )}
    </div>
  );
};
