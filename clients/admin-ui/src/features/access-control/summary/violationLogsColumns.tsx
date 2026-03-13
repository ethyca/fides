import { formatDistance } from "date-fns";
import { Button, type ColumnsType, Dropdown, Icons } from "fidesui";

import type { PolicyViolationLog } from "../types";

const menuItems = [
  {
    key: "view",
    label: "View details",
  },
];

export const getViolationLogsColumns = (): ColumnsType<PolicyViolationLog> => [
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
    render: (value: string) => (
      <span className="font-mono">{value}</span>
    ),
  },
  {
    title: "Data use",
    dataIndex: "data_use",
    key: "data_use",
    render: (value: string) => (
      <span className="font-mono">{value}</span>
    ),
  },
  {
    title: "Actions",
    key: "actions",
    width: 80,
    render: () => (
      <Dropdown menu={{ items: menuItems }} trigger={["click"]}>
        <Button
          aria-label="Menu"
          icon={<Icons.OverflowMenuVertical />}
          size="small"
        />
      </Dropdown>
    ),
  },
];
