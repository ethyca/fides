import {
  Button,
  Dropdown,
  Flex,
  Icons,
  Input,
  Popconfirm,
  Select,
  Switch,
  Table,
  Tag,
  Text,
  Title,
  Tooltip,
} from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import { useMemo, useState } from "react";

import AddDatasetsModal from "./AddDatasetsModal";
import { MOCK_AVAILABLE_DATASETS } from "./mockData";
import type { PurposeDatasetAssignment } from "./types";

interface AssignedDatasetsSectionProps {
  datasets: PurposeDatasetAssignment[];
  definedCategories: string[];
  onDatasetsChange: (next: PurposeDatasetAssignment[]) => void;
  onAcceptCategories: (categories: string[]) => void;
  onMarkMisclassified: (
    datasetKeys: string[],
    categories: string[],
  ) => void;
  onRemoveDatasets: (datasetKeys: string[]) => void;
}

const MAX_VISIBLE_CATEGORIES = 2;

const renderDataCategories = (
  categories: string[] | undefined,
  definedSet: Set<string>,
  highlightUndeclared: boolean,
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
      {visible.map((c) => (
        <Tag
          key={c}
          color={
            highlightUndeclared && !definedSet.has(c) ? "error" : undefined
          }
          bordered={false}
        >
          {c}
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
  datasets,
  definedCategories,
  onDatasetsChange,
  onAcceptCategories,
  onMarkMisclassified,
  onRemoveDatasets,
}: AssignedDatasetsSectionProps) => {
  const [modalOpen, setModalOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [systemFilter, setSystemFilter] = useState<string | null>(null);
  const [selectedKeys, setSelectedKeys] = useState<string[]>([]);
  const [issuesOnly, setIssuesOnly] = useState(false);

  const definedSet = useMemo(
    () => new Set(definedCategories),
    [definedCategories],
  );

  const systemOptions = useMemo(() => {
    const systems = [...new Set(datasets.map((d) => d.system_name))];
    return systems.map((s) => ({ label: s, value: s }));
  }, [datasets]);

  const undeclaredFor = (dataset: PurposeDatasetAssignment) =>
    dataset.data_categories.filter((c) => !definedSet.has(c));

  const filtered = useMemo(
    () =>
      datasets.filter((d) => {
        const matchesSearch = d.dataset_name
          .toLowerCase()
          .includes(search.toLowerCase());
        const matchesSystem = !systemFilter || d.system_name === systemFilter;
        const matchesIssues =
          !issuesOnly || undeclaredFor(d).length > 0;
        return matchesSearch && matchesSystem && matchesIssues;
      }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [datasets, search, systemFilter, issuesOnly, definedSet],
  );

  const selectedDatasets = useMemo(
    () => datasets.filter((d) => selectedKeys.includes(d.dataset_fides_key)),
    [datasets, selectedKeys],
  );

  const selectedUndeclared = useMemo(() => {
    const set = new Set<string>();
    selectedDatasets.forEach((d) =>
      undeclaredFor(d).forEach((c) => set.add(c)),
    );
    return Array.from(set);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedDatasets, definedSet]);

  const hasSelection = selectedKeys.length > 0;
  const hasFlaggedSelection = selectedUndeclared.length > 0;

  const handleRowAccept = (record: PurposeDatasetAssignment) => {
    const undeclared = undeclaredFor(record);
    onAcceptCategories(undeclared);
  };

  const handleRowRemoveCategory = (record: PurposeDatasetAssignment) => {
    const undeclared = undeclaredFor(record);
    onMarkMisclassified([record.dataset_fides_key], undeclared);
  };

  const handleBulkApprove = () => {
    onAcceptCategories(selectedUndeclared);
  };

  const handleBulkRemoveCategory = () => {
    onMarkMisclassified(selectedKeys, selectedUndeclared);
  };

  const handleBulkRemoveDataset = () => {
    onRemoveDatasets(selectedKeys);
    setSelectedKeys([]);
  };

  const columns = useMemo(
    () => [
      {
        title: "Dataset",
        dataIndex: "dataset_name",
        key: "dataset_name",
        width: "20%",
        ellipsis: true,
        sorter: (
          a: PurposeDatasetAssignment,
          b: PurposeDatasetAssignment,
        ) => a.dataset_name.localeCompare(b.dataset_name),
        render: (_: unknown, record: PurposeDatasetAssignment) => {
          const undeclared = undeclaredFor(record);
          const highlighted =
            record.system_name === "BigQuery" && undeclared.length > 0;
          return (
            <Flex align="center" gap={6}>
              {highlighted && (
                <Tooltip
                  title={`Flagged: ${undeclared.length === 1 ? "new use" : "new uses"} detected (${undeclared.join(", ")})`}
                >
                  <span
                    style={{
                      color: palette.FIDESUI_ERROR,
                      lineHeight: 0,
                    }}
                  >
                    <Icons.WarningFilled size={14} />
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
          a: PurposeDatasetAssignment,
          b: PurposeDatasetAssignment,
        ) => a.system_name.localeCompare(b.system_name),
      },
      {
        title: "Data categories",
        dataIndex: "data_categories",
        key: "data_categories",
        width: "28%",
        render: (categories: string[], record: PurposeDatasetAssignment) =>
          renderDataCategories(
            categories,
            definedSet,
            record.system_name === "BigQuery",
          ),
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
          a: PurposeDatasetAssignment,
          b: PurposeDatasetAssignment,
        ) => {
          const aTime = a.updated_at ? new Date(a.updated_at).getTime() : 0;
          const bTime = b.updated_at ? new Date(b.updated_at).getTime() : 0;
          return aTime - bTime;
        },
        render: (value: string | undefined) => {
          if (!value) return <Text type="secondary">—</Text>;
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
          if (!flagged) return null;
          return (
            <Flex gap={2} justify="flex-end">
              <Tooltip title="Approve category">
                <Button
                  type="text"
                  size="small"
                  icon={<Icons.Checkmark size={14} />}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleRowAccept(record);
                  }}
                />
              </Tooltip>
              <Tooltip title="Remove category">
                <Button
                  type="text"
                  size="small"
                  icon={<Icons.Close size={14} />}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleRowRemoveCategory(record);
                  }}
                />
              </Tooltip>
            </Flex>
          );
        },
      },
    ],
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [definedSet],
  );

  const handleConfirm = (keys: string[]) => {
    const updated = keys
      .map((key) => {
        const existing = datasets.find(
          (d) => d.dataset_fides_key === key,
        );
        if (existing) return existing;
        const available = MOCK_AVAILABLE_DATASETS.find(
          (d) => d.dataset_fides_key === key,
        );
        if (!available) return null;
        return {
          dataset_fides_key: available.dataset_fides_key,
          dataset_name: available.dataset_name,
          system_name: available.system_name,
          collection_count: 0,
          data_categories: [],
        };
      })
      .filter(Boolean) as PurposeDatasetAssignment[];
    onDatasetsChange(updated);
    setModalOpen(false);
  };

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
            Datasets processed under this purpose. Detected categories are compared against the defined policy to surface risks.
          </Text>
        </div>
        <Button size="small" type="default" onClick={() => setModalOpen(true)}>
          + Add datasets
        </Button>
      </Flex>
      <Flex
        gap="small"
        className="mb-3"
        align="center"
        wrap="wrap"
      >
        <Input
          placeholder="Search datasets..."
          value={search}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
            setSearch(e.target.value)
          }
          allowClear
          size="middle"
          style={{ width: 240 }}
        />
        {hasSelection && (
          <Text type="secondary" className="text-xs">
            {selectedKeys.length} selected
          </Text>
        )}
        <div style={{ flex: 1 }} />
        <Flex align="center" gap={6}>
          <Switch
            size="small"
            checked={issuesOnly}
            onChange={setIssuesOnly}
          />
          <Text className="text-sm">Issues only</Text>
        </Flex>
        <Select
          placeholder="All systems"
          options={systemOptions}
          value={systemFilter}
          onChange={setSystemFilter}
          allowClear
          size="middle"
          style={{ width: 180 }}
        />
        <Dropdown trigger={["click"]} menu={primaryActionsMenu}>
          <Button
            size="middle"
            type="primary"
            disabled={!hasSelection}
          >
            Actions{" "}
            <Icons.ChevronDown size={12} style={{ marginLeft: 2 }} />
          </Button>
        </Dropdown>
      </Flex>
      <Table
        dataSource={filtered}
        columns={columns}
        size="small"
        pagination={false}
        rowKey="dataset_fides_key"
        scroll={{ y: 320 }}
        tableLayout="fixed"
        rowSelection={{
          selectedRowKeys: selectedKeys,
          onChange: (keys) => setSelectedKeys(keys as string[]),
        }}
      />
      <AddDatasetsModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onConfirm={handleConfirm}
        assignedKeys={datasets.map((d) => d.dataset_fides_key)}
      />
    </div>
  );
};

export default AssignedDatasetsSection;
