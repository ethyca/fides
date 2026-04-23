import {
  Button,
  ColumnsType,
  Flex,
  Input,
  Modal,
  Select,
  Table,
  Tag,
} from "fidesui";
import { useEffect, useMemo, useState } from "react";

interface AssignPickerModalProps<T> {
  open: boolean;
  onClose: () => void;
  title: string;
  searchPlaceholder: string;
  filterPlaceholder: string;
  data: T[];
  isFetching: boolean;
  isSubmitting: boolean;
  columns: ColumnsType<T>;
  getRowKey: (item: T) => string;
  getSearchValue: (item: T) => string;
  getFilterValue: (item: T) => string;
  enableSelectAll?: boolean;
  onSubmit: (keys: string[]) => Promise<boolean>;
}

const AssignPickerModal = <T,>({
  open,
  onClose,
  title,
  searchPlaceholder,
  filterPlaceholder,
  data,
  isFetching,
  isSubmitting,
  columns,
  getRowKey,
  getSearchValue,
  getFilterValue,
  enableSelectAll = false,
  onSubmit,
}: AssignPickerModalProps<T>) => {
  const [selectedKeys, setSelectedKeys] = useState<string[]>([]);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setSelectedKeys([]);
    }
  }, [open]);

  const filterOptions = useMemo(() => {
    const values = [...new Set(data.map(getFilterValue))];
    return values.map((v) => ({ label: v, value: v }));
  }, [data, getFilterValue]);

  const filtered = useMemo(
    () =>
      data.filter((item) => {
        const matchesSearch = getSearchValue(item)
          .toLowerCase()
          .includes(search.toLowerCase());
        const matchesFilter = !filter || getFilterValue(item) === filter;
        return matchesSearch && matchesFilter;
      }),
    [data, search, filter, getSearchValue, getFilterValue],
  );

  const filteredKeys = useMemo(
    () => filtered.map(getRowKey),
    [filtered, getRowKey],
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
    setFilter(null);
    setSelectedKeys([]);
  };

  const handleConfirm = async () => {
    if (selectedKeys.length === 0) {
      resetLocalState();
      onClose();
      return;
    }
    const ok = await onSubmit(selectedKeys);
    if (!ok) {
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
          <span>{title}</span>
          <Tag color="default" bordered={false}>
            {selectedKeys.length} selected
          </Tag>
        </Flex>
      }
      open={open}
      onCancel={handleCancel}
      onOk={handleConfirm}
      okText={selectedKeys.length > 0 ? "Add" : "Done"}
      confirmLoading={isSubmitting}
      width={640}
      destroyOnClose
    >
      <Flex gap="small" className="mb-3">
        <Input
          placeholder={searchPlaceholder}
          value={search}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
            setSearch(e.target.value)
          }
          allowClear
          style={{ flex: 1 }}
        />
        <Select
          aria-label={filterPlaceholder}
          placeholder={filterPlaceholder}
          options={filterOptions}
          value={filter}
          onChange={setFilter}
          allowClear
          style={{ width: 180 }}
        />
        {enableSelectAll && (
          <Button
            size="middle"
            onClick={toggleSelectAllFiltered}
            disabled={filteredKeys.length === 0}
          >
            {allFilteredSelected ? "Clear all" : "Select all"}
          </Button>
        )}
      </Flex>
      <Table<T>
        dataSource={filtered}
        columns={columns}
        rowKey={getRowKey}
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

export default AssignPickerModal;
