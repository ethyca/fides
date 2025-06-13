import { Edge, Node, Position } from "@xyflow/react";
import dagre from "dagre";

// The dagre layout algorithm needs a graph instance with nodes and edges
const dagreGraph = new dagre.graphlib.Graph();
dagreGraph.setDefaultEdgeLabel(() => ({}));

// Function to generate positions from a dagre layout
export const getLayoutedElements = (
  nodes: Node[],
  edges: Edge[],
  direction: "LR" | "TB" = "LR", // Left to Right or Top to Bottom
) => {
  // Clear the layout
  dagreGraph.setGraph({
    rankdir: direction,
    // Bring the graph a bit tighter while still maintaining breathing room
    ranksep: 40, // Vertical spacing between ranks (rows/columns)
    nodesep: 40, // Horizontal spacing between individual nodes
    edgesep: 25, // Minimum distance between edges and other graph elements
    marginx: 15, // Extra margin on the x-axis
    marginy: 15, // Extra margin on the y-axis
  });

  // Set node width and height for layout calculation
  // We intentionally add some padding to the node dimensions so that dagre
  // allocates extra whitespace around each rendered node. This prevents
  // edges (especially those with large arrowheads) from hugging the node
  // border too closely.
  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: 220, height: 70 });
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
      sourcePosition: direction === "LR" ? Position.Right : Position.Bottom,
      targetPosition: direction === "LR" ? Position.Left : Position.Top,
    };
  });

  return { nodes: layoutedNodes, edges };
};
