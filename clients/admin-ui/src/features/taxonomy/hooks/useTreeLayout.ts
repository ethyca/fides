import Dagre from "@dagrejs/dagre";
import { Edge, Node } from "@xyflow/react";
import { useMemo } from "react";

interface UseTreeLayoutProps {
  nodes: Node[];
  edges: Edge[];
  options: {
    direction: "TB" | "BT" | "LR" | "RL";
    stableOrder?: boolean;
  };
}

const useTreeLayout = ({ nodes, edges, options }: UseTreeLayoutProps) => {
  const layouted = useMemo(() => {
    const g = new Dagre.graphlib.Graph().setDefaultEdgeLabel(() => ({}));
    g.setGraph({
      rankdir: options.direction,
      ranksep: 200,
    });

    edges.forEach((edge) => g.setEdge(edge.source, edge.target));
    nodes.forEach((node) =>
      g.setNode(node.id, {
        ...node,
        width: node.measured?.width ?? 220,
        height: node.measured?.height ?? 0,
      }),
    );

    Dagre.layout(g, {
      disableOptimalOrderHeuristic: options.stableOrder,
    });

    return {
      nodes: nodes.map((node) => {
        const position = g.node(node.id);
        // We are shifting the dagre node position (anchor=center center) to the top left
        // so it matches the React Flow node anchor point (top left).
        const x = position.x - (node.measured?.width ?? 0) / 2;
        const y = position.y - (node.measured?.height ?? 0) / 2;

        return { ...node, position: { x, y } };
      }),
      edges,
    };
  }, [nodes, edges, options]);

  return layouted;
};
export default useTreeLayout;
