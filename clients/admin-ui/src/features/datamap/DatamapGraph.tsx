import "@xyflow/react/dist/style.css";

import {
  Background,
  BackgroundVariant,
  Controls,
  MiniMap,
  Node,
  NodeTypes,
  ReactFlow,
  ReactFlowProvider,
  useReactFlow,
} from "@xyflow/react";
import palette from "fidesui/src/palette/palette.module.scss";
import React, { useCallback, useEffect, useMemo, useRef } from "react";

import DatamapSystemNode from "~/features/datamap/DatamapSystemNode";
import { useDatamapGraph } from "~/features/datamap/hooks/useDatamapGraph";
import { SpatialData } from "~/features/datamap/types";

/**
 * DatamapGraph - Interactive system data flow visualization using ReactFlow
 *
 * This component renders an interactive graph of systems and their data flows,
 * replacing the previous Cytoscape implementation with ReactFlow + Dagre for
 * better React integration and performance.
 *
 * Features:
 * - Custom layout with grid for isolated nodes and Dagre for connected components
 * - Smart viewport management for drawer interactions
 * - Node selection and highlighting
 */

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
  const reactFlowRef = useRef<HTMLDivElement>(null);
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
        const reactFlowBounds = reactFlowRef.current?.getBoundingClientRect();
        const drawerElement = document.querySelector(
          '[data-testid="datamap-drawer"]',
        );

        if (!reactFlowBounds) {
          fidesDebugger(
            "DatamapGraph: ReactFlow bounds not available for viewport management",
          );
          return;
        }

        if (!drawerElement) {
          fidesDebugger(
            "DatamapGraph: Drawer element not found for viewport management",
          );
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
  }, [selectedSystemId, nodes, reactFlowInstance, reactFlowRef]);

  // Handle node selection
  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      setSelectedSystemId(node.id);
    },
    [setSelectedSystemId],
  );

  return (
    <div
      ref={reactFlowRef}
      data-testid="reactflow-graph"
      className="absolute size-full"
    >
      <div
        className="size-full"
        style={{ backgroundColor: palette.FIDESUI_BG_CORINTH }}
      >
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
      </div>
    </div>
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
