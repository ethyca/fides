import React, { useCallback, useRef } from "react";
import {
  Background,
  BackgroundVariant,
  Controls,
  ControlButton,
  MiniMap,
  Node,
  NodeMouseHandler,
  OnEdgesChange,
  OnNodesChange,
  ReactFlow,
  ReactFlowProvider,
  useEdgesState,
  useNodesState,
  useReactFlow,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { Icons } from "fidesui";

import { edgeTypes } from "./edges";
import { nodeTypes } from "./nodes";
import { FlowEdge, FlowNode, FlowNodeType } from "./types";
import styles from "./FlowCanvas.module.scss";

interface FlowCanvasProps {
  initialNodes: FlowNode[];
  initialEdges: FlowEdge[];
  onNodeSelect?: (nodeId: string | null) => void;
  onDrop?: (nodeType: FlowNodeType, position: { x: number; y: number }) => void;
  readOnly?: boolean;
}

const FlowCanvasInner = ({
  initialNodes,
  initialEdges,
  onNodeSelect,
  onDrop,
  readOnly = true,
}: FlowCanvasProps) => {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const { screenToFlowPosition } = useReactFlow();

  // Track user-modified positions to preserve them across updates
  const userPositionsRef = useRef<Map<string, { x: number; y: number }>>(
    new Map()
  );

  // Update nodes when initialNodes change, preserving user-dragged positions
  React.useEffect(() => {
    // Get the set of current node IDs to detect policy changes
    const newNodeIds = new Set(initialNodes.map((n) => n.id));

    // Clean up positions for nodes that no longer exist
    const positionsToDelete: string[] = [];
    userPositionsRef.current.forEach((_, nodeId) => {
      if (!newNodeIds.has(nodeId)) {
        positionsToDelete.push(nodeId);
      }
    });
    positionsToDelete.forEach((nodeId) => {
      userPositionsRef.current.delete(nodeId);
    });

    setNodes(() => {
      // Merge: use user-dragged position if available, otherwise use initial position
      return initialNodes.map((initialNode) => {
        const userPosition = userPositionsRef.current.get(initialNode.id);
        if (userPosition) {
          // Preserve user-dragged position
          return { ...initialNode, position: userPosition };
        }
        // Use automatic layout position (for new nodes or nodes not yet dragged)
        return initialNode;
      });
    });
  }, [initialNodes, setNodes]);

  // Update edges when initialEdges change
  React.useEffect(() => {
    setEdges(initialEdges);
  }, [initialEdges, setEdges]);

  // Track position changes from user dragging
  const handleNodesChangeWithTracking: OnNodesChange<FlowNode> = useCallback(
    (changes) => {
      // Track position changes to preserve user-dragged positions
      changes.forEach((change) => {
        if (change.type === "position" && change.position && change.dragging === false) {
          // User finished dragging - store the final position
          userPositionsRef.current.set(change.id, change.position);
        }
      });

      if (readOnly) {
        // Filter out remove changes in read-only mode
        const filteredChanges = changes.filter(
          (change) => change.type !== "remove"
        );
        onNodesChange(filteredChanges);
      } else {
        onNodesChange(changes);
      }
    },
    [readOnly, onNodesChange]
  );

  // Handle node click
  const handleNodeClick: NodeMouseHandler = useCallback(
    (event, node) => {
      if (onNodeSelect) {
        onNodeSelect(node.id);
      }
    },
    [onNodeSelect]
  );

  // Handle pane click (deselect)
  const handlePaneClick = useCallback(() => {
    if (onNodeSelect) {
      onNodeSelect(null);
    }
  }, [onNodeSelect]);

  // MiniMap node color function
  const nodeColor = (node: Node): string => {
    switch (node.type) {
      case "start":
        return "#10b981"; // green
      case "match":
        return "#3b82f6"; // blue
      case "gate":
        return "#8b5cf6"; // purple
      case "constraint":
        return "#f59e0b"; // amber
      case "action":
        return "#ef4444"; // red
      default:
        return "#6b7280"; // gray
    }
  };

  const handleEdgesChange: OnEdgesChange<FlowEdge> = useCallback(
    (changes) => {
      if (readOnly) {
        // Filter out remove changes in read-only mode
        const filteredChanges = changes.filter(
          (change) => change.type !== "remove"
        );
        onEdgesChange(filteredChanges);
      } else {
        onEdgesChange(changes);
      }
    },
    [readOnly, onEdgesChange]
  );

  // Reset layout to automatic positions (clear all user-dragged positions)
  const handleResetLayout = useCallback(() => {
    userPositionsRef.current.clear();
    setNodes(initialNodes);
  }, [initialNodes, setNodes]);

  // Handle drag over to allow drop
  const handleDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = "copy";
  }, []);

  // Handle drop to create new node
  const handleDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      if (!onDrop || readOnly) {
        return;
      }

      const nodeType = event.dataTransfer.getData("nodeType") as FlowNodeType;
      if (!nodeType) {
        return;
      }

      // Get the position in the flow
      const position = screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      });

      onDrop(nodeType, position);
    },
    [onDrop, readOnly, screenToFlowPosition]
  );

  return (
    <div
      ref={reactFlowWrapper}
      className={styles.container}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
    >
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={handleNodesChangeWithTracking}
        onEdgesChange={handleEdgesChange}
        onNodeClick={handleNodeClick}
        onPaneClick={handlePaneClick}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
        fitViewOptions={{ padding: 0.2, maxZoom: 1 }}
        nodesDraggable={!readOnly}
        nodesConnectable={!readOnly}
        elementsSelectable
        panOnDrag
        zoomOnScroll
        minZoom={0.2}
        maxZoom={2}
        className={styles.reactFlow}
      >
        <Background variant={BackgroundVariant.Dots} gap={16} size={1} />
        <Controls
          className={styles.controls}
          showInteractive={false}
          position="bottom-left"
        >
          <ControlButton onClick={handleResetLayout} title="Reset layout">
            <Icons.Renew />
          </ControlButton>
        </Controls>
        <MiniMap
          className={styles.minimap}
          nodeColor={nodeColor}
          position="bottom-right"
          zoomable
          pannable
        />
      </ReactFlow>
    </div>
  );
};

// Wrap with ReactFlowProvider to enable useReactFlow hook
export const FlowCanvas = (props: FlowCanvasProps) => (
  <ReactFlowProvider>
    <FlowCanvasInner {...props} />
  </ReactFlowProvider>
);
