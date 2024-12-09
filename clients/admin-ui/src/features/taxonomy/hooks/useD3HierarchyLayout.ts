import { Edge, Node } from "@xyflow/react";
import { stratify, tree } from "d3-hierarchy";
import { useMemo } from "react";

interface UseTreeLayoutProps {
  nodes: Node[];
  edges: Edge[];
  options: {
    direction: "TB" | "LR";
    stableOrder?: boolean;
  };
}

const NODE_WIDTH = 320;
const NODE_HEIGHT = 35;

const g = tree<Node>();

const useD3HierarchyLayout = ({
  nodes,
  edges,
  options,
}: UseTreeLayoutProps) => {
  const layouted = useMemo(() => {
    if (nodes.length === 0) {
      return { nodes, edges };
    }

    const hierarchy = stratify<Node>()
      .id((node) => node.id)
      .parentId(
        (node) => edges.find((edge) => edge.target === node.id)?.source,
      );

    const root = hierarchy(nodes);

    // For horizontal left-right tree, we swap the width and height
    const nodeSizes: [number, number] =
      options.direction === "LR"
        ? [NODE_HEIGHT, NODE_WIDTH]
        : [NODE_WIDTH, NODE_HEIGHT];

    const layout = g
      .nodeSize(nodeSizes)
      .separation((a, b) => (a.parent === b.parent ? 1 : 1.5))(root);

    return {
      nodes: layout.descendants().map((node) => {
        // For horizontal left-right tree, we swap the x and y positions
        let position;
        if (options.direction === "LR") {
          position = { x: node.y, y: node.x };
        } else {
          position = { x: node.x, y: node.y };
        }
        return { ...node.data, position };
      }),
      edges,
    };
  }, [nodes, edges, options]);

  return layouted;
};
export default useD3HierarchyLayout;
