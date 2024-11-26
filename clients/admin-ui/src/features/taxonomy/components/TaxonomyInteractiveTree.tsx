import "@xyflow/react/dist/style.css";

import {
  Background,
  BackgroundVariant,
  Controls,
  Edge,
  MiniMap,
  Node,
  NodeTypes,
  ReactFlow,
  ReactFlowProvider,
  useReactFlow,
} from "@xyflow/react";
import { useEffect, useMemo } from "react";

import useTreeLayout from "../hooks/useTreeLayout";
import { TaxonomyEntity } from "../types";
import { CoreTaxonomiesEnum } from "../types/CoreTaxonomiesEnum";
import TaxonomyTextInputNode, {
  TextInputNodeType,
} from "./TaxonomyTextInputNode";
import TaxonomyTreeNode, { TaxonomyTreeNodeType } from "./TaxonomyTreeNode";

interface TaxonomyInteractiveTreeProps {
  taxonomyType: CoreTaxonomiesEnum;
  taxonomyItems: TaxonomyEntity[];
  draftNewItem: Partial<TaxonomyEntity> | null;
  onTaxonomyItemClick: (taxonomyItem: TaxonomyEntity) => void;
  onAddButtonClick: (taxonomyItem: TaxonomyEntity | undefined) => void;
  onCancelDraftItem: () => void;
  onSubmitDraftItem: (label: string) => void;
}

const TaxonomyInteractiveTree = ({
  taxonomyType,
  taxonomyItems,
  draftNewItem,
  onTaxonomyItemClick,
  onAddButtonClick,
  onCancelDraftItem,
  onSubmitDraftItem,
}: TaxonomyInteractiveTreeProps) => {
  const { fitView } = useReactFlow();
  useEffect(() => {
    setTimeout(() => fitView(), 0);
  }, [fitView, taxonomyType]);

  // Root node (the taxonomy type)
  const ROOT_NODE_ID = "root";
  const rootNode: Node = {
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

  const nodes: Node[] = [rootNode];
  const edges: Edge[] = [];

  // Add one node for each label in the taxonomy
  taxonomyItems.forEach((taxonomyItem) => {
    const label =
      taxonomyItem.name || taxonomyItem.fides_key.split(".").pop() || "";
    const node: TaxonomyTreeNodeType = {
      id: taxonomyItem.fides_key,
      position: { x: 0, y: 0 },
      data: {
        label,
        taxonomyItem,
        onTaxonomyItemClick,
        onAddButtonClick,
      },
      type: "taxonomyTreeNode",
    };
    nodes.push(node);
  });

  // Add lines between each label and their parent (if it has one)
  taxonomyItems.forEach((taxonomyItem) => {
    const parentKey = taxonomyItem.parent_key || ROOT_NODE_ID;
    edges.push({
      id: `${parentKey}-${taxonomyItem.fides_key}`,
      source: parentKey,
      target: taxonomyItem.fides_key,
    });
  });

  // Add the special input node and line for when we're adding a new label
  if (draftNewItem) {
    const parentKey = draftNewItem.parent_key || ROOT_NODE_ID;
    const newLabelNode: TextInputNodeType = {
      id: "draft-node",
      position: { x: 0, y: 0 },
      type: "textInputNode",
      data: {
        parentKey,
        onCancel: onCancelDraftItem,
        onSubmit: onSubmitDraftItem,
      },
      hidden: !draftNewItem,
    };
    nodes.push(newLabelNode);
    edges.push({
      id: "draft-line",
      source: parentKey,
      target: "draft-node",
    });
  }

  // use the layout library to place all nodes nicely on the screen as a tree
  const { nodes: nodesAfterLayout, edges: edgesAfterLayout } = useTreeLayout({
    nodes,
    edges,
    options: {
      direction: "LR",
      stableOrder: true,
    },
  });

  const nodeTypes: NodeTypes = useMemo(
    () => ({
      taxonomyTreeNode: TaxonomyTreeNode,
      textInputNode: TaxonomyTextInputNode,
    }),
    [],
  );

  return (
    <div className="size-full  bg-[#fafafa]">
      <ReactFlow
        nodes={nodesAfterLayout}
        edges={edgesAfterLayout}
        nodeTypes={nodeTypes}
        maxZoom={2}
        minZoom={0.3}
      >
        <Background color="#eee" variant={BackgroundVariant.Dots} size={3} />
        <MiniMap nodeStrokeWidth={3} pannable />
        <Controls />
      </ReactFlow>
    </div>
  );
};

const TaxonomyInteractiveTreeWithProvider = (
  props: TaxonomyInteractiveTreeProps,
) => {
  return (
    <ReactFlowProvider>
      <TaxonomyInteractiveTree {...props} />
    </ReactFlowProvider>
  );
};

export default TaxonomyInteractiveTreeWithProvider;
