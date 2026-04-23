import {
  Button,
  Flex,
  Input,
  Modal,
  Select,
  Table,
  Tag,
  useMessage,
} from "fidesui";
import { useEffect, useMemo, useState } from "react";

import { isErrorResult } from "~/features/common/helpers";

import {
  type AvailableDataset,
  useAddDatasetsToPurposeMutation,
  useGetPurposeAvailableDatasetsQuery,
} from "./data-purpose.slice";

interface AddDatasetsModalProps {
  fidesKey: string;
  open: boolean;
  onClose: () => void;
}

const columns = [
  { title: "Dataset", dataIndex: "dataset_name", key: "dataset_name" },
  { title: "System", dataIndex: "system_name", key: "system_name", width: 180 },
];

const AddDatasetsModal = ({
  fidesKey,
  open,
  onClose,
}: AddDatasetsModalProps) => {
  const [selectedKeys, setSelectedKeys] = useState<string[]>([]);
  const [search, setSearch] = useState("");
  const [systemFilter, setSystemFilter] = useState<string | null>(null);
  const message = useMessage();

  const { data: availableDatasets = [], isFetching } =
    useGetPurposeAvailableDatasetsQuery(fidesKey, { skip: !open });
  const [addDatasets, { isLoading: isAdding }] =
    useAddDatasetsToPurposeMutation();

  useEffect(() => {
    if (open) {
      setSelectedKeys([]);
    }
  }, [open]);

  const systemOptions = useMemo(() => {
    const systems = [...new Set(availableDatasets.map((d) => d.system_name))];
    return systems.map((s) => ({ label: s, value: s }));
  }, [availableDatasets]);

  const filtered = useMemo(
    () =>
      availableDatasets.filter((d) => {
        const matchesSearch = d.dataset_name
          .toLowerCase()
          .includes(search.toLowerCase());
        const matchesSystem = !systemFilter || d.system_name === systemFilter;
        return matchesSearch && matchesSystem;
      }),
    [availableDatasets, search, systemFilter],
  );

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

  const resetLocalState = () => {
    setSearch("");
    setSystemFilter(null);
    setSelectedKeys([]);
  };

  const handleConfirm = async () => {
    if (selectedKeys.length === 0) {
      resetLocalState();
      onClose();
      return;
    }
    const result = await addDatasets({
      fidesKey,
      datasetFidesKeys: selectedKeys,
    });
    if (isErrorResult(result)) {
      message.error("Could not add datasets");
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
          <span>Add datasets</span>
          <Tag color="default" bordered={false}>
            {selectedKeys.length} selected
          </Tag>
        </Flex>
      }
      open={open}
      onCancel={handleCancel}
      onOk={handleConfirm}
      okText={selectedKeys.length > 0 ? "Add" : "Done"}
      confirmLoading={isAdding}
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
          aria-label="Filter by system"
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

export default AddDatasetsModal;
