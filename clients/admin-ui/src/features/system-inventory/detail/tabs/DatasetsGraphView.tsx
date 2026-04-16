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
import { Text } from "fidesui";
import { useMemo } from "react";

import type { MockSystem } from "../../types";

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

const DatasetsGraphView = ({ system }: { system: MockSystem }) => {
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

export default DatasetsGraphView;
