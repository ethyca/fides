import dynamic from "next/dynamic";
import {
  Button,
  Checkbox,
  Dropdown,
  Flex,
  Icons,
  Input,
  Modal,
  Popover,
  Segmented,
  Select,
  Tag,
  Text,
  Tooltip,
  useMessage,
} from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import { useMemo, useState } from "react";

import { MOCK_PURPOSES } from "~/features/data-purposes/mockData";

import type { MockSystem } from "../../types";

const GraphView = dynamic(
  () => import("./DatasetsGraphView"),
  { ssr: false },
);

const CURRENT_USER = "Jack Gale";

interface DatasetsTabProps {
  system: MockSystem;
}

type ViewMode = "table" | "graph";

// --- Table View ---

interface TableViewProps {
  system: MockSystem;
  selectedKeys: Set<string>;
  onSelectionChange: (keys: Set<string>) => void;
}

const PURPOSE_OPTIONS = MOCK_PURPOSES.map((p) => ({
  label: p.name,
  value: p.name,
}));

const PurposeCell = ({
  datasetKey,
  assigned,
  onAdd,
  onRemove,
}: {
  datasetKey: string;
  assigned: string[];
  onAdd: (purpose: string) => void;
  onRemove: (purpose: string) => void;
}) => {
  const [open, setOpen] = useState(false);
  const isEmpty = assigned.length === 0;
  const available = PURPOSE_OPTIONS.filter(
    (o) => !assigned.includes(o.value),
  );

  const popoverContent = (
    <Flex vertical gap={4} style={{ width: 240 }}>
      {available.map((opt) => (
        <div
          key={opt.value}
          className="cursor-pointer rounded px-2 py-1.5 text-xs hover:bg-[#f5f5f5]"
          onClick={() => {
            onAdd(opt.value);
            if (available.length <= 1) setOpen(false);
          }}
        >
          {opt.label}
        </div>
      ))}
      {available.length === 0 && (
        <Text type="secondary" className="px-2 py-1 text-xs">
          All purposes assigned
        </Text>
      )}
    </Flex>
  );

  return (
    <Flex
      align="center"
      gap={8}
      className="min-w-0"
      style={
        isEmpty
          ? {
              backgroundColor: "#fff7e6",
              border: "1px solid #ffd591",
              borderRadius: 6,
              padding: "4px 10px",
            }
          : undefined
      }
    >
      <Popover
        content={popoverContent}
        trigger="click"
        open={open}
        onOpenChange={setOpen}
        placement="bottomLeft"
        arrow={false}
      >
        <Tooltip title="Assign purpose">
          <Button
            type="text"
            size="small"
            icon={<Icons.Add size={14} />}
            className={
              isEmpty
                ? "!text-[#fa8c16] hover:!bg-[#fff7e6]"
                : "!text-gray-400 hover:!text-gray-600"
            }
            style={{ width: 22, height: 22, padding: 0, flexShrink: 0 }}
          />
        </Tooltip>
      </Popover>
      {isEmpty ? (
        <Text className="whitespace-nowrap text-[11px]" style={{ color: "#d46b08" }}>
          Purpose required
        </Text>
      ) : (
        <Flex gap={4} align="center" className="min-w-0 overflow-hidden">
          {assigned.map((p) => (
            <Tag
              key={p}
              bordered={false}
              closable
              onClose={(e) => {
                e.preventDefault();
                onRemove(p);
              }}
              className="!m-0 !shrink-0 !text-[10px]"
            >
              {p}
            </Tag>
          ))}
        </Flex>
      )}
    </Flex>
  );
};

const TableView = ({
  system,
  selectedKeys,
  onSelectionChange,
}: TableViewProps) => {
  const [search, setSearch] = useState("");
  const [stewardFilter, setStewardFilter] = useState<string | null>(
    CURRENT_USER,
  );
  const [purposeAssignments, setPurposeAssignments] = useState<
    Record<string, string[]>
  >(
    Object.fromEntries(
      system.datasets.map((ds) => [ds.key, ds.purposes ?? []]),
    ),
  );

  const stewardOptions = useMemo(() => {
    const names = new Set<string>();
    system.datasets.forEach((ds) => {
      if (ds.steward) {
        names.add(ds.steward);
      }
    });
    return [...names].sort().map((n) => ({ label: n, value: n }));
  }, [system.datasets]);

  const filtered = system.datasets.filter((ds) => {
    if (search) {
      const q = search.toLowerCase();
      if (
        !ds.name.toLowerCase().includes(q) &&
        !ds.key.toLowerCase().includes(q) &&
        !ds.category?.toLowerCase().includes(q) &&
        !ds.dataCategories?.some((c) => c.toLowerCase().includes(q))
      ) {
        return false;
      }
    }
    if (stewardFilter && ds.steward !== stewardFilter) {
      return false;
    }
    return true;
  });

  const allFilteredSelected =
    filtered.length > 0 && filtered.every((ds) => selectedKeys.has(ds.key));
  const someSelected = filtered.some((ds) => selectedKeys.has(ds.key));

  const toggleAll = () => {
    if (allFilteredSelected) {
      const next = new Set(selectedKeys);
      filtered.forEach((ds) => next.delete(ds.key));
      onSelectionChange(next);
    } else {
      const next = new Set(selectedKeys);
      filtered.forEach((ds) => next.add(ds.key));
      onSelectionChange(next);
    }
  };

  const toggleRow = (key: string) => {
    const next = new Set(selectedKeys);
    if (next.has(key)) {
      next.delete(key);
    } else {
      next.add(key);
    }
    onSelectionChange(next);
  };

  return (
    <Flex vertical gap={12}>
      <Flex justify="space-between" align="center">
        <Flex gap={8} align="center">
          <Input
            placeholder="Search datasets..."
            value={search}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              setSearch(e.target.value)
            }
            allowClear
            size="small"
            style={{ width: 240 }}
          />
          <Text type="secondary" className="text-xs whitespace-nowrap">
            {selectedKeys.size > 0
              ? `${selectedKeys.size} selected`
              : `${filtered.length} datasets`}
          </Text>
        </Flex>
        <Select
          aria-label="Filter by steward"
          placeholder="All stewards"
          options={stewardOptions}
          value={stewardFilter}
          onChange={setStewardFilter}
          allowClear
          size="small"
          style={{ width: 180 }}
        />
      </Flex>

      <Flex vertical gap={0}>
        <Flex
          className="border-b border-solid px-3 py-2"
          align="center"
          style={{
            backgroundColor: palette.FIDESUI_CORINTH,
            borderColor: palette.FIDESUI_NEUTRAL_100,
          }}
        >
          <div className="w-[3%]">
            <Checkbox
              checked={allFilteredSelected}
              indeterminate={someSelected && !allFilteredSelected}
              onChange={toggleAll}
              aria-label="Select all datasets"
            />
          </div>
          <Text strong className="w-[15%] text-xs">
            Dataset
          </Text>
          <Text strong className="w-[10%] text-xs">
            Steward
          </Text>
          <Text strong className="w-[20%] text-xs">
            Data categories
          </Text>
          <Text strong className="w-[22%] text-xs">
            Purpose
          </Text>
          <Text strong className="w-[7%] text-xs">
            Fields
          </Text>
          <Text strong className="w-[10%] text-xs">
            Collections
          </Text>
          <Text
            strong
            className="w-[13%] text-right text-xs"
          >
            Actions
          </Text>
        </Flex>
        {filtered.map((ds) => {
          const isSelected = selectedKeys.has(ds.key);
          return (
            <Flex
              key={ds.key}
              align="center"
              className="border-b border-solid px-3 py-2"
              style={{
                borderColor: palette.FIDESUI_NEUTRAL_75,
                backgroundColor: isSelected
                  ? palette.FIDESUI_BG_DEFAULT
                  : undefined,
              }}
            >
              <div className="w-[3%]">
                <Checkbox
                  checked={isSelected}
                  onChange={() => toggleRow(ds.key)}
                  aria-label={`Select ${ds.name}`}
                />
              </div>
              <Text className="w-[15%] text-xs">{ds.name}</Text>
              <Text type="secondary" className="w-[10%] text-xs">
                {ds.steward ?? "—"}
              </Text>
              <div className="w-[20%] pr-2">
                {ds.dataCategories && ds.dataCategories.length > 0 ? (
                  <Flex gap={4} align="center" className="overflow-hidden">
                    {ds.dataCategories.slice(0, 2).map((c) => (
                      <Tag
                        key={c}
                        bordered={false}
                        className="!m-0 !shrink-0 !text-[10px]"
                      >
                        {c}
                      </Tag>
                    ))}
                    {ds.dataCategories.length > 2 && (
                      <Tag
                        bordered={false}
                        className="!m-0 !shrink-0 !text-[10px]"
                      >
                        +{ds.dataCategories.length - 2}
                      </Tag>
                    )}
                  </Flex>
                ) : (
                  <Text type="secondary" className="text-xs">
                    —
                  </Text>
                )}
              </div>
              <div className="w-[22%] pr-2">
                {ds.steward === CURRENT_USER ? (
                  <PurposeCell
                    datasetKey={ds.key}
                    assigned={purposeAssignments[ds.key] ?? []}
                    onAdd={(purpose) =>
                      setPurposeAssignments((prev) => ({
                        ...prev,
                        [ds.key]: [...(prev[ds.key] ?? []), purpose],
                      }))
                    }
                    onRemove={(purpose) =>
                      setPurposeAssignments((prev) => ({
                        ...prev,
                        [ds.key]: (prev[ds.key] ?? []).filter(
                          (p) => p !== purpose,
                        ),
                      }))
                    }
                  />
                ) : (
                  <div className="overflow-hidden">
                    {(purposeAssignments[ds.key] ?? []).length > 0 ? (
                      <Flex gap={4} align="center" className="overflow-hidden">
                        {(purposeAssignments[ds.key] ?? []).map((p) => (
                          <Tag
                            key={p}
                            bordered={false}
                            className="!m-0 !shrink-0 !text-[10px]"
                          >
                            {p}
                          </Tag>
                        ))}
                      </Flex>
                    ) : (
                      <Text type="secondary" className="text-xs">
                        —
                      </Text>
                    )}
                  </div>
                )}
              </div>
              <Text type="secondary" className="w-[7%] text-xs">
                {ds.fieldCount.toLocaleString()}
              </Text>
              <Text type="secondary" className="w-[10%] text-xs">
                {ds.collectionCount}
              </Text>
              <Flex className="w-[13%]" justify="flex-end" gap={6}>
                <Button size="small" type="default" className="!text-[10px]">
                  View
                </Button>
                <Button size="small" type="default" className="!text-[10px]">
                  YAML
                </Button>
              </Flex>
            </Flex>
          );
        })}
        {filtered.length === 0 && (
          <Flex justify="center" className="py-6">
            <Text type="secondary" className="text-xs">
              No datasets match filters
            </Text>
          </Flex>
        )}
      </Flex>
    </Flex>
  );
};

// --- Main ---

const AVAILABLE_DATASETS = [
  {
    key: "stripe_payments",
    name: "stripe_payments",
    system: "Stripe",
    fields: 45,
  },
  { key: "sf_contacts", name: "sf_contacts", system: "Salesforce", fields: 55 },
  { key: "sf_accounts", name: "sf_accounts", system: "Salesforce", fields: 30 },
  {
    key: "amplitude_events",
    name: "amplitude_events",
    system: "Amplitude",
    fields: 93,
  },
  {
    key: "snowflake_raw_events",
    name: "snowflake_raw_events",
    system: "Snowflake",
    fields: 85,
  },
  {
    key: "snowflake_user_profiles",
    name: "snowflake_user_profiles",
    system: "Snowflake",
    fields: 35,
  },
  {
    key: "bq_analytics_events",
    name: "bq_analytics_events",
    system: "BigQuery",
    fields: 65,
  },
  { key: "bq_user_data", name: "bq_user_data", system: "BigQuery", fields: 42 },
  {
    key: "segment_events",
    name: "segment_events",
    system: "Segment",
    fields: 73,
  },
  {
    key: "zendesk_tickets",
    name: "zendesk_tickets",
    system: "Zendesk",
    fields: 49,
  },
];

const DatasetPickerModal = ({
  open,
  onClose,
  existing,
}: {
  open: boolean;
  onClose: () => void;
  existing: string[];
}) => {
  const [pickerSearch, setPickerSearch] = useState("");
  const [selected, setSelected] = useState<string[]>([]);

  const available = AVAILABLE_DATASETS.filter(
    (d) =>
      !existing.includes(d.key) &&
      (!pickerSearch ||
        d.name.toLowerCase().includes(pickerSearch.toLowerCase()) ||
        d.system.toLowerCase().includes(pickerSearch.toLowerCase())),
  );

  return (
    <Modal
      title="Add dataset reference"
      open={open}
      onCancel={() => {
        setSelected([]);
        setPickerSearch("");
        onClose();
      }}
      onOk={() => {
        setSelected([]);
        setPickerSearch("");
        onClose();
      }}
      okText={`Add ${selected.length > 0 ? selected.length : ""} dataset${selected.length !== 1 ? "s" : ""}`}
      okButtonProps={{ disabled: selected.length === 0 }}
      width={560}
    >
      <Flex vertical gap={12} className="mt-3">
        <Input
          placeholder="Search datasets by name or system..."
          value={pickerSearch}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
            setPickerSearch(e.target.value)
          }
          allowClear
          size="small"
        />
        <div className="max-h-[320px] overflow-y-auto">
          {available.map((ds) => {
            const isSelected = selected.includes(ds.key);
            return (
              <Flex
                key={ds.key}
                align="center"
                justify="space-between"
                className="cursor-pointer border-b border-solid border-[#f5f5f5] px-3 py-2.5 hover:bg-[#fafafa]"
                onClick={() =>
                  setSelected(
                    isSelected
                      ? selected.filter((k) => k !== ds.key)
                      : [...selected, ds.key],
                  )
                }
              >
                <Flex vertical>
                  <Text strong={isSelected} className="text-xs">
                    {ds.name}
                  </Text>
                  <Text type="secondary" className="text-[10px]">
                    {ds.system} &middot; {ds.fields} fields
                  </Text>
                </Flex>
                {isSelected && (
                  <Tag
                    color="success"
                    bordered={false}
                    className="!text-[10px]"
                  >
                    Selected
                  </Tag>
                )}
              </Flex>
            );
          })}
          {available.length === 0 && (
            <Flex justify="center" className="py-6">
              <Text type="secondary" className="text-xs">
                No datasets available
              </Text>
            </Flex>
          )}
        </div>
      </Flex>
    </Modal>
  );
};

const ACTION_ITEMS = [
  { key: "add-purpose", label: "Add purpose" },
  { key: "add-category", label: "Add data category" },
  { type: "divider" as const },
  { key: "delete", label: "Delete dataset", danger: true },
];

const DatasetsTab = ({ system }: DatasetsTabProps) => {
  const [view, setView] = useState<ViewMode>("table");
  const [addOpen, setAddOpen] = useState(false);
  const [selectedKeys, setSelectedKeys] = useState<Set<string>>(new Set());
  const msg = useMessage();

  const handleAction = (actionKey: string) => {
    if (selectedKeys.size === 0) {
      return;
    }
    const action = ACTION_ITEMS.find((a) => a.key === actionKey);
    msg.success(
      `${action?.label ?? actionKey} applied to ${selectedKeys.size} dataset${selectedKeys.size !== 1 ? "s" : ""}`,
    );
    setSelectedKeys(new Set());
  };

  return (
    <Flex vertical gap={12}>
      <Flex justify="space-between" align="center">
        <Text type="secondary" className="text-xs">
          Datasets linked to this system, their classification categories, and
          DSR scope.
        </Text>
        <Flex gap={8} align="center">
          <Segmented
            size="small"
            options={[
              {
                label: <Icons.DataTable size={14} />,
                value: "table",
              },
              {
                label: <Icons.Fork size={14} />,
                value: "graph",
              },
            ]}
            value={view}
            onChange={(val) => setView(val as ViewMode)}
          />
          <Button size="small" onClick={() => setAddOpen(true)}>
            + Add dataset
          </Button>
          <Dropdown
            menu={{
              items: ACTION_ITEMS,
              onClick: ({ key }) => handleAction(key),
            }}
            trigger={["click"]}
            disabled={selectedKeys.size === 0}
          >
            <Button type="primary" size="small">
              Actions <Icons.ChevronDown size={12} />
            </Button>
          </Dropdown>
        </Flex>
      </Flex>
      {view === "table" ? (
        <TableView
          system={system}
          selectedKeys={selectedKeys}
          onSelectionChange={setSelectedKeys}
        />
      ) : (
        <GraphView system={system} />
      )}
      <DatasetPickerModal
        open={addOpen}
        onClose={() => setAddOpen(false)}
        existing={system.datasets.map((d) => d.key)}
      />
    </Flex>
  );
};

export default DatasetsTab;
