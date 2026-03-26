import { Flex, Input, Modal, Select, Table, Tag } from "fidesui";
import { useEffect, useMemo, useState } from "react";

import { MOCK_AVAILABLE_SYSTEMS } from "./mockData";
import type { AvailableSystem } from "./types";

interface AssignSystemsPickerModalProps {
  open: boolean;
  onClose: () => void;
  onConfirm: (systemIds: string[]) => void;
  assignedIds: string[];
}

const columns = [
  {
    title: "System",
    dataIndex: "system_name",
    key: "system_name",
  },
  {
    title: "Type",
    dataIndex: "system_type",
    key: "system_type",
  },
];

const AssignSystemsPickerModal = ({
  open,
  onClose,
  onConfirm,
  assignedIds,
}: AssignSystemsPickerModalProps) => {
  const [selectedKeys, setSelectedKeys] = useState<string[]>(assignedIds);
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setSelectedKeys(assignedIds);
    }
  }, [open, assignedIds]);

  const typeOptions = useMemo(() => {
    const types = [...new Set(MOCK_AVAILABLE_SYSTEMS.map((s) => s.system_type))];
    return types.map((t) => ({ label: t, value: t }));
  }, []);

  const filtered = useMemo(
    () =>
      MOCK_AVAILABLE_SYSTEMS.filter((s) => {
        const matchesSearch = s.system_name
          .toLowerCase()
          .includes(search.toLowerCase());
        const matchesType = !typeFilter || s.system_type === typeFilter;
        return matchesSearch && matchesType;
      }),
    [search, typeFilter],
  );

  const handleConfirm = () => {
    onConfirm(selectedKeys);
    setSearch("");
    setTypeFilter(null);
  };

  const handleCancel = () => {
    setSearch("");
    setTypeFilter(null);
    onClose();
  };

  return (
    <Modal
      title={
        <Flex align="center" justify="space-between" className="pr-6">
          <span>Data consumers</span>
          <Tag color="default" bordered={false}>{selectedKeys.length} selected</Tag>
        </Flex>
      }
      open={open}
      onCancel={handleCancel}
      onOk={handleConfirm}
      okText="Confirm"
      width={640}
      destroyOnClose
    >
      <Flex gap="small" className="mb-3">
        <Input
          placeholder="Search data consumers..."
          value={search}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
            setSearch(e.target.value)
          }
          allowClear
          style={{ flex: 1 }}
        />
        <Select
          placeholder="All types"
          options={typeOptions}
          value={typeFilter}
          onChange={setTypeFilter}
          allowClear
          style={{ width: 180 }}
        />
      </Flex>
      <Table<AvailableSystem>
        dataSource={filtered}
        columns={columns}
        rowKey="system_id"
        size="small"
        pagination={false}
        scroll={{ y: 400 }}
        rowSelection={{
          selectedRowKeys: selectedKeys,
          onChange: (keys) => setSelectedKeys(keys as string[]),
        }}
      />
    </Modal>
  );
};

export default AssignSystemsPickerModal;
