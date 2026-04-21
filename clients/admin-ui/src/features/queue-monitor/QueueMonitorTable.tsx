import { ColumnsType, Table, Typography } from "fidesui";
import { useMemo } from "react";

import { QueueStats } from "./types";

const { Text } = Typography;

const columns: ColumnsType<QueueStats> = [
  {
    title: "Queue Name",
    dataIndex: "queue_name",
    key: "queue_name",
  },
  {
    title: "Available",
    dataIndex: "available",
    key: "available",
  },
  {
    title: "Delayed",
    dataIndex: "delayed",
    key: "delayed",
  },
  {
    title: "In Flight",
    dataIndex: "in_flight",
    key: "in_flight",
  },
];

interface Props {
  queues: QueueStats[];
  isLoading?: boolean;
}

const QueueMonitorTable = ({ queues, isLoading }: Props) => {
  const sorted = useMemo(
    () => [...queues].sort((a, b) => a.queue_name.localeCompare(b.queue_name)),
    [queues],
  );

  if (!isLoading && sorted.length === 0) {
    return <Text type="secondary">No queues configured</Text>;
  }

  return (
    <Table
      dataSource={sorted}
      columns={columns}
      rowKey="queue_name"
      pagination={false}
      loading={isLoading}
    />
  );
};

export default QueueMonitorTable;
