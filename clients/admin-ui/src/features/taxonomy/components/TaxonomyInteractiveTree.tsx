import "@xyflow/react/dist/style.css";

import { Background, BackgroundVariant, ReactFlow } from "@xyflow/react";
import { useMemo } from "react";

import useTreeLayout from "../hooks/useTreeLayout";
import { TaxonomyEntity } from "../types";
import { CoreTaxonomiesEnum } from "../types/CoreTaxonomiesEnum";
import TaxonomyNewNodeInput from "./TaxonomyNewNodeInput";
import TaxonomyTreeNode, { TaxonomyTreeNodeData } from "./TaxonomyTreeNode";

interface TaxonomyInteractiveTreeProps {
  taxonomyType: CoreTaxonomiesEnum;
  taxonomyItems: TaxonomyEntity[];
  draftNewItem: Partial<TaxonomyEntity>;
  onTaxonomyItemClick: (taxonomyItem: TaxonomyEntity) => void;
  onAddButtonClick: (taxonomyItem: TaxonomyEntity | undefined) => void;
}

const TaxonomyInteractiveTree = ({
  taxonomyType,
  taxonomyItems,
  draftNewItem,
  onTaxonomyItemClick,
  onAddButtonClick,
}: TaxonomyInteractiveTreeProps) => {
  // Root node (the taxonomy type)
  const ROOT_NODE_ID = "root";
  const rootNode = {
    id: ROOT_NODE_ID,
    position: { x: 0, y: 0 },
    data: {
      label: taxonomyType,
      taxonomyItem: null,
      onTaxonomyItemClick: null,
      onAddButtonClick,
    },
    type: "taxonomyTreeNode",
  };

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
  const initialEdges = taxonomyItems.map((taxonomyItem) => ({
    id: `${taxonomyItem.fides_key}-${taxonomyItem.parent_key}`,
    source: taxonomyItem.parent_key ?? "root",
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
      source: draftNewItem.parent_key || ROOT_NODE_ID,
      target: "draft-node",
    });
  }

  // use the layout library to place all nodes nicely on the screen as a tree
  const { nodes, edges } = useTreeLayout({
    nodes: [rootNode, ...initialNodes],
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
