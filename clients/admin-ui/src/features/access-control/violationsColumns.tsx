import { formatDistance } from "date-fns";
import { type ColumnsType, Tag } from "fidesui";

import type { PolicyViolationAggregate } from "./types";

const getViolationColor = (count: number) => {
  if (count >= 100) {
    return "error";
  }
  if (count >= 30) {
    return "warning";
  }
  return "default";
};

export const getViolationsColumns =
  (): ColumnsType<PolicyViolationAggregate> => [
    {
      title: "Policy",
      dataIndex: "policy",
      key: "policy",
    },
    {
      title: "Control",
      dataIndex: "control",
      key: "control",
    },
    {
      title: "Violations",
      dataIndex: "violation_count",
      key: "violation_count",
      width: 120,
      sorter: (a, b) => a.violation_count - b.violation_count,
      render: (count: number) => (
        <Tag color={getViolationColor(count)}>{count}</Tag>
      ),
    },
    {
      title: "Last violation",
      dataIndex: "last_violation",
      key: "last_violation",
      width: 160,
      render: (timestamp: string) =>
        formatDistance(new Date(timestamp), new Date(), { addSuffix: true }),
      sorter: (a, b) =>
        new Date(a.last_violation).getTime() -
        new Date(b.last_violation).getTime(),
    },
  ];
