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
    ranksep: 100, // Increase vertical spacing between nodes
    nodesep: 80, // Increase horizontal spacing between nodes
    edgesep: 80, // Edge separation
    marginx: 40, // Margin on x axis
    marginy: 40, // Margin on y axis
  });

  // Set node width and height for layout calculation
  // Make these larger to ensure proper spacing
  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: 180, height: 60 });
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
