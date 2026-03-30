import { Table, Text } from "fidesui";

import type { MockDataset, MockSystem } from "../../types";

interface AssetsTabProps {
  system: MockSystem;
}

const columns = [
  {
    title: "Dataset",
    dataIndex: "name",
    key: "name",
    render: (name: string) => <Text strong>{name}</Text>,
  },
  {
    title: "Key",
    dataIndex: "key",
    key: "key",
    render: (key: string) => (
      <Text type="secondary" className="text-xs">
        {key}
      </Text>
    ),
  },
  {
    title: "Collections",
    dataIndex: "collectionCount",
    key: "collectionCount",
    sorter: (a: MockDataset, b: MockDataset) =>
      a.collectionCount - b.collectionCount,
  },
  {
    title: "Fields",
    dataIndex: "fieldCount",
    key: "fieldCount",
    sorter: (a: MockDataset, b: MockDataset) => a.fieldCount - b.fieldCount,
  },
  {
    title: "Created",
    dataIndex: "createdAt",
    key: "createdAt",
  },
];

const AssetsTab = ({ system }: AssetsTabProps) => (
  <div>
    {system.datasets.length === 0 ? (
      <Text type="secondary">No datasets linked to this system.</Text>
    ) : (
      <Table
        dataSource={system.datasets}
        columns={columns}
        rowKey="key"
        size="small"
        pagination={false}
      />
    )}
  </div>
);

export default AssetsTab;
