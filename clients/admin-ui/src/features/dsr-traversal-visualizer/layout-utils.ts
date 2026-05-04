import { Edge, Node } from "@xyflow/react";

import { getLayoutedElements } from "~/features/datamap/layout-utils";

import { NODE_HEIGHT, NODE_WIDTH } from "./constants";

export type LayoutDirection = "LR" | "TB";

// In LR mode, ``ranksep`` controls the horizontal gap between columns of
// integration cards. The shared dagre default is 60 px, which leaves arrows
// landing right against the next card's edge with no room for the
// arrowhead to read. Widening it gives the bezier curve room to settle and
// the arrowhead a visible approach. ``nodesep`` is the vertical gap between
// stacked siblings in the same column -- we keep it generous so cards in a
// tall fan-out don't run together.
const LR_RANKSEP = 140;
const LR_NODESEP = 70;

export const layoutTraversal = (
  nodes: Node[],
  edges: Edge[],
  direction: LayoutDirection = "LR",
) =>
  getLayoutedElements(nodes, edges, direction, {
    nodeWidth: NODE_WIDTH,
    nodeHeight: NODE_HEIGHT,
    ...(direction === "LR" ? { ranksep: LR_RANKSEP, nodesep: LR_NODESEP } : {}),
  });
