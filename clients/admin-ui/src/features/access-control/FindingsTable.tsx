import {
  Button,
  ColumnsType,
  CUSTOM_TAG_COLOR,
  Dropdown,
  Icons,
  Table,
  Tag,
  Typography,
} from "fidesui";
import { useRouter } from "next/router";

import { ACCESS_CONTROL_REQUEST_LOG_ROUTE } from "~/features/common/nav/routes";

import { MOCK_FINDINGS } from "./mock-data";
import { ViolationSummary } from "./types";

const { Text } = Typography;

const uniquePolicies = [...new Set(MOCK_FINDINGS.map((f) => f.policyName))].map(
  (p) => ({ text: p, value: p }),
);

const uniqueControls = [
  ...new Set(MOCK_FINDINGS.map((f) => f.controlName)),
].map((c) => ({ text: c, value: c }));

const FindingsTable = () => {
  const router = useRouter();

  const columns: ColumnsType<ViolationSummary> = [
    {
      title: "Policy",
      dataIndex: "policyName",
      key: "policyName",
      filters: uniquePolicies,
      onFilter: (value, record) => record.policyName === value,
      render: (name: string) => <Text strong>{name}</Text>,
    },
    {
      title: "Control",
      dataIndex: "controlName",
      key: "controlName",
      filters: uniqueControls,
      onFilter: (value, record) => record.controlName === value,
    },
    {
      title: "Violation count",
      dataIndex: "violationCount",
      key: "violationCount",
      sorter: (a, b) => a.violationCount - b.violationCount,
      render: (count: number) => {
        let color: CUSTOM_TAG_COLOR = CUSTOM_TAG_COLOR.CAUTION;
        if (count >= 10) {
          color = CUSTOM_TAG_COLOR.ERROR;
        } else if (count >= 5) {
          color = CUSTOM_TAG_COLOR.WARNING;
        }
        return <Tag color={color}>{count}</Tag>;
      },
    },
    {
      title: "Last violation",
      dataIndex: "lastViolation",
      key: "lastViolation",
      sorter: (a, b) =>
        new Date(a.lastViolation).getTime() -
        new Date(b.lastViolation).getTime(),
      defaultSortOrder: "descend",
      render: (date: string) => {
        const d = new Date(date);
        return (
          <Text>
            {d.toISOString().slice(0, 10)} {d.toISOString().slice(11, 19)}
          </Text>
        );
      },
    },
    {
      title: "Actions",
      key: "actions",
      width: 60,
      render: () => (
        <Dropdown
          menu={{
            items: [
              { key: "view", label: "View details" },
              { key: "dismiss", label: "Dismiss" },
            ],
          }}
          trigger={["click"]}
        >
          <Button
            aria-label="Row actions"
            type="text"
            icon={<Icons.OverflowMenuVertical size={16} />}
          />
        </Dropdown>
      ),
    },
  ];

  const handleRowClick = (record: ViolationSummary) => {
    router.push({
      pathname: ACCESS_CONTROL_REQUEST_LOG_ROUTE,
      query: { policy: record.policyName },
    });
  };

  return (
    <Table
      dataSource={MOCK_FINDINGS}
      columns={columns}
      rowKey="id"
      pagination={{
        total: MOCK_FINDINGS.length,
        pageSize: 15,
        showTotal: (total, range) =>
          `${range[0]}-${range[1]} of ${total} violations`,
      }}
      onRow={(record) => ({
        onClick: () => handleRowClick(record),
        style: { cursor: "pointer" },
      })}
    />
  );
};

export default FindingsTable;
