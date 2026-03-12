import {
  Button,
  ColumnsType,
  Dropdown,
  Icons,
  Table,
  Tag,
  Typography,
} from "fidesui";

import {
  MOCK_REQUEST_LOG,
  MOCK_TOTAL_REQUEST_LOG_VIOLATIONS,
} from "./mock-data";
import { RequestLogEntry } from "./types";

const { Text } = Typography;

interface RequestLogTableProps {
  policyFilter: string | undefined;
  dataUseFilter: string | undefined;
  searchQuery: string;
  onRowClick: (record: RequestLogEntry) => void;
}

const RequestLogTable = ({
  policyFilter,
  dataUseFilter,
  searchQuery,
  onRowClick,
}: RequestLogTableProps) => {
  const filteredData = MOCK_REQUEST_LOG.filter((entry) => {
    if (policyFilter && entry.policy !== policyFilter) {
      return false;
    }
    if (dataUseFilter && entry.dataUse !== dataUseFilter) {
      return false;
    }
    if (
      searchQuery &&
      !entry.consumer.toLowerCase().includes(searchQuery.toLowerCase()) &&
      !entry.policy.toLowerCase().includes(searchQuery.toLowerCase())
    ) {
      return false;
    }
    return true;
  });

  const columns: ColumnsType<RequestLogEntry> = [
    {
      title: "Timestamp",
      dataIndex: "timestamp",
      key: "timestamp",
      render: (date: string) => {
        const d = new Date(date);
        return (
          <Text className="font-semibold">
            {d.toISOString().slice(0, 10)} {d.toISOString().slice(11, 19)}
          </Text>
        );
      },
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
    },
    {
      title: "Data use",
      dataIndex: "dataUse",
      key: "dataUse",
      render: (dataUse: string) => <Tag>{dataUse}</Tag>,
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
            onClick={(e) => e.stopPropagation()}
          />
        </Dropdown>
      ),
    },
  ];

  return (
    <Table
      dataSource={filteredData}
      columns={columns}
      rowKey="id"
      pagination={{
        total: MOCK_TOTAL_REQUEST_LOG_VIOLATIONS,
        pageSize: 25,
        showTotal: (total, range) =>
          `${range[0]}-${range[1]} of ${total} violations`,
      }}
      onRow={(record) => ({
        onClick: () => onRowClick(record),
        style: { cursor: "pointer" },
      })}
    />
  );
};

export default RequestLogTable;
