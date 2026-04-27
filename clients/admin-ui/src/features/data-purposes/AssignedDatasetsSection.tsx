import {
  Button,
  Dropdown,
  Empty,
  Flex,
  Icons,
  Popconfirm,
  Select,
  Switch,
  Table,
  Tag,
  Text,
  Title,
  Tooltip,
  useMessage,
} from "fidesui";
import { useCallback, useMemo, useState } from "react";

import { DebouncedSearchInput } from "~/features/common/DebouncedSearchInput";
import { isErrorResult } from "~/features/common/helpers";
import styles from "~/features/data-purposes/AssignedDatasetsSection.module.scss";

import AssignPickerModal from "./AssignPickerModal";
import {
  type AvailableDataset,
  type PurposeDatasetAssignment,
  useAcceptPurposeCategoriesMutation,
  useAddDatasetsToPurposeMutation,
  useGetDataPurposeByKeyQuery,
  useGetPurposeAvailableDatasetsQuery,
  useGetPurposeDatasetsQuery,
  useMarkPurposeCategoriesMisclassifiedMutation,
  useRemoveDatasetsFromPurposeMutation,
} from "./data-purpose.slice";

interface AssignedDatasetsSectionProps {
  fidesKey: string;
}

const MAX_VISIBLE_CATEGORIES = 2;

const renderDataCategories = (
  categories: string[] | undefined,
  definedSet: Set<string>,
) => {
  if (!categories || categories.length === 0) {
    return (
      <Tag bordered={false} className="cursor-default">
        None detected
      </Tag>
    );
  }
  const visible = categories.slice(0, MAX_VISIBLE_CATEGORIES);
  const remaining = categories.length - MAX_VISIBLE_CATEGORIES;
  const hidden = remaining > 0 ? categories.slice(MAX_VISIBLE_CATEGORIES) : [];
  return (
    <Flex gap={4} wrap="wrap">
      {visible.map((category) => (
        <Tag
          key={category}
          color={!definedSet.has(category) ? "error" : undefined}
          bordered={false}
        >
          {category}
        </Tag>
      ))}
      {remaining > 0 && (
        <Tooltip title={hidden.join(", ")}>
          <Tag bordered={false} className="cursor-default">
            +{remaining} more
          </Tag>
        </Tooltip>
      )}
    </Flex>
  );
};

const AssignedDatasetsSection = ({
  fidesKey,
}: AssignedDatasetsSectionProps) => {
  const [modalOpen, setModalOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [systemFilter, setSystemFilter] = useState<string | null>(null);
  const [selectedKeys, setSelectedKeys] = useState<string[]>([]);
  const [issuesOnly, setIssuesOnly] = useState(false);
  const message = useMessage();

  const { data: purpose } = useGetDataPurposeByKeyQuery(fidesKey);
  const { data: datasets = [], isLoading: isLoadingDatasets } =
    useGetPurposeDatasetsQuery(fidesKey);
  const [acceptCategories] = useAcceptPurposeCategoriesMutation();
  const [markMisclassified] = useMarkPurposeCategoriesMisclassifiedMutation();
  const [removeDatasets] = useRemoveDatasetsFromPurposeMutation();
  const { data: availableDatasets = [], isFetching: isFetchingAvailable } =
    useGetPurposeAvailableDatasetsQuery(fidesKey, { skip: !modalOpen });
  const [addDatasets, { isLoading: isAdding }] =
    useAddDatasetsToPurposeMutation();

  const handleAddSubmit = async (datasetFidesKeys: string[]) => {
    const result = await addDatasets({ fidesKey, datasetFidesKeys });
    if (isErrorResult(result)) {
      message.error("Could not add datasets");
      return false;
    }
    return true;
  };

  const definedSet = useMemo(
    () => new Set(purpose?.data_categories ?? []),
    [purpose?.data_categories],
  );

  const systemOptions = useMemo(() => {
    const systemNames = [
      ...new Set(datasets.map((dataset) => dataset.system_name)),
    ];
    return systemNames.map((systemName) => ({
      label: systemName,
      value: systemName,
    }));
  }, [datasets]);

  const undeclaredFor = useCallback(
    (dataset: PurposeDatasetAssignment) =>
      dataset.data_categories.filter((category) => !definedSet.has(category)),
    [definedSet],
  );

  const filtered = useMemo(
    () =>
      datasets.filter((dataset) => {
        const matchesSearch = dataset.dataset_name
          .toLowerCase()
          .includes(search.toLowerCase());
        const matchesSystem =
          !systemFilter || dataset.system_name === systemFilter;
        const matchesIssues = !issuesOnly || undeclaredFor(dataset).length > 0;
        return matchesSearch && matchesSystem && matchesIssues;
      }),
    [datasets, search, systemFilter, issuesOnly, undeclaredFor],
  );

  const selectedDatasets = useMemo(
    () =>
      datasets.filter((dataset) =>
        selectedKeys.includes(dataset.dataset_fides_key),
      ),
    [datasets, selectedKeys],
  );

  const selectedUndeclared = useMemo(() => {
    const categories = new Set<string>();
    selectedDatasets.forEach((dataset) =>
      undeclaredFor(dataset).forEach((category) => categories.add(category)),
    );
    return Array.from(categories);
  }, [selectedDatasets, undeclaredFor]);

  const hasSelection = selectedKeys.length > 0;
  const hasFlaggedSelection = selectedUndeclared.length > 0;

  const handleAccept = useCallback(
    async (categories: string[]) => {
      if (categories.length === 0) {
        return;
      }
      const result = await acceptCategories({ fidesKey, categories });
      if (isErrorResult(result)) {
        message.error("Could not accept categories");
        return;
      }
      message.success(
        categories.length === 1
          ? `Added "${categories[0]}" to defined categories`
          : `Added ${categories.length} categories to defined list`,
      );
    },
    [acceptCategories, fidesKey, message],
  );

  const handleMarkMisclassified = useCallback(
    async (datasetFidesKeys: string[], categories: string[]) => {
      if (categories.length === 0) {
        return;
      }
      const result = await markMisclassified({
        fidesKey,
        categories,
        datasetFidesKeys,
      });
      if (isErrorResult(result)) {
        message.error("Could not mark categories as misclassified");
        return;
      }
      message.success(
        categories.length === 1
          ? `Marked "${categories[0]}" as misclassified`
          : `Marked ${categories.length} categories as misclassified`,
      );
    },
    [markMisclassified, fidesKey, message],
  );

  const handleBulkRemoveDataset = async () => {
    const result = await removeDatasets({
      fidesKey,
      datasetFidesKeys: selectedKeys,
    });
    if (isErrorResult(result)) {
      message.error("Could not remove datasets");
      return;
    }
    message.success(
      selectedKeys.length === 1
        ? "Dataset removed from purpose"
        : `${selectedKeys.length} datasets removed from purpose`,
    );
    setSelectedKeys([]);
  };

  const handleRowAccept = useCallback(
    (record: PurposeDatasetAssignment) => handleAccept(undeclaredFor(record)),
    [handleAccept, undeclaredFor],
  );

  const handleRowRemoveCategory = useCallback(
    (record: PurposeDatasetAssignment) =>
      handleMarkMisclassified(
        [record.dataset_fides_key],
        undeclaredFor(record),
      ),
    [handleMarkMisclassified, undeclaredFor],
  );

  const handleBulkApprove = () => handleAccept(selectedUndeclared);
  const handleBulkRemoveCategory = () =>
    handleMarkMisclassified(selectedKeys, selectedUndeclared);

  const columns = useMemo(
    () => [
      {
        title: "Dataset",
        dataIndex: "dataset_name",
        key: "dataset_name",
        width: "20%",
        ellipsis: true,
        sorter: (
          left: PurposeDatasetAssignment,
          right: PurposeDatasetAssignment,
        ) => left.dataset_name.localeCompare(right.dataset_name),
        render: (_: unknown, record: PurposeDatasetAssignment) => {
          const undeclared = undeclaredFor(record);
          const flagged = undeclared.length > 0;
          return (
            <Flex align="center" gap={6}>
              {flagged && (
                <Tooltip
                  title={`Flagged: ${undeclared.length === 1 ? "new use" : "new uses"} detected (${undeclared.join(", ")})`}
                >
                  <span className={styles.warningIcon}>
                    <Icons.WarningAltFilled size={14} />
                  </span>
                </Tooltip>
              )}
              <span>{record.dataset_name}</span>
            </Flex>
          );
        },
      },
      {
        title: "System",
        dataIndex: "system_name",
        key: "system_name",
        width: "18%",
        ellipsis: true,
        sorter: (
          left: PurposeDatasetAssignment,
          right: PurposeDatasetAssignment,
        ) => left.system_name.localeCompare(right.system_name),
      },
      {
        title: "Data categories",
        dataIndex: "data_categories",
        key: "data_categories",
        width: "28%",
        render: (categories: string[]) =>
          renderDataCategories(categories, definedSet),
      },
      {
        title: "Steward",
        dataIndex: "steward",
        key: "steward",
        width: "12%",
        ellipsis: true,
        render: (value: string | undefined) =>
          value ? (
            <Text type="secondary" className="text-xs">
              {value}
            </Text>
          ) : (
            <Text type="secondary">—</Text>
          ),
      },
      {
        title: "Updated",
        dataIndex: "updated_at",
        key: "updated_at",
        width: "12%",
        sorter: (
          left: PurposeDatasetAssignment,
          right: PurposeDatasetAssignment,
        ) => {
          const leftTime = left.updated_at
            ? new Date(left.updated_at).getTime()
            : 0;
          const rightTime = right.updated_at
            ? new Date(right.updated_at).getTime()
            : 0;
          return leftTime - rightTime;
        },
        render: (value: string | undefined) => {
          if (!value) {
            return <Text type="secondary">—</Text>;
          }
          const date = new Date(value);
          if (Number.isNaN(date.getTime())) {
            return <Text type="secondary">—</Text>;
          }
          return (
            <Tooltip title={date.toLocaleString()}>
              <Text type="secondary" className="text-xs">
                {date.toLocaleDateString(undefined, {
                  month: "short",
                  day: "numeric",
                  year: "numeric",
                })}
              </Text>
            </Tooltip>
          );
        },
      },
      {
        title: "",
        key: "actions",
        width: "10%",
        render: (_: unknown, record: PurposeDatasetAssignment) => {
          const undeclared = undeclaredFor(record);
          const flagged = undeclared.length > 0;
          if (!flagged) {
            return null;
          }
          return (
            <Flex gap={2} justify="flex-end">
              <Tooltip title="Approve category">
                <Button
                  aria-label="Approve category"
                  type="text"
                  size="small"
                  icon={<Icons.Checkmark size={14} />}
                  onClick={(event) => {
                    event.stopPropagation();
                    handleRowAccept(record);
                  }}
                />
              </Tooltip>
              <Tooltip title="Remove category">
                <Button
                  aria-label="Remove category"
                  type="text"
                  size="small"
                  icon={<Icons.Close size={14} />}
                  onClick={(event) => {
                    event.stopPropagation();
                    handleRowRemoveCategory(record);
                  }}
                />
              </Tooltip>
            </Flex>
          );
        },
      },
    ],
    [definedSet, undeclaredFor, handleRowAccept, handleRowRemoveCategory],
  );

  const primaryActionsMenu = {
    items: [
      {
        key: "approve",
        label: "Approve categories",
        disabled: !hasFlaggedSelection,
        onClick: handleBulkApprove,
      },
      {
        key: "remove-category",
        label: "Remove categories",
        disabled: !hasFlaggedSelection,
        onClick: handleBulkRemoveCategory,
      },
      {
        key: "remove-dataset",
        danger: true,
        disabled: !hasSelection,
        label: (
          <Popconfirm
            title={`Remove ${selectedKeys.length} ${selectedKeys.length === 1 ? "dataset" : "datasets"} from purpose?`}
            okText="Remove"
            cancelText="Cancel"
            disabled={!hasSelection}
            onConfirm={handleBulkRemoveDataset}
          >
            <span>Remove dataset</span>
          </Popconfirm>
        ),
      },
    ],
  };

  return (
    <div>
      <Flex justify="space-between" align="flex-start" className="mb-3">
        <div>
          <Title level={5} className="!mb-1">
            Datasets assigned
          </Title>
          <Text type="secondary" className="text-xs">
            Datasets processed under this purpose. Detected categories are
            compared against the defined policy to surface risks.
          </Text>
        </div>
        <Button size="small" type="default" onClick={() => setModalOpen(true)}>
          + Add datasets
        </Button>
      </Flex>
      <Flex gap="small" className="mb-3" align="center" wrap="wrap">
        <DebouncedSearchInput
          placeholder="Search datasets..."
          value={search}
          onChange={setSearch}
          className="w-60"
        />
        {hasSelection && (
          <Text type="secondary" className="text-xs">
            {selectedKeys.length} selected
          </Text>
        )}
        <div className="flex-1" />
        <Flex align="center" gap={6}>
          <Switch size="small" checked={issuesOnly} onChange={setIssuesOnly} />
          <Text className="text-sm">Risks only</Text>
        </Flex>
        <Select
          aria-label="Filter by system"
          placeholder="All systems"
          options={systemOptions}
          value={systemFilter}
          onChange={setSystemFilter}
          allowClear
          size="middle"
          className="w-48"
        />
        <Dropdown trigger={["click"]} menu={primaryActionsMenu}>
          <Button size="middle" type="primary" disabled={!hasSelection}>
            Actions{" "}
            <Icons.ChevronDown size={12} className={styles.chevronDown} />
          </Button>
        </Dropdown>
      </Flex>
      <Table
        dataSource={filtered}
        columns={columns}
        size="small"
        loading={isLoadingDatasets}
        pagination={false}
        rowKey="dataset_fides_key"
        scroll={{ y: 320 }}
        tableLayout="fixed"
        rowSelection={{
          selectedRowKeys: selectedKeys,
          onChange: (keys) => setSelectedKeys(keys as string[]),
        }}
        locale={{
          emptyText: (
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description="No datasets assigned yet"
            >
              <Button size="small" onClick={() => setModalOpen(true)}>
                Add datasets
              </Button>
            </Empty>
          ),
        }}
      />
      <AssignPickerModal<AvailableDataset>
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title="Add datasets"
        searchPlaceholder="Search datasets..."
        filterPlaceholder="All systems"
        data={availableDatasets}
        isFetching={isFetchingAvailable}
        isSubmitting={isAdding}
        columns={[
          { title: "Dataset", dataIndex: "dataset_name", key: "dataset_name" },
          {
            title: "System",
            dataIndex: "system_name",
            key: "system_name",
            width: 180,
          },
        ]}
        getRowKey={(dataset) => dataset.dataset_fides_key}
        getSearchValue={(dataset) => dataset.dataset_name}
        getFilterValue={(dataset) => dataset.system_name}
        enableSelectAll
        onSubmit={handleAddSubmit}
      />
    </div>
  );
};

export default AssignedDatasetsSection;
