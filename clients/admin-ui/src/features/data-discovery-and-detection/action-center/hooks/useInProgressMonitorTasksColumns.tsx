import { AntTag as Tag, AntTypography as Typography } from "fidesui";
import { useMemo } from "react";

import { formatDate } from "~/features/common/utils";
import { MonitorTaskInProgressResponse } from "~/types/api";

const { Text } = Typography;

export const useInProgressMonitorTasksColumns = () => {
  const columns = useMemo(
    () => [
      {
        title: "Monitor Name",
        dataIndex: "monitor_name",
        key: "monitor_name",
        width: "25%",
        render: (monitorName: string) => (
          <Text strong>{monitorName}</Text>
        ),
      },
      {
        title: "Task Type",
        dataIndex: "task_type",
        key: "task_type",
        width: "15%",
        render: (taskType: string) => {
          const color = taskType === "classification" ? "blue" : "green";
          return (
            <Tag color={color}>
              {taskType.charAt(0).toUpperCase() + taskType.slice(1)}
            </Tag>
          );
        },
      },
      {
        title: "Status",
        dataIndex: "status",
        key: "status",
        width: "15%",
        render: (status: string) => {
          const color = status === "pending" ? "orange" : "processing";
          return (
            <Tag color={color}>
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </Tag>
          );
        },
      },
      {
        title: "Connection Type",
        dataIndex: "connection_type",
        key: "connection_type",
        width: "15%",
        render: (connectionType: string | null) => (
          <Text>{connectionType || "Unknown"}</Text>
        ),
      },
      {
        title: "Last Updated",
        dataIndex: "last_updated",
        key: "last_updated",
        width: "20%",
        render: (lastUpdated: string) => (
          <Text>{formatDate(lastUpdated)}</Text>
        ),
      },
      {
        title: "Message",
        dataIndex: "message",
        key: "message",
        width: "10%",
        render: (message: string | null) => (
          <Text type={message ? "secondary" : undefined}>
            {message || "—"}
          </Text>
        ),
      },
    ],
    [],
  );

  return { columns };
};
