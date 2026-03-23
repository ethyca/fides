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

  // Get position and assign it to the nodes
  const layoutedNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);

    // Position node at the calculated coordinates
    // with the origin in the top left corner
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

  return { nodes: layoutedNodes, edges };
};
