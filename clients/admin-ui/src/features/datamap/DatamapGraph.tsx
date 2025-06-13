import "@xyflow/react/dist/style.css";

import {
  Background,
  BackgroundVariant,
  Controls,
  Edge,
  MarkerType,
  MiniMap,
  Node,
  NodeTypes,
  Position,
  ReactFlow,
  ReactFlowProvider,
  useReactFlow,
} from "@xyflow/react";
import { Box } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import React, {
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
} from "react";

import { DatamapGraphContext } from "~/features/datamap/datamap-graph/DatamapGraphContext";
import DatamapSystemNode from "~/features/datamap/DatamapSystemNode";
import { getLayoutedElements } from "~/features/datamap/layout-utils";
import { SpatialData } from "~/features/datamap/types";

type UseDatamapGraphProps = {
  data: SpatialData;
};

const useDatamapGraph = ({ data }: UseDatamapGraphProps) => {
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
    const GRID_COLS = 4; // number of columns in top grid
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
        sourcePosition: Position.Right,
        targetPosition: Position.Left,
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

interface DatamapGraphProps {
  data: SpatialData;
  setSelectedSystemId: (id: string) => void;
  selectedSystemId?: string;
}

const DatamapGraph = ({
  data,
  setSelectedSystemId,
  selectedSystemId,
}: DatamapGraphProps) => {
  const { nodes: baseNodes, edges } = useDatamapGraph({ data });
  const reactFlowInstance = useReactFlow();
  const datamapGraphRef = useContext(DatamapGraphContext);
  const originalViewportRef = useRef<{
    x: number;
    y: number;
    zoom: number;
  } | null>(null);

  // Merge selection state with base nodes based on selectedSystemId from parent
  const nodes = useMemo(
    () =>
      baseNodes.map((node) => ({
        ...node,
        selected: node.id === selectedSystemId,
      })),
    [baseNodes, selectedSystemId],
  );

  // Define the custom node types
  const nodeTypes = useMemo<NodeTypes>(
    () => ({
      systemNode: DatamapSystemNode,
    }),
    [],
  );

  // Store the ReactFlow instance in the context
  useEffect(() => {
    datamapGraphRef.current = reactFlowInstance;

    // Cleanup function
    return () => {
      datamapGraphRef.current = undefined;
    };
  }, [reactFlowInstance, datamapGraphRef]);

  // Center (or re-center) the graph only when the underlying layout
  // changes – not when merely toggling the `selected` flag on nodes.
  // Using `baseNodes` (which is unaffected by selection) prevents an
  // unintentional zoom reset when a user clicks on a node.
  useEffect(() => {
    if (baseNodes.length > 0) {
      // Slight delay so the graph has time to mount before fitting.
      setTimeout(() => {
        reactFlowInstance.fitView({ padding: 0.2 });
      }, 150);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [baseNodes, reactFlowInstance]);

  // Pan view to keep selected node visible when drawer opens/closes
  useEffect(() => {
    if (selectedSystemId && nodes.length > 0) {
      // Wait for the drawer animation to complete (drawer has 500ms animation)
      setTimeout(() => {
        const selectedNode = nodes.find((node) => node.id === selectedSystemId);
        if (!selectedNode) {
          return;
        }

        const viewport = reactFlowInstance.getViewport();
        const reactFlowBounds = document
          .querySelector('[data-testid="reactflow-graph"]')
          ?.getBoundingClientRect();
        const drawerElement = document.querySelector(
          '[data-testid="datamap-drawer"]',
        );

        if (!reactFlowBounds) {
          return;
        }

        if (!drawerElement) {
          return;
        }

        // Store original viewport if not already stored
        if (!originalViewportRef.current) {
          originalViewportRef.current = { ...viewport };
        }

        // Get actual drawer width from the DOM
        const drawerBounds = drawerElement.getBoundingClientRect();
        const drawerWidth = drawerBounds.width;
        const nodeScreenX =
          selectedNode.position.x * viewport.zoom + viewport.x;
        const availableWidth = reactFlowBounds.width - drawerWidth;

        // Check if the selected node is covered by the drawer
        if (nodeScreenX > availableWidth - 100) {
          // 100px buffer
          // Calculate how much to pan left to center the node in the available space
          const targetX = availableWidth / 2;
          const deltaX = targetX - nodeScreenX;

          // Pan the view with smooth animation
          reactFlowInstance.setViewport(
            {
              x: viewport.x + deltaX,
              y: viewport.y,
              zoom: viewport.zoom,
            },
            { duration: 300 },
          ); // 300ms smooth animation
        }
      }, 600); // Wait for drawer animation to complete (500ms) plus small buffer
    } else if (!selectedSystemId && originalViewportRef.current) {
      // Drawer is closed, restore original viewport with custom smooth animation
      setTimeout(() => {
        if (originalViewportRef.current) {
          const startViewport = reactFlowInstance.getViewport();
          const targetViewport = originalViewportRef.current;
          const duration = 800; // 800ms for smooth restoration
          const startTime = performance.now();

          // Ease-out-cubic function for smooth deceleration
          const easeOutCubic = (t: number): number => 1 - (1 - t) ** 3;

          const animate = (currentTime: number) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const easedProgress = easeOutCubic(progress);

            // Interpolate between start and target viewport
            const currentViewport = {
              x:
                startViewport.x +
                (targetViewport.x - startViewport.x) * easedProgress,
              y:
                startViewport.y +
                (targetViewport.y - startViewport.y) * easedProgress,
              zoom:
                startViewport.zoom +
                (targetViewport.zoom - startViewport.zoom) * easedProgress,
            };

            reactFlowInstance.setViewport(currentViewport);

            if (progress < 1) {
              requestAnimationFrame(animate);
            }
          };

          requestAnimationFrame(animate);
          originalViewportRef.current = null;
        }
      }, 100);
    }
  }, [selectedSystemId, nodes, reactFlowInstance]);

  // Handle node selection
  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      setSelectedSystemId(node.id);
    },
    [setSelectedSystemId],
  );

  return (
    <Box boxSize="100%" data-testid="reactflow-graph" position="absolute">
      <Box boxSize="100%" bgColor={palette.FIDESUI_BG_CORINTH}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodeClick={onNodeClick}
          nodeTypes={nodeTypes}
          nodesFocusable={false}
          edgesFocusable={false}
          connectOnClick={false}
          nodesConnectable={false}
          elementsSelectable
          fitView
          minZoom={0.3}
          maxZoom={2}
          proOptions={{ hideAttribution: true }}
        >
          <Background
            color={palette.FIDESUI_NEUTRAL_100}
            variant={BackgroundVariant.Dots}
            size={3}
          />
          <MiniMap nodeStrokeWidth={3} pannable />
          <Controls showInteractive={false} />
        </ReactFlow>
      </Box>
    </Box>
  );
};

const DatamapGraphWithProvider = (props: DatamapGraphProps) => {
  return (
    <ReactFlowProvider>
      <DatamapGraph {...props} />
    </ReactFlowProvider>
  );
};

export default DatamapGraphWithProvider;
