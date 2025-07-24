import { Edge, MarkerType, Node } from "@xyflow/react";
import palette from "fidesui/src/palette/palette.module.scss";
import { useMemo } from "react";

import { getLayoutedElements } from "~/features/datamap/layout-utils";
import { SpatialData } from "~/features/datamap/types";

type UseDatamapGraphProps = {
  data: SpatialData;
};

/**
 * Custom hook for transforming datamap data into ReactFlow format
 *
 * This hook handles:
 * - Converting datamap nodes to ReactFlow nodes
 * - Converting datamap links to ReactFlow edges
 * - Custom layout with grid for isolated nodes and Dagre for connected components
 *
 * @param data - The spatial datamap data containing nodes and links
 * @returns Object containing formatted nodes and edges for ReactFlow
 */
export const useDatamapGraph = ({ data }: UseDatamapGraphProps) => {
  // Transform nodes from the datamap format to ReactFlow format
  const initialNodes: Node[] = useMemo(
    () =>
      data.nodes.map((node) => ({
        id: node.id,
        data: {
          label: node.name,
          description: node.description,
        },
        position: { x: 0, y: 0 }, // Initial positions will be set by the layout
        type: "systemNode", // Use our custom node type
      })),
    [data.nodes],
  );

  // Transform links from the datamap format to ReactFlow edges
  const initialEdges: Edge[] = useMemo(
    () =>
      data.links.map((link, index) => ({
        id: `edge-${index}`,
        source: link.source,
        target: link.target,
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: palette.FIDESUI_NEUTRAL_300,
          width: 15,
          height: 15,
        },
        style: {
          stroke: palette.FIDESUI_NEUTRAL_300,
          strokeWidth: 1.5,
          strokeOpacity: 0.8,
        },
        animated: false,
      })),
    [data.links],
  );

  // Custom layout: place unlinked nodes in a grid at the top, with the
  // interconnected portion of the graph (linked nodes + edges) rendered
  // beneath that grid. This keeps visually isolated systems clearly
  // separated while preserving dagre's automatic layout for the connected
  // sub-graph.

  const { nodes, edges } = useMemo(() => {
    // Identify which nodes participate in at least one edge
    const linkedNodeIds = new Set<string>();
    initialEdges.forEach((e) => {
      linkedNodeIds.add(e.source);
      linkedNodeIds.add(e.target);
    });

    const gridNodes: Node[] = [];
    const dagreNodes: Node[] = [];

    initialNodes.forEach((n) => {
      if (linkedNodeIds.has(n.id)) {
        dagreNodes.push(n);
      } else {
        gridNodes.push(n);
      }
    });

    // 1. Lay out the connected graph with Dagre
    const { nodes: dagreLayoutNodes } = getLayoutedElements(
      dagreNodes,
      initialEdges,
      "LR",
    );

    // 2. Lay out the unlinked nodes in a simple grid
    // Choose a column count that approximates a square grid so the layout
    // remains compact horizontally and vertically. For N nodes, use
    // ceil(sqrt(N)) columns (with a minimum of 1).
    const GRID_COLS = Math.max(1, Math.ceil(Math.sqrt(gridNodes.length)));
    const H_SPACING = 240; // horizontal distance between nodes (px)
    const V_SPACING = 120; // vertical distance between nodes (px)

    const gridLayoutNodes = gridNodes.map((node, idx) => {
      const row = Math.floor(idx / GRID_COLS);
      const col = idx % GRID_COLS;

      return {
        ...node,
        position: {
          x: col * H_SPACING,
          y: row * V_SPACING,
        },
        sourcePosition: "right" as const,
        targetPosition: "left" as const,
      } as Node;
    });

    // 3. Offset the dagre layout so it appears beneath the grid
    const gridRows = Math.ceil(gridLayoutNodes.length / GRID_COLS);
    const offsetY = gridRows * V_SPACING + 80; // 80px extra buffer below grid

    const shiftedDagreNodes = dagreLayoutNodes.map((node) => ({
      ...node,
      position: {
        x: node.position.x,
        y: node.position.y + offsetY,
      },
    }));

    return {
      nodes: [...gridLayoutNodes, ...shiftedDagreNodes],
      edges: initialEdges,
    };
  }, [initialNodes, initialEdges]);

  return {
    nodes,
    edges,
  };
};
