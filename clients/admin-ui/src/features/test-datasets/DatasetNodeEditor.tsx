import "@xyflow/react/dist/style.css";

import {
  Background,
  BackgroundVariant,
  Controls,
  EdgeTypes,
  MiniMap,
  Node,
  NodeTypes,
  ReactFlow,
  ReactFlowProvider,
  useReactFlow,
} from "@xyflow/react";
import palette from "fidesui/src/palette/palette.module.scss";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { Dataset, DatasetCollection, DatasetField } from "~/types/api";

import { DatasetTreeHoverProvider } from "./context/DatasetTreeHoverContext";
import DatasetNodeDetailPanel from "./DatasetNodeDetailPanel";
import DatasetTreeEdge from "./edges/DatasetTreeEdge";
import DatasetCollectionNode from "./nodes/DatasetCollectionNode";
import DatasetFieldNode from "./nodes/DatasetFieldNode";
import DatasetRootNode from "./nodes/DatasetRootNode";
import useDatasetGraph, {
  CollectionNodeData,
  DATASET_ROOT_ID,
  FieldNodeData,
} from "./useDatasetGraph";
import useDatasetNodeLayout from "./useDatasetNodeLayout";

interface ProtectedFieldsInfo {
  immutable_fields: string[];
  protected_collection_fields: Array<{
    collection: string;
    field: string;
  }>;
}

interface DatasetNodeEditorProps {
  dataset: Dataset;
  protectedFields?: ProtectedFieldsInfo;
  onDatasetChange: (dataset: Dataset) => void;
}

const nodeTypes: NodeTypes = {
  datasetRootNode: DatasetRootNode,
  datasetCollectionNode: DatasetCollectionNode,
  datasetFieldNode: DatasetFieldNode,
};

const edgeTypes: EdgeTypes = {
  datasetTreeEdge: DatasetTreeEdge,
};

/** Walk nested fields to find and update the one at fieldPath */
const updateFieldAtPath = (
  fields: DatasetField[],
  segments: string[],
  updates: Partial<DatasetField>,
): DatasetField[] =>
  fields.map((f) => {
    if (f.name !== segments[0]) {
      return f;
    }
    if (segments.length === 1) {
      return { ...f, ...updates };
    }
    return {
      ...f,
      fields: updateFieldAtPath(f.fields ?? [], segments.slice(1), updates),
    };
  });

/** Ease-out-cubic for smooth deceleration */
const easeOutCubic = (t: number): number => 1 - (1 - t) ** 3;

const DatasetNodeEditorInner = ({
  dataset,
  protectedFields,
  onDatasetChange,
}: DatasetNodeEditorProps) => {
  const reactFlowInstance = useReactFlow();
  const reactFlowRef = useRef<HTMLDivElement>(null);
  const originalViewportRef = useRef<{
    x: number;
    y: number;
    zoom: number;
  } | null>(null);

  const { nodes: rawNodes, edges } = useDatasetGraph(dataset, protectedFields);
  const { nodes: layoutedNodes, edges: layoutedEdges } = useDatasetNodeLayout({
    nodes: rawNodes,
    edges,
    options: { direction: "LR" },
  });

  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [selectedNodeData, setSelectedNodeData] = useState<
    CollectionNodeData | FieldNodeData | null
  >(null);

  // Merge selection state into nodes
  const nodes = useMemo(
    () =>
      layoutedNodes.map((node) => ({
        ...node,
        selected: node.id === selectedNodeId,
      })),
    [layoutedNodes, selectedNodeId],
  );

  // Fit view when layout changes (not on selection)
  useEffect(() => {
    if (rawNodes.length > 0) {
      setTimeout(() => {
        reactFlowInstance.fitView({ padding: 0.2 });
      }, 150);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rawNodes, reactFlowInstance]);

  // Drawer-aware viewport panning
  useEffect(() => {
    if (selectedNodeId && nodes.length > 0) {
      setTimeout(() => {
        const selectedNode = nodes.find((n) => n.id === selectedNodeId);
        if (!selectedNode) {
          return;
        }

        const viewport = reactFlowInstance.getViewport();
        const bounds = reactFlowRef.current?.getBoundingClientRect();
        if (!bounds) {
          return;
        }

        if (!originalViewportRef.current) {
          originalViewportRef.current = { ...viewport };
        }

        const drawerWidth = 400;
        const nodeScreenX =
          selectedNode.position.x * viewport.zoom + viewport.x;
        const availableWidth = bounds.width - drawerWidth;

        if (nodeScreenX > availableWidth - 100) {
          const targetX = availableWidth / 2;
          const deltaX = targetX - nodeScreenX;
          reactFlowInstance.setViewport(
            {
              x: viewport.x + deltaX,
              y: viewport.y,
              zoom: viewport.zoom,
            },
            { duration: 300 },
          );
        }
      }, 600);
    } else if (!selectedNodeId && originalViewportRef.current) {
      setTimeout(() => {
        if (!originalViewportRef.current) {
          return;
        }

        const startViewport = reactFlowInstance.getViewport();
        const targetViewport = originalViewportRef.current;
        const duration = 800;
        const startTime = performance.now();

        const animate = (currentTime: number) => {
          const elapsed = currentTime - startTime;
          const progress = Math.min(elapsed / duration, 1);
          const easedProgress = easeOutCubic(progress);

          reactFlowInstance.setViewport({
            x:
              startViewport.x +
              (targetViewport.x - startViewport.x) * easedProgress,
            y:
              startViewport.y +
              (targetViewport.y - startViewport.y) * easedProgress,
            zoom:
              startViewport.zoom +
              (targetViewport.zoom - startViewport.zoom) * easedProgress,
          });

          if (progress < 1) {
            requestAnimationFrame(animate);
          }
        };

        requestAnimationFrame(animate);
        originalViewportRef.current = null;
      }, 100);
    }
  }, [selectedNodeId, nodes, reactFlowInstance]);

  const handleNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
    if (node.id === DATASET_ROOT_ID) {
      return;
    }
    setSelectedNodeId(node.id);
    setSelectedNodeData(node.data as CollectionNodeData | FieldNodeData);
  }, []);

  const handlePaneClick = useCallback(() => {
    setSelectedNodeId(null);
    setSelectedNodeData(null);
  }, []);

  const handleUpdateCollection = useCallback(
    (collectionName: string, updates: Partial<DatasetCollection>) => {
      const updated: Dataset = {
        ...dataset,
        collections: dataset.collections.map((c) =>
          c.name === collectionName ? { ...c, ...updates } : c,
        ),
      };
      onDatasetChange(updated);
    },
    [dataset, onDatasetChange],
  );

  const handleUpdateField = useCallback(
    (
      collectionName: string,
      fieldPath: string,
      updates: Partial<DatasetField>,
    ) => {
      const segments = fieldPath.split(".");
      const updated: Dataset = {
        ...dataset,
        collections: dataset.collections.map((c) => {
          if (c.name !== collectionName) {
            return c;
          }
          return {
            ...c,
            fields: updateFieldAtPath(c.fields, segments, updates),
          };
        }),
      };
      onDatasetChange(updated);
    },
    [dataset, onDatasetChange],
  );

  return (
    <div ref={reactFlowRef} className="size-full">
      <div
        className="size-full"
        style={{ backgroundColor: palette.FIDESUI_BG_CORINTH }}
      >
        <DatasetTreeHoverProvider edges={layoutedEdges}>
          <ReactFlow
            nodes={nodes}
            edges={layoutedEdges}
            onNodeClick={handleNodeClick}
            onPaneClick={handlePaneClick}
            nodeTypes={nodeTypes}
            edgeTypes={edgeTypes}
            nodesFocusable={false}
            edgesFocusable={false}
            connectOnClick={false}
            nodesConnectable={false}
            elementsSelectable
            fitView
            minZoom={0.2}
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
        </DatasetTreeHoverProvider>
      </div>
      <DatasetNodeDetailPanel
        open={!!selectedNodeData}
        onClose={() => {
          setSelectedNodeId(null);
          setSelectedNodeData(null);
        }}
        nodeData={selectedNodeData}
        onUpdateCollection={handleUpdateCollection}
        onUpdateField={handleUpdateField}
      />
    </div>
  );
};

const DatasetNodeEditor = (props: DatasetNodeEditorProps) => (
  <ReactFlowProvider>
    <DatasetNodeEditorInner {...props} />
  </ReactFlowProvider>
);

export default DatasetNodeEditor;
