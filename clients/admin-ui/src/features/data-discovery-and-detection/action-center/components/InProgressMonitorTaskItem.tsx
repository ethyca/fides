import {
  AntCol as Col,
  AntFlex as Flex,
  AntListItemProps as ListItemProps,
  AntRow as Row,
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
    <div {...props}>
      <Row gutter={[16, 8]}>
        <Col span={24}>
          <Flex justify="space-between" align="flex-start">
            <div>
              <Title level={5} style={{ margin: 0, marginBottom: 4 }}>
                {task.monitor_name || "Unknown Monitor"}
              </Title>
              <Flex gap={8} align="center">
                <Tag color={getTaskTypeColor(task.action_type)}>
                  {formatText(task.action_type)}
                </Tag>
                <Tag color={getStatusColor(task.status)}>
                  {formatText(task.status)}
                </Tag>
                {task.connection_type && (
                  <Text type="secondary" style={{ fontSize: "12px" }}>
                    {task.connection_type}
                  </Text>
                )}
              </Flex>
            </div>
            <div style={{ textAlign: "right" }}>
              <Text type="secondary" style={{ fontSize: "12px" }}>
                {formatDate(task.updated_at)}
              </Text>
            </div>
          </Flex>
        </Col>
        {task.message && (
          <Col span={24}>
            <Text type="secondary" style={{ fontSize: "12px" }}>
              {task.message}
            </Text>
          </Col>
        )}
        {task.staged_resource_urns && task.staged_resource_urns.length > 0 && (
          <Col span={24}>
            <Text type="secondary" style={{ fontSize: "12px" }}>
              Staged resources: {task.staged_resource_urns.length}
            </Text>
          </Col>
        )}
      </Row>
    </div>
  );
};
