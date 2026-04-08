import "@xyflow/react/dist/style.css";

import {
  Background,
  type Edge,
  Handle,
  type Node,
  Position,
  ReactFlow,
  ReactFlowProvider,
} from "@xyflow/react";
import { Button, Flex, Input, Modal, Segmented, Tag, Text } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import { useMemo, useState } from "react";

import type { MockSystem } from "../../types";

interface DatasetsTabProps {
  system: MockSystem;
}

type ViewMode = "table" | "graph";

// --- Table View ---

const TableView = ({ system }: { system: MockSystem }) => {
  const [search, setSearch] = useState("");
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
    return true;
  });

  return (
    <Flex vertical gap={12}>
      <Flex justify="space-between" align="center">
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
        <Text type="secondary" className="text-xs">
          {filtered.length} datasets
        </Text>
      </Flex>

      <Flex vertical gap={0}>
        <Flex
          className="border-b border-solid border-[#f0f0f0] px-3 py-2"
          style={{ backgroundColor: palette.FIDESUI_CORINTH }}
        >
          <Text strong className="w-[18%] text-[10px] uppercase tracking-wider">
            Dataset
          </Text>
          <Text strong className="w-[24%] text-[10px] uppercase tracking-wider">
            Data Categories
          </Text>
          <Text strong className="w-[16%] text-[10px] uppercase tracking-wider">
            DSR Scope
          </Text>
          <Text strong className="w-[10%] text-[10px] uppercase tracking-wider">
            Fields
          </Text>
          <Text strong className="w-[12%] text-[10px] uppercase tracking-wider">
            Collections
          </Text>
          <Text
            strong
            className="w-1/5 text-right text-[10px] uppercase tracking-wider"
          >
            Actions
          </Text>
        </Flex>
        {filtered.map((ds) => (
          <Flex
            key={ds.key}
            align="center"
            className="border-b border-solid border-[#f5f5f5] px-3 py-2"
          >
            <Text className="w-[18%] text-xs">{ds.name}</Text>
            <div className="w-[24%]">
              {ds.dataCategories && ds.dataCategories.length > 0 ? (
                <Flex gap={3} wrap>
                  {ds.dataCategories.slice(0, 2).map((c) => (
                    <Tag
                      key={c}
                      color="corinth"
                      bordered={false}
                      className="!text-[9px]"
                    >
                      {c}
                    </Tag>
                  ))}
                  {ds.dataCategories.length > 2 && (
                    <Tag
                      color="corinth"
                      bordered={false}
                      className="!text-[9px]"
                    >
                      +{ds.dataCategories.length - 2}
                    </Tag>
                  )}
                </Flex>
              ) : (
                <Text type="secondary" className="text-[10px]">
                  —
                </Text>
              )}
            </div>
            <div className="w-[16%]">
              {ds.dsrScope && ds.dsrScope.length > 0 ? (
                <Flex gap={3} wrap>
                  {ds.dsrScope.map((s) => (
                    <Tag
                      key={s}
                      bordered={false}
                      color="olive"
                      className="!text-[9px]"
                    >
                      {s}
                    </Tag>
                  ))}
                </Flex>
              ) : (
                <Text type="secondary" className="text-[10px]">
                  —
                </Text>
              )}
            </div>
            <Text type="secondary" className="w-[10%] text-xs">
              {ds.fieldCount.toLocaleString()}
            </Text>
            <Text type="secondary" className="w-[12%] text-xs">
              {ds.collectionCount}
            </Text>
            <Flex className="w-1/5" justify="flex-end" gap={6}>
              <Button size="small" type="default" className="!text-[10px]">
                View
              </Button>
              <Button size="small" type="default" className="!text-[10px]">
                YAML
              </Button>
            </Flex>
          </Flex>
        ))}
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

// --- Graph View (React Flow) ---

const DatasetNode = ({
  data,
}: {
  data: { label: string; type: string; count?: number };
}) => (
  <div className="rounded-lg border border-solid border-[#e6e6e8] bg-white px-3 py-2 text-center shadow-sm">
    <Text
      className="block text-[10px] uppercase tracking-wider"
      type="secondary"
    >
      {data.type}
    </Text>
    <Text strong className="block text-xs">
      {data.label}
    </Text>
    {data.count !== undefined && (
      <Text type="secondary" className="block text-[10px]">
        {data.count} items
      </Text>
    )}
    <Handle
      type="source"
      position={Position.Right}
      className="!size-2 !border-[#999b83] !bg-[#999b83]"
    />
    <Handle
      type="target"
      position={Position.Left}
      className="!size-2 !border-[#b9704b] !bg-[#b9704b]"
    />
  </div>
);

const nodeTypes = { dataset: DatasetNode };

function buildGraph(system: MockSystem): { nodes: Node[]; edges: Edge[] } {
  const nodes: Node[] = [];
  const edges: Edge[] = [];
  let y = 0;

  system.datasets.forEach((ds, dsIdx) => {
    const dsId = `ds-${dsIdx}`;
    nodes.push({
      id: dsId,
      type: "dataset",
      position: { x: 0, y },
      data: { label: ds.name, type: "Dataset", count: ds.collectionCount },
    });

    // Collections
    const collectionsPerDs = Math.min(ds.collectionCount, 3);
    for (let c = 0; c < collectionsPerDs; c += 1) {
      const colId = `col-${dsIdx}-${c}`;
      nodes.push({
        id: colId,
        type: "dataset",
        position: { x: 280, y: y + c * 60 },
        data: {
          label: `collection_${c + 1}`,
          type: "Collection",
          count: Math.round(ds.fieldCount / ds.collectionCount),
        },
      });
      edges.push({
        id: `e-${dsId}-${colId}`,
        source: dsId,
        target: colId,
        animated: true,
        style: { stroke: "#cecac2" },
      });

      // Fields (show 2 per collection)
      for (let f = 0; f < 2; f += 1) {
        const fieldId = `field-${dsIdx}-${c}-${f}`;
        const catIdx = f % (ds.dataCategories?.length ?? 1);
        const cat = ds.dataCategories?.[catIdx] ?? "uncategorized";
        nodes.push({
          id: fieldId,
          type: "dataset",
          position: { x: 560, y: y + c * 60 + f * 50 },
          data: { label: cat.split(".").pop() ?? cat, type: "Field" },
        });
        edges.push({
          id: `e-${colId}-${fieldId}`,
          source: colId,
          target: fieldId,
          style: { stroke: "#e6e6e8" },
        });

        // Category
        const catNodeId = `cat-${dsIdx}-${c}-${f}`;
        nodes.push({
          id: catNodeId,
          type: "dataset",
          position: { x: 820, y: y + c * 60 + f * 50 },
          data: { label: cat, type: "Category" },
        });
        edges.push({
          id: `e-${fieldId}-${catNodeId}`,
          source: fieldId,
          target: catNodeId,
          style: { stroke: "#f0f0f0" },
        });
      }
    }

    y += Math.max(collectionsPerDs * 100, 120);
  });

  return { nodes, edges };
}

const GraphView = ({ system }: { system: MockSystem }) => {
  const { nodes, edges } = useMemo(() => buildGraph(system), [system]);

  return (
    <div className="h-[600px] w-full rounded-lg border border-solid border-[#f0f0f0]">
      <ReactFlowProvider>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          fitView
          proOptions={{ hideAttribution: true }}
          defaultEdgeOptions={{ type: "smoothstep" }}
        >
          <Background color="#f5f5f5" gap={20} />
        </ReactFlow>
      </ReactFlowProvider>
    </div>
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

const DatasetsTab = ({ system }: DatasetsTabProps) => {
  const [view, setView] = useState<ViewMode>("table");
  const [addOpen, setAddOpen] = useState(false);

  return (
    <Flex vertical gap={12}>
      <Flex justify="space-between" align="center">
        <Text type="secondary" className="text-xs">
          Datasets linked to this system, their classification categories, and
          DSR scope.
        </Text>
        <Flex gap={12} align="center">
          <Segmented
            size="small"
            options={[
              { label: "Table", value: "table" },
              { label: "Graph", value: "graph" },
            ]}
            value={view}
            onChange={(val) => setView(val as ViewMode)}
          />
          <Button type="primary" size="small" onClick={() => setAddOpen(true)}>
            + Add dataset
          </Button>
        </Flex>
      </Flex>
      {view === "table" ? (
        <TableView system={system} />
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
