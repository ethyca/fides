import "@xyflow/react/dist/style.css";

import {
  Background,
  BackgroundVariant,
  Controls,
  Edge,
  EdgeTypes,
  MiniMap,
  Node,
  NodeTypes,
  ReactFlow,
  ReactFlowProvider,
  useReactFlow,
} from "@xyflow/react";
import palette from "fidesui/src/palette/palette.module.scss";
import { useEffect, useMemo } from "react";

import { CoreTaxonomiesEnum, TAXONOMY_ROOT_NODE_ID } from "../constants";
import { TaxonomyTreeHoverProvider } from "../context/TaxonomyTreeHoverContext";
import useD3HierarchyLayout from "../hooks/useD3HierarchyLayout";
import { TaxonomyEntity } from "../types";
import TaxonomyTextInputNode, {
  TextInputNodeType,
} from "./TaxonomyTextInputNode";
import TaxonomyTreeEdge from "./TaxonomyTreeEdge";
import TaxonomyTreeNode, { TaxonomyTreeNodeType } from "./TaxonomyTreeNode";

interface TaxonomyInteractiveTreeProps {
  taxonomyType: CoreTaxonomiesEnum;
  taxonomyItems: TaxonomyEntity[];
  draftNewItem: Partial<TaxonomyEntity> | null;
  lastCreatedItemKey: string | null;
  resetLastCreatedItemKey: () => void;
  onTaxonomyItemClick: (taxonomyItem: TaxonomyEntity) => void;
  onAddButtonClick: (taxonomyItem: TaxonomyEntity | undefined) => void;
  onCancelDraftItem: () => void;
  onSubmitDraftItem: (label: string) => void;
  userCanAddLabels: boolean;
}

const TaxonomyInteractiveTree = ({
  taxonomyType,
  taxonomyItems,
  draftNewItem,
  lastCreatedItemKey,
  resetLastCreatedItemKey,
  onTaxonomyItemClick,
  onAddButtonClick,
  onCancelDraftItem,
  onSubmitDraftItem,
  userCanAddLabels,
}: TaxonomyInteractiveTreeProps) => {
  const { fitView } = useReactFlow();

  // Reset the zoom level and center the view when the taxonomy type changes
  useEffect(() => {
    // A small delay is needed because fitView doesn't work if it's
    // called before the nodes are rendered
    setTimeout(() => fitView(), 150);
  }, [fitView, taxonomyType]);

  // Root node (the taxonomy type)
  const rootNode: Node = useMemo(
    () => ({
      id: TAXONOMY_ROOT_NODE_ID,
      position: { x: 0, y: 0 },
      data: {
        label: taxonomyType,
        taxonomyItem: {
          fides_key: TAXONOMY_ROOT_NODE_ID,
        },
        taxonomyType,
        onTaxonomyItemClick: null,
        onAddButtonClick,
        hasChildren: taxonomyItems.length !== 0,
        userCanAddLabels,
      },
      type: "taxonomyTreeNode",
    }),
    [taxonomyType, taxonomyItems.length, onAddButtonClick, userCanAddLabels],
  );

  const nodes: Node[] = [rootNode];
  const edges: Edge[] = [];

  taxonomyItems.forEach((taxonomyItem) => {
    // Add one node for each label in the taxonomy
    const label =
      taxonomyItem.name || taxonomyItem.fides_key.split(".").pop() || "";

    const node: TaxonomyTreeNodeType = {
      id: taxonomyItem.fides_key,
      position: { x: 0, y: 0 },
      data: {
        label,
        taxonomyType,
        taxonomyItem,
        onTaxonomyItemClick,
        onAddButtonClick,
        hasChildren: false,
        isLastCreatedItem: lastCreatedItemKey === taxonomyItem.fides_key,
        resetLastCreatedItemKey,
        userCanAddLabels,
      },
      type: "taxonomyTreeNode",
    };
    nodes.push(node);

    // Add lines between each label and it's parent.
    // If it doesn't have a parent node, connect it to the root node.
    const parentTaxonomyItem = taxonomyItem.parent_key
      ? nodes.find((n) => n.id === taxonomyItem.parent_key)
      : null;
    const source = parentTaxonomyItem
      ? parentTaxonomyItem.id
      : TAXONOMY_ROOT_NODE_ID;

    const target = taxonomyItem.fides_key;

    const newEdge = {
      id: `${source}-${target}`,
      source,
      target,
      type: "taxonomyTreeEdge",
    };
    edges.push(newEdge);

    // Update hasChildren for parent to true
    if (parentTaxonomyItem) {
      parentTaxonomyItem.data.hasChildren = true;
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
  const { nodes: nodesAfterLayout, edges: edgesAfterLayout } =
    useD3HierarchyLayout({
      nodes,
      edges,
      options: {
        direction: "LR",
      },
    });

  const nodeTypes: NodeTypes = useMemo(
    () => ({
      taxonomyTreeNode: TaxonomyTreeNode,
      textInputNode: TaxonomyTextInputNode,
    }),
    [],
  );

  const edgeTypes: EdgeTypes = useMemo(
    () => ({
      taxonomyTreeEdge: TaxonomyTreeEdge,
    }),
    [],
  );

  return (
    <div
      className="size-full"
      style={{ backgroundColor: palette.FIDESUI_BG_CORINTH }}
      data-testid="taxonomy-interactive-tree"
    >
      <TaxonomyTreeHoverProvider>
        <ReactFlow
          nodes={nodesAfterLayout}
          edges={edgesAfterLayout}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
          maxZoom={2}
          minZoom={0.3}
          nodesConnectable={false}
          edgesFocusable={false}
          elementsSelectable={false}
          proOptions={{ hideAttribution: true }}
        >
          <Background
            color={palette.FIDESUI_NEUTRAL_100}
            variant={BackgroundVariant.Dots}
            size={3}
          />
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
