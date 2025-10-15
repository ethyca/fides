import { formatDistanceStrict } from "date-fns";
import {
  AntButton as Button,
  AntCol as Col,
  AntDivider as Divider,
  AntListItemProps as ListItemProps,
  AntRow as Row,
  AntSpace as Space,
  AntTag as Tag,
  AntTypography as Typography,
  useToast,
} from "fidesui";

import { capitalize } from "~/features/common/utils";
import ConnectionTypeLogo, {
  connectionLogoFromMonitor,
} from "~/features/datastore-connections/ConnectionTypeLogo";
import {
  ConnectionType,
  MonitorTaskInProgressResponse,
  MonitorTaskType,
} from "~/types/api";

import {
  useDismissMonitorTaskMutation,
  useGetAggregateMonitorResultsQuery,
  useRetryMonitorTaskMutation,
} from "../action-center.slice";
import { CustomSpinner } from "./CustomSpinner";

const { Text, Title } = Typography;

// Helper function to format status names for display
const formatStatusForDisplay = (status: string): string => {
  // Special case: "paused" should display as "Awaiting Processing"
  if (status === "paused") {
    return "Awaiting Processing";
  }

  return status.split("_").map(capitalize).join(" ");
};

interface InProgressMonitorTaskItemProps extends ListItemProps {
  task: MonitorTaskInProgressResponse;
}

export const InProgressMonitorTaskItem = ({
  task,
  ...props
}: InProgressMonitorTaskItemProps) => {
  const toast = useToast();
  const [retryMonitorTask, { isLoading: isRetrying }] =
    useRetryMonitorTaskMutation();
  const [dismissMonitorTask, { isLoading: isDismissing }] =
    useDismissMonitorTaskMutation();
  const isDismissed = Boolean(task.dismissed_in_activity_view);
  const canRetry =
    task.status === "error" && task.action_type !== MonitorTaskType.DETECTION;

  // Build a minimal monitor key -> icon data map for ConnectionTypeLogo
  const { data: monitorAgg } = useGetAggregateMonitorResultsQuery({
    page: 1,
    size: 1000,
  });
  const aggItem = task.monitor_config_id
    ? monitorAgg?.items?.find((m) => m.key === task.monitor_config_id)
    : undefined;

  const logoSource = (() => {
    if (aggItem) {
      return connectionLogoFromMonitor({
        connection_type: aggItem.connection_type,
        name: aggItem.name ?? null,
        key: aggItem.key ?? null,
        saas_config: aggItem.saas_config
          ? {
              type: aggItem.saas_config.type ?? null,
              name: aggItem.saas_config.name ?? null,
              fides_key: aggItem.saas_config.fides_key ?? null,
            }
          : null,
        secrets: aggItem.secrets?.url ? { url: aggItem.secrets.url } : null,
      });
    }

    if (task.connection_type) {
      return connectionLogoFromMonitor({
        connection_type: task.connection_type as ConnectionType,
        name:
          task.connection_name ??
          (task.connection_type ? task.connection_type.toString() : null),
        key: null,
        saas_config: null,
        secrets: null,
      });
    }

    return undefined;
  })();

  const taskCount = task.staged_resource_urns?.length || 0;
  const isInProgress = [
    "pending",
    "in_processing",
    "paused",
    "retrying",
  ].includes((task.status || "").toLowerCase());
  const fieldCount = task.field_count || taskCount;
  const taskTitle = (() => {
    if (
      task.action_type === MonitorTaskType.CLASSIFICATION ||
      task.action_type === MonitorTaskType.LLM_CLASSIFICATION
    ) {
      const verb = task.status === "complete" ? "Classified" : "Classifying";
      return `${verb} ${fieldCount} ${fieldCount === 1 ? "field" : "fields"}`;
    }
    if (task.action_type === MonitorTaskType.DETECTION) {
      return task.status === "complete"
        ? "Monitor scanned"
        : "Monitor scanning";
    }
    if (task.action_type === MonitorTaskType.PROMOTION) {
      return task.status === "complete" ? "Promoted" : "Promoting";
    }
    return task.action_type ? task.action_type.replace(/_/g, " ") : "Task";
  })();

  const monitorGroupLabel = (() => {
    const type = (task.connection_type || "").toString().toUpperCase();
    if (type.includes("WEBSITE")) {
      return "Product monitor";
    }
    return "Analytics monitor";
  })();

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
      case "paused": // This is the actual enum value for "awaiting_processing"
        return "purple";
      case "retrying":
        return "orange";
      case "skipped":
        return "gray";
      default:
        return "gray";
    }
  };

  const formatText = (text?: string) => {
    if (!text) {
      return "Unknown";
    }
    return formatStatusForDisplay(text);
  };

  const handleRetryTask = async () => {
    try {
      await retryMonitorTask({ taskId: task.id }).unwrap();
      toast({
        status: "success",
        description: "Task retry initiated successfully",
      });
    } catch (error: any) {
      const errorMessage =
        error?.data?.detail || error?.message || "Unknown error occurred";
      toast({
        status: "error",
        description: `Failed to retry task: ${errorMessage}`,
      });
    }
  };

  const handleDismissTask = async () => {
    try {
      await dismissMonitorTask({ taskId: task.id }).unwrap();
      toast({
        status: "success",
        description: "Task dismissed successfully",
      });
    } catch (error: any) {
      const errorMessage =
        error?.data?.detail || error?.message || "Unknown error occurred";
      toast({
        status: "error",
        description: `Failed to dismiss task: ${errorMessage}`,
      });
    }
  };

  return (
    <div {...props} className="w-full">
      <Row gutter={12} className="w-full">
        <Col span={14} className="align-middle">
          <Space align="center" size={8} wrap>
            {logoSource && (
              <ConnectionTypeLogo data={logoSource} boxSize="24px" />
            )}
            <Title level={5} className="m-0">
              {taskTitle}
            </Title>
            {!isInProgress && (
              <Tag color={getStatusColor(task.status)}>
                {formatText(task.status)}
              </Tag>
            )}
          </Space>
        </Col>
        <Col span={4} className="flex items-center justify-end">
          <Text type="secondary" size="sm">
            {monitorGroupLabel}
          </Text>
        </Col>
        <Col span={3} className="flex items-center justify-end">
          {isInProgress ? (
            <CustomSpinner />
          ) : (
            <Text type="secondary" size="sm">
              {formatDistanceStrict(new Date(task.updated_at), new Date(), {
                addSuffix: true,
              })}
            </Text>
          )}
        </Col>
        <Col span={3} className="flex items-center justify-end">
          {task.status === "error" && (
            <Space size={0} split={<Divider type="vertical" />}>
              {canRetry && (
                <Button
                  type="link"
                  size="small"
                  loading={isRetrying}
                  onClick={handleRetryTask}
                  className="p-0"
                >
                  Retry
                </Button>
              )}
              {!isDismissed && (
                <Button
                  type="link"
                  size="small"
                  loading={isDismissing}
                  onClick={handleDismissTask}
                  className="p-0"
                >
                  Dismiss
                </Button>
              )}
            </Space>
          )}
        </Col>
      </Row>
    </div>
  );
};
