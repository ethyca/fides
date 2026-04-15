import { Button, Flex, Input, Modal, Select, Table, Tag } from "fidesui";
import { useEffect, useMemo, useState } from "react";

import { MOCK_AVAILABLE_DATASETS } from "./mockData";
import type { AvailableDataset } from "./types";

interface AddDatasetsModalProps {
  open: boolean;
  onClose: () => void;
  onConfirm: (keys: string[]) => void;
  assignedKeys: string[];
}

const columns = [
  {
    title: "Dataset",
    dataIndex: "dataset_name",
    key: "dataset_name",
  },
  {
    title: "System",
    dataIndex: "system_name",
    key: "system_name",
    width: 180,
  },
];

const AddDatasetsModal = ({
  open,
  onClose,
  onConfirm,
  assignedKeys,
}: AddDatasetsModalProps) => {
  const [selectedKeys, setSelectedKeys] = useState<string[]>(assignedKeys);
  const [search, setSearch] = useState("");
  const [systemFilter, setSystemFilter] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setSelectedKeys(assignedKeys);
    }
  }, [open, assignedKeys]);

  const systemOptions = useMemo(() => {
    const systems = [...new Set(MOCK_AVAILABLE_DATASETS.map((d) => d.system_name))];
    return systems.map((s) => ({ label: s, value: s }));
  }, []);

  const filtered = useMemo(
    () =>
      MOCK_AVAILABLE_DATASETS.filter((d) => {
        const matchesSearch = d.dataset_name
          .toLowerCase()
          .includes(search.toLowerCase());
        const matchesSystem =
          !systemFilter || d.system_name === systemFilter;
        return matchesSearch && matchesSystem;
      }),
    [search, systemFilter],
  );

  const handleConfirm = () => {
    onConfirm(selectedKeys);
    setSearch("");
    setSystemFilter(null);
  };

  const handleCancel = () => {
    setSearch("");
    setSystemFilter(null);
    onClose();
  };

  const filteredKeys = useMemo(
    () => filtered.map((d) => d.dataset_fides_key),
    [filtered],
  );
  const allFilteredSelected =
    filteredKeys.length > 0 &&
    filteredKeys.every((k) => selectedKeys.includes(k));
  const toggleSelectAllFiltered = () => {
    if (allFilteredSelected) {
      setSelectedKeys((prev) => prev.filter((k) => !filteredKeys.includes(k)));
    } else {
      setSelectedKeys((prev) =>
        Array.from(new Set([...prev, ...filteredKeys])),
      );
    }
  };

  return (
    <Modal
      title={
        <Flex align="center" justify="space-between" className="pr-6">
          <span>Add datasets</span>
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
          placeholder="Search datasets..."
          value={search}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
            setSearch(e.target.value)
          }
          allowClear
          style={{ flex: 1 }}
        />
        <Select
          placeholder="All systems"
          options={systemOptions}
          value={systemFilter}
          onChange={setSystemFilter}
          allowClear
          style={{ width: 180 }}
        />
        <Button
          size="middle"
          onClick={toggleSelectAllFiltered}
          disabled={filteredKeys.length === 0}
        >
          {allFilteredSelected ? "Clear all" : "Select all"}
        </Button>
      </Flex>
      <Table<AvailableDataset>
        dataSource={filtered}
        columns={columns}
        rowKey="dataset_fides_key"
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

export default AddDatasetsModal;
