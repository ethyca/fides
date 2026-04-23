import { Flex, Input, Modal, Select, Table, Tag, useMessage } from "fidesui";
import { useEffect, useMemo, useState } from "react";

import { isErrorResult } from "~/features/common/helpers";

import {
  type AvailableSystem,
  useAssignSystemsToPurposeMutation,
  useGetPurposeAvailableSystemsQuery,
} from "./data-purpose.slice";

interface AssignSystemsPickerModalProps {
  fidesKey: string;
  open: boolean;
  onClose: () => void;
}

const columns = [
  { title: "System", dataIndex: "system_name", key: "system_name" },
  { title: "Type", dataIndex: "system_type", key: "system_type" },
];

const AssignSystemsPickerModal = ({
  fidesKey,
  open,
  onClose,
}: AssignSystemsPickerModalProps) => {
  const [selectedKeys, setSelectedKeys] = useState<string[]>([]);
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState<string | null>(null);
  const message = useMessage();

  const { data: availableSystems = [], isFetching } =
    useGetPurposeAvailableSystemsQuery(fidesKey, { skip: !open });
  const [assignSystems, { isLoading: isAssigning }] =
    useAssignSystemsToPurposeMutation();

  useEffect(() => {
    if (open) {
      setSelectedKeys([]);
    }
  }, [open]);

  const typeOptions = useMemo(() => {
    const types = [...new Set(availableSystems.map((s) => s.system_type))];
    return types.map((t) => ({ label: t, value: t }));
  }, [availableSystems]);

  const filtered = useMemo(
    () =>
      availableSystems.filter((s) => {
        const matchesSearch = s.system_name
          .toLowerCase()
          .includes(search.toLowerCase());
        const matchesType = !typeFilter || s.system_type === typeFilter;
        return matchesSearch && matchesType;
      }),
    [availableSystems, search, typeFilter],
  );

  const resetLocalState = () => {
    setSearch("");
    setTypeFilter(null);
    setSelectedKeys([]);
  };

  const handleConfirm = async () => {
    if (selectedKeys.length === 0) {
      resetLocalState();
      onClose();
      return;
    }
    const result = await assignSystems({
      fidesKey,
      systemIds: selectedKeys,
    });
    if (isErrorResult(result)) {
      message.error("Could not assign systems");
      return;
    }
    resetLocalState();
    onClose();
  };

  const handleCancel = () => {
    resetLocalState();
    onClose();
  };

  return (
    <Modal
      title={
        <Flex align="center" justify="space-between" className="pr-6">
          <span>Add data consumers</span>
          <Tag color="default" bordered={false}>
            {selectedKeys.length} selected
          </Tag>
        </Flex>
      }
      open={open}
      onCancel={handleCancel}
      onOk={handleConfirm}
      okText={selectedKeys.length > 0 ? "Add" : "Done"}
      confirmLoading={isAssigning}
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
          aria-label="Filter by type"
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
        loading={isFetching}
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
