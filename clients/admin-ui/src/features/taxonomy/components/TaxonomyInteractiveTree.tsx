import "@xyflow/react/dist/style.css";

import { Background, BackgroundVariant, ReactFlow } from "@xyflow/react";
import { useMemo } from "react";

import useTreeLayout from "../hooks/useTreeLayout";
import { TaxonomyEntity } from "../types";
import TaxonomyTreeNode from "./TaxonomyTreeNode";

interface TaxonomyInteractiveTreeProps {
  taxonomyItems: TaxonomyEntity[];
  onTaxonomyItemClick?: (taxonomyItem: TaxonomyEntity) => void;
}

const TaxonomyInteractiveTree = ({
  taxonomyItems,
  onTaxonomyItemClick,
}: TaxonomyInteractiveTreeProps) => {
  const initialNodes = taxonomyItems.map((taxonomyItem) => ({
    id: taxonomyItem.fides_key,
    position: { x: 0, y: 0 },
    data: {
      label: taxonomyItem.name,
      taxonomyItem,
      onTaxonomyItemClick,
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

  const nodeTypes = useMemo(() => ({ customNode: TaxonomyTreeNode }), []);

  return (
    <div className="h-[600px] w-full border border-black">
      <ReactFlow nodes={nodes} edges={edges} nodeTypes={nodeTypes}>
        <Background color="#ccc" variant={BackgroundVariant.Dots} />
      </ReactFlow>
    </div>
  );
};

export default TaxonomyInteractiveTree;
