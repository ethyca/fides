import "@xyflow/react/dist/style.css";

import { Background, BackgroundVariant, ReactFlow } from "@xyflow/react";
import { useMemo } from "react";

import useTreeLayout from "../hooks/useTreeLayout";
import { TaxonomyEntity } from "../types";
import TaxonomyNewNodeInput from "./TaxonomyNewNodeInput";
import TaxonomyTreeNode, { TaxonomyTreeNodeData } from "./TaxonomyTreeNode";

interface TaxonomyInteractiveTreeProps {
  taxonomyItems: TaxonomyEntity[];
  draftNewItem: Partial<TaxonomyEntity>;
  onTaxonomyItemClick: (taxonomyItem: TaxonomyEntity) => void;
  onAddButtonClick: (taxonomyItem: TaxonomyEntity) => void;
}

const TaxonomyInteractiveTree = ({
  taxonomyItems,
  draftNewItem,
  onTaxonomyItemClick,
  onAddButtonClick,
}: TaxonomyInteractiveTreeProps) => {
  // Add one node for each label
  const initialNodes = taxonomyItems.map((taxonomyItem) => {
    const data: TaxonomyTreeNodeData = {
      label: taxonomyItem.name ?? "",
      taxonomyItem,
      onTaxonomyItemClick,
      onAddButtonClick,
    };

    return {
      id: taxonomyItem.fides_key,
      position: { x: 0, y: 0 },
      data,
      type: "taxonomyTreeNode",
    };
  });

  // Add lines between each label and their parent (if it has one)
  const initialEdges = taxonomyItems
    .filter((t) => !!t.parent_key)
    .map((taxonomyItem) => ({
      id: `${taxonomyItem.fides_key}-${taxonomyItem.parent_key}`,
      source: taxonomyItem.parent_key!,
      target: taxonomyItem.fides_key,
    }));

  // Add the special input node and line for when we're adding a new label
  if (draftNewItem) {
    initialNodes.push({
      id: "draft-node",
      position: { x: 0, y: 0 },
      type: "newNodeInput",
      data: {},
    });
    initialEdges.push({
      id: "draft-line",
      source: draftNewItem.parent_key!,
      target: "draft-node",
    });
  }

  // use the layout library to place all nodes nicely on the screen as a tree
  const { nodes, edges } = useTreeLayout({
    nodes: initialNodes,
    edges: initialEdges,
    options: {
      direction: "LR",
    },
  });

  const nodeTypes = useMemo(
    () => ({
      taxonomyTreeNode: TaxonomyTreeNode,
      newNodeInput: TaxonomyNewNodeInput,
    }),
    [],
  );

  return (
    <div className="size-full  bg-[#fafafa]">
      <ReactFlow nodes={nodes} edges={edges} nodeTypes={nodeTypes}>
        <Background color="#eee" variant={BackgroundVariant.Dots} size={3} />
      </ReactFlow>
    </div>
  );
};

export default TaxonomyInteractiveTree;
