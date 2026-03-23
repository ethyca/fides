import { Edge, Node, Position } from "@xyflow/react";
import dagre from "dagre";

type AlignOption = "UL" | "UR" | "DL" | "DR" | undefined;

export interface DagreLayoutOptions {
  rankdir?: "LR" | "TB";
  ranksep?: number;
  nodesep?: number;
  edgesep?: number;
  marginx?: number;
  marginy?: number;
  nodeWidth?: number;
  nodeHeight?: number;
  /** Per-node dimension overrides keyed by node id. */
  nodeSizes?: Record<string, { width: number; height: number }>;
  /** Node alignment within ranks. Default: dagre default (center). */
  align?: AlignOption;
  /** Align the top of every rank to the same y origin. Default: false. */
  topAlign?: boolean;
}

const DEFAULT_OPTIONS = {
  rankdir: "LR" as const,
  ranksep: 60,
  nodesep: 60,
  edgesep: 50,
  marginx: 15,
  marginy: 15,
  nodeWidth: 220,
  nodeHeight: 70,
  nodeSizes: {} as Record<string, { width: number; height: number }>,
  align: undefined as AlignOption,
  topAlign: false,
};

/**
 * Shift nodes so that every rank (column in LR layout) starts at the same
 * top y coordinate. Dagre centers ranks independently, which causes misalignment
 * when nodes in different ranks have different heights. This corrects for that
 * by finding the minimum y in each rank and aligning them all to the global minimum.
 */
const alignRankTops = <T extends { position: { x: number; y: number } }>(
  nodes: T[],
): T[] => {
  if (nodes.length === 0) {
    return nodes;
  }

  // Find the topmost y in each rank (grouped by x position)
  const rankMinY = new Map<number, number>();
  nodes.forEach((n) => {
    const rx = Math.round(n.position.x);
    const prev = rankMinY.get(rx);
    if (prev === undefined || n.position.y < prev) {
      rankMinY.set(rx, n.position.y);
    }
  });
  const globalMinY = Math.min(...rankMinY.values());

  return nodes.map((n) => {
    const shift = rankMinY.get(Math.round(n.position.x))! - globalMinY;
    return {
      ...n,
      position: { ...n.position, y: n.position.y - shift },
    };
  });
};

// The dagre layout algorithm needs a graph instance with nodes and edges
const dagreGraph = new dagre.graphlib.Graph();
dagreGraph.setDefaultEdgeLabel(() => ({}));

// Function to generate positions from a dagre layout
export const getLayoutedElements = (
  nodes: Node[],
  edges: Edge[],
  direction: "LR" | "TB" = "LR",
  options?: Partial<DagreLayoutOptions>,
) => {
  const opts = { ...DEFAULT_OPTIONS, ...options, rankdir: direction };

  // Clear the layout
  dagreGraph.setGraph({
    rankdir: opts.rankdir,
    ranksep: opts.ranksep,
    nodesep: opts.nodesep,
    edgesep: opts.edgesep,
    marginx: opts.marginx,
    marginy: opts.marginy,
    align: opts.align,
  });

  // Set node width and height for layout calculation
  nodes.forEach((node) => {
    const size = opts.nodeSizes?.[node.id];
    dagreGraph.setNode(node.id, {
      width: size?.width ?? opts.nodeWidth,
      height: size?.height ?? opts.nodeHeight,
    });
  });

  // Add edges
  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  // Calculate positions
  dagre.layout(dagreGraph);

  // Get position and assign it to the nodes (top-left origin)
  let layoutedNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);

    return {
      ...node,
      position: {
        x: nodeWithPosition.x - nodeWithPosition.width / 2,
        y: nodeWithPosition.y - nodeWithPosition.height / 2,
      },
      // Set node source/target handles based on flow direction
      sourcePosition: opts.rankdir === "LR" ? Position.Right : Position.Bottom,
      targetPosition: opts.rankdir === "LR" ? Position.Left : Position.Top,
    };
  });

  if (opts.topAlign) {
    layoutedNodes = alignRankTops(layoutedNodes);
  }

  return { nodes: layoutedNodes, edges };
};
