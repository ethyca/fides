import "@xyflow/react/dist/style.css";

import {
  Background,
  BackgroundVariant,
  Handle,
  Position,
  ReactFlow,
} from "@xyflow/react";
import { AntButton, SmallAddIcon } from "fidesui";
import { useCallback, useMemo } from "react";

import useTreeLayout from "../hooks/useTreeLayout";
import { TaxonomyEntity } from "../types";

interface TaxonomyInteractiveFlowVisualizationProps {
  taxonomyItems: TaxonomyEntity[];
  onTaxonomyItemClick?: (taxonomyItem: TaxonomyEntity) => void;
}

interface NodeData {
  label: string;
  taxonomyItem: TaxonomyEntity;
}

const TaxonomyInteractiveFlowVisualization = ({
  taxonomyItems,
  onTaxonomyItemClick,
}: TaxonomyInteractiveFlowVisualizationProps) => {
  const initialNodes = taxonomyItems.map((taxonomyItem) => ({
    id: taxonomyItem.fides_key,
    position: { x: 0, y: 0 },
    data: {
      label: taxonomyItem.name,
      taxonomyItem,
    },
    type: "customNode",
  }));

  const initialEdges = taxonomyItems
    .filter((t) => !!t.parent_key)
    .map((taxonomyItem) => ({
      id: `${taxonomyItem.fides_key}-${taxonomyItem.parent_key}`,
      source: taxonomyItem.parent_key!,
      target: taxonomyItem.fides_key,
    }));

  const { nodes, edges } = useTreeLayout({
    nodes: initialNodes,
    edges: initialEdges,
    options: {
      direction: "LR",
    },
  });

  const CustomNode = useCallback(({ data }: { data: NodeData }) => {
    return (
      <div className="group relative">
        <button
          type="button"
          className=" rounded px-4 py-1 transition-colors group-hover:bg-black group-hover:text-white"
          onClick={() => onTaxonomyItemClick?.(data.taxonomyItem!)}
        >
          {data.label}
        </button>

        <Handle type="target" position={Position.Left} />
        <Handle type="source" position={Position.Right} />
        <div className="absolute left-full top-0 hidden pl-2 group-hover:block">
          <AntButton
            type="default"
            className="bg-white pt-0.5 shadow-[0_1px_3px_0px_rgba(0,0,0,0.1)] "
            icon={<SmallAddIcon className="text-xl" />}
          />
        </div>
      </div>
    );
  }, []);

  const nodeTypes = useMemo(() => ({ customNode: CustomNode }), [CustomNode]);

  return (
    <div className="h-[600px] w-full border border-black">
      <ReactFlow nodes={nodes} edges={edges} nodeTypes={nodeTypes}>
        <Background color="#ccc" variant={BackgroundVariant.Dots} />
      </ReactFlow>
    </div>
  );
};

export default TaxonomyInteractiveFlowVisualization;
