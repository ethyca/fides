import { Edge, Node } from "@xyflow/react";
import { stratify, tree } from "d3-hierarchy";
import { useMemo } from "react";

interface UseDatasetNodeLayoutProps {
  nodes: Node[];
  edges: Edge[];
  options: {
    direction: "TB" | "LR";
  };
}

// Horizontal gap between parent→child ranks; vertical gap between siblings
const NODE_WIDTH = 300;
const NODE_HEIGHT = 44;

const layoutTree = tree<Node>();

const useDatasetNodeLayout = ({
  nodes,
  edges,
  options,
}: UseDatasetNodeLayoutProps) => {
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

    const nodeSizes: [number, number] =
      options.direction === "LR"
        ? [NODE_HEIGHT, NODE_WIDTH]
        : [NODE_WIDTH, NODE_HEIGHT];

    const layout = layoutTree
      .nodeSize(nodeSizes)
      .separation((a, b) => (a.parent === b.parent ? 1 : 1.6))(root);

    return {
      nodes: layout.descendants().map((node) => {
        const position =
          options.direction === "LR"
            ? { x: node.y, y: node.x }
            : { x: node.x, y: node.y };
        return { ...node.data, position };
      }),
      edges,
    };
  }, [nodes, edges, options]);

  return layouted;
};

export default useDatasetNodeLayout;
