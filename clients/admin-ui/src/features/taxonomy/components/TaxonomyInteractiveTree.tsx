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
import palette from "fidesui/src/palette/palette.module.scss";
import { useEffect, useMemo } from "react";

import { TAXONOMY_ROOT_NODE_ID } from "../constants";
import { TaxonomyTreeHoverProvider } from "../context/TaxonomyTreeHoverContext";
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
  const rootNode: Node = {
    id: TAXONOMY_ROOT_NODE_ID,
    position: { x: 0, y: 0 },
    data: {
      label: taxonomyType,
      taxonomyItem: {
        fides_key: TAXONOMY_ROOT_NODE_ID,
      },
      onTaxonomyItemClick: null,
      onAddButtonClick,
      hasChildren: taxonomyItems.length !== 0,
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
        hasChildren: false,
      },
      type: "taxonomyTreeNode",
    };
    nodes.push(node);
  });

  // Add lines between each label and their parent (if it has one)
  taxonomyItems.forEach((taxonomyItem) => {
    const parentKey = taxonomyItem.parent_key || TAXONOMY_ROOT_NODE_ID;
    edges.push({
      id: `${parentKey}-${taxonomyItem.fides_key}`,
      source: parentKey,
      target: taxonomyItem.fides_key,
      style: { stroke: palette.FIDESUI_SANDSTONE, strokeWidth: 1 },
    });

    // Update hasChildren for parent to true
    const parentNode = nodes.find((node) => node.id === parentKey);
    if (parentNode) {
      parentNode.data.hasChildren = true;
    }
  });

  // Add the special input node and line for when we're adding a new label
  if (draftNewItem) {
    const parentKey = draftNewItem.parent_key || TAXONOMY_ROOT_NODE_ID;
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
      animated: true,
    });

    // Update hasChildren for parent to true
    const parentNode = nodes.find((node) => node.id === parentKey);
    if (parentNode) {
      parentNode.data.hasChildren = true;
    }
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
    <div className="size-full bg-[#fafafa]">
      <TaxonomyTreeHoverProvider>
        <ReactFlow
          nodes={nodesAfterLayout}
          edges={edgesAfterLayout}
          nodeTypes={nodeTypes}
          maxZoom={2}
          minZoom={0.3}
          edgesFocusable={false}
          elementsSelectable={false}
          proOptions={{ hideAttribution: true }}
        >
          <Background color="#eee" variant={BackgroundVariant.Dots} size={3} />
          <MiniMap nodeStrokeWidth={3} pannable />
          <Controls showInteractive={false} />
        </ReactFlow>
      </TaxonomyTreeHoverProvider>
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
