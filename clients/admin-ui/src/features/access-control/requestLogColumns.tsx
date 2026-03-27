import { formatDistance } from "date-fns";
import { type ColumnsType, Text } from "fidesui";

import type { PolicyViolationLog } from "./types";

export const getRequestLogColumns = (): ColumnsType<PolicyViolationLog> => [
  {
    title: "Timestamp",
    dataIndex: "timestamp",
    key: "timestamp",
    width: 140,
    render: (timestamp: string) =>
      formatDistance(new Date(timestamp), new Date(), { addSuffix: true }),
  },
  {
    title: "Consumer",
    dataIndex: "consumer",
    key: "consumer",
    width: 160,
    ellipsis: true,
  },
  {
    title: "Policy",
    dataIndex: "policy",
    key: "policy",
    width: 180,
    ellipsis: true,
    render: (value: string | undefined) => value || "Missing",
  },
  {
    title: "Control",
    dataIndex: "control",
    key: "control",
    width: 220,
    ellipsis: true,
  },
  {
    title: "Dataset",
    dataIndex: "dataset",
    key: "dataset",
    width: 200,
    ellipsis: true,
    render: (value: string) => <Text code>{value}</Text>,
  },
];
