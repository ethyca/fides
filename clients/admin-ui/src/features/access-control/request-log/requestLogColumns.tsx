import { formatDistance } from "date-fns";
import type { ColumnsType } from "fidesui";

import type { PolicyViolationLog } from "../types";

export const getRequestLogColumns = (): ColumnsType<PolicyViolationLog> => [
  {
    title: "Timestamp",
    dataIndex: "timestamp",
    key: "timestamp",
    width: 160,
    render: (timestamp: string) =>
      formatDistance(new Date(timestamp), new Date(), { addSuffix: true }),
  },
  {
    title: "Consumer",
    dataIndex: "consumer",
    key: "consumer",
  },
  {
    title: "Policy",
    dataIndex: "policy",
    key: "policy",
  },
  {
    title: "Dataset",
    dataIndex: "dataset",
    key: "dataset",
    render: (value: string) => <span className="font-mono">{value}</span>,
  },
  {
    title: "Data use",
    dataIndex: "data_use",
    key: "data_use",
    render: (value: string) => <span className="font-mono">{value}</span>,
  },
];
