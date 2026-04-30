import { Edge, Node } from "@xyflow/react";

import { getLayoutedElements } from "~/features/datamap/layout-utils";

import { NODE_HEIGHT, NODE_WIDTH } from "./constants";

export type LayoutDirection = "LR" | "TB";

export const layoutTraversal = (
  nodes: Node[],
  edges: Edge[],
  direction: LayoutDirection = "LR",
) =>
  getLayoutedElements(nodes, edges, direction, {
    nodeWidth: NODE_WIDTH,
    nodeHeight: NODE_HEIGHT,
  });
