import {
  AntButton as Button,
  AntFlex as Flex,
  AntListItemProps as ListItemProps,
  AntPopover as Popover,
  AntTag as Tag,
  AntTypography as Typography,
} from "fidesui";
import { useRouter } from "next/router";

import { formatDate } from "~/features/common/utils";
import { DATA_DISCOVERY_ROUTE_DETAIL } from "~/features/common/nav/routes";
import { MonitorTaskInProgressResponse } from "~/types/api";

const { Text, Title } = Typography;

interface InProgressMonitorTaskItemProps extends ListItemProps {
  task: MonitorTaskInProgressResponse;
}

export const InProgressMonitorTaskItem = ({
  task,
  ...props
}: InProgressMonitorTaskItemProps) => {
  const router = useRouter();

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

  const handleSingleResourceClick = (urn: string) => {
    router.push({
      pathname: DATA_DISCOVERY_ROUTE_DETAIL,
      query: { resourceUrn: encodeURIComponent(urn) },
    });
  };

  const renderMultipleResourcesPopover = (urns: string[]) => {
    const content = (
      <div style={{ maxWidth: "300px" }}>
        <Text strong style={{ marginBottom: "8px", display: "block" }}>
          Staged Resources ({urns.length})
        </Text>
        <div style={{ maxHeight: "200px", overflowY: "auto" }}>
          {urns.map((urn, index) => (
            <div key={urn} style={{ marginBottom: "4px" }}>
              <Button
                type="link"
                size="small"
                onClick={() => handleSingleResourceClick(urn)}
                style={{ padding: "0", height: "auto", textAlign: "left" }}
              >
                <Text style={{ fontSize: "12px" }} ellipsis={{ tooltip: urn }}>
                  {urn.split("/").pop() || `Resource ${index + 1}`}
                </Text>
              </Button>
            </div>
          ))}
        </div>
      </div>
    );

    return (
      <Popover content={content} title={null} trigger="click" placement="bottom">
        <Tag
          color="orange"
          style={{ cursor: "pointer" }}
          onClick={(e) => e.stopPropagation()}
        >
          Staged Resources: {urns.length}
        </Tag>
      </Popover>
    );
  };

  return (
    <div {...props} style={{ width: "100%" }}>
      {/* Line 1: Monitor name + all tags */}
      <div style={{ marginBottom: "4px" }}>
        <Flex gap={8} align="center" wrap="wrap">
          <Title level={5} style={{ margin: 0, marginRight: "8px" }}>
            {task.monitor_name || "Unknown Monitor"}
          </Title>

          {task.connection_type && (
            <Tag color="default">
              {task.connection_type}
            </Tag>
          )}

          <Tag color={getTaskTypeColor(task.action_type)}>
            {formatText(task.action_type)}
          </Tag>

          <Tag color={getStatusColor(task.status)}>
            {formatText(task.status)}
          </Tag>

          {task.staged_resource_urns && task.staged_resource_urns.length > 0 && (
            task.staged_resource_urns.length === 1 ? (
              <Tag
                color="orange"
                style={{ cursor: "pointer" }}
                onClick={() => handleSingleResourceClick(task.staged_resource_urns![0])}
              >
                Staged Resources: 1
              </Tag>
            ) : (
              renderMultipleResourcesPopover(task.staged_resource_urns)
            )
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
