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
import { Breadcrumb, Button, Flex, Icons } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { Dataset, DatasetCollection, DatasetField } from "~/types/api";

import AddNodeModal from "./AddNodeModal";
import DatasetEditorActionsContext, {
  DatasetEditorActions,
} from "./context/DatasetEditorActionsContext";
import { DatasetTreeHoverProvider } from "./context/DatasetTreeHoverContext";
import DatasetNodeDetailPanel from "./DatasetNodeDetailPanel";
import DatasetTreeEdge from "./edges/DatasetTreeEdge";
import DatasetCollectionNode from "./nodes/DatasetCollectionNode";
import DatasetFieldNode from "./nodes/DatasetFieldNode";
import DatasetRootNode from "./nodes/DatasetRootNode";
import useDatasetGraph, {
  COLLECTION_ROOT_PREFIX,
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

/** Get the children fields of a field at the given path */
const getFieldsAtPath = (
  fields: DatasetField[],
  segments: string[],
): DatasetField[] => {
  const match = fields.find((f) => f.name === segments[0]);
  if (!match) {
    return [];
  }
  if (segments.length === 1) {
    return match.fields ?? [];
  }
  return getFieldsAtPath(match.fields ?? [], segments.slice(1));
};

/** Append a new child field to the parent at the given path */
const addNestedField = (
  fields: DatasetField[],
  segments: string[],
  newField: DatasetField,
): DatasetField[] =>
  fields.map((f) => {
    if (f.name !== segments[0]) {
      return f;
    }
    if (segments.length === 1) {
      return { ...f, fields: [...(f.fields ?? []), newField] };
    }
    return {
      ...f,
      fields: addNestedField(f.fields ?? [], segments.slice(1), newField),
    };
  });

/** Recursively remove a field at the given path */
const removeFieldAtPath = (
  fields: DatasetField[],
  segments: string[],
): DatasetField[] => {
  if (segments.length === 1) {
    return fields.filter((f) => f.name !== segments[0]);
  }
  return fields.map((f) => {
    if (f.name !== segments[0]) {
      return f;
    }
    return {
      ...f,
      fields: removeFieldAtPath(f.fields ?? [], segments.slice(1)),
    };
  });
};

interface AddModalState {
  open: boolean;
  title: string;
  existingNames: string[];
  mode: "collection" | "field";
  onConfirm: (name: string, fieldData?: Partial<DatasetField>) => void;
}

const CLOSED_MODAL: AddModalState = {
  open: false,
  title: "",
  existingNames: [],
  mode: "collection",
  onConfirm: () => {},
};

const DatasetNodeEditorInner = ({
  dataset,
  protectedFields,
  onDatasetChange,
}: DatasetNodeEditorProps) => {
  const reactFlowInstance = useReactFlow();
  const reactFlowRef = useRef<HTMLDivElement>(null);

  const [focusedCollection, setFocusedCollection] = useState<string | null>(
    null,
  );
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [selectedNodeData, setSelectedNodeData] = useState<
    CollectionNodeData | FieldNodeData | null
  >(null);
  const [addModal, setAddModal] = useState<AddModalState>(CLOSED_MODAL);

  const { nodes: rawNodes, edges } = useDatasetGraph(
    dataset,
    protectedFields,
    focusedCollection,
  );
  const { nodes: layoutedNodes, edges: layoutedEdges } = useDatasetNodeLayout({
    nodes: rawNodes,
    edges,
    options: { direction: "LR" },
  });

  // Merge selection state into nodes
  const nodes = useMemo(
    () =>
      layoutedNodes.map((node) => ({
        ...node,
        selected: node.id === selectedNodeId,
      })),
    [layoutedNodes, selectedNodeId],
  );

  // Fit view when layout changes
  useEffect(() => {
    if (rawNodes.length > 0) {
      setTimeout(() => {
        reactFlowInstance.fitView({ padding: 0.2 });
      }, 150);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rawNodes, reactFlowInstance]);

  // Clear selection when drilling in/out
  useEffect(() => {
    setSelectedNodeId(null);
    setSelectedNodeData(null);
  }, [focusedCollection]);

  const handleNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      if (node.id === DATASET_ROOT_ID) {
        return;
      }
      // If clicking a collection in overview mode, drill in
      if (!focusedCollection && node.id.startsWith(COLLECTION_ROOT_PREFIX)) {
        const collectionName = node.id.slice(COLLECTION_ROOT_PREFIX.length);
        setFocusedCollection(collectionName);
        return;
      }
      // If clicking the collection root in drill-down mode, open its detail panel
      if (
        focusedCollection &&
        node.id === `${COLLECTION_ROOT_PREFIX}${focusedCollection}`
      ) {
        setSelectedNodeId(node.id);
        setSelectedNodeData(node.data as CollectionNodeData);
        return;
      }
      setSelectedNodeId(node.id);
      setSelectedNodeData(node.data as CollectionNodeData | FieldNodeData);
    },
    [focusedCollection],
  );

  const handlePaneClick = useCallback(() => {
    setSelectedNodeId(null);
    setSelectedNodeData(null);
  }, []);

  const handleBack = useCallback(() => {
    setFocusedCollection(null);
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

  // --- Add / Delete handlers ---

  const handleAddCollection = useCallback(
    (name: string) => {
      const newCollection: DatasetCollection = {
        name,
        fields: [],
      };
      onDatasetChange({
        ...dataset,
        collections: [...dataset.collections, newCollection],
      });
    },
    [dataset, onDatasetChange],
  );

  const handleAddField = useCallback(
    (
      collectionName: string,
      name: string,
      parentFieldPath?: string,
      fieldData?: Partial<DatasetField>,
    ) => {
      const newField: DatasetField = { name, ...fieldData };
      onDatasetChange({
        ...dataset,
        collections: dataset.collections.map((c) => {
          if (c.name !== collectionName) {
            return c;
          }
          if (!parentFieldPath) {
            // Top-level field on the collection
            return { ...c, fields: [...c.fields, newField] };
          }
          // Nested field: append to the parent's fields array
          const segments = parentFieldPath.split(".");
          return {
            ...c,
            fields: addNestedField(c.fields, segments, newField),
          };
        }),
      });
    },
    [dataset, onDatasetChange],
  );

  const handleDeleteCollection = useCallback(
    (collectionName: string) => {
      onDatasetChange({
        ...dataset,
        collections: dataset.collections.filter(
          (c) => c.name !== collectionName,
        ),
      });
      if (focusedCollection === collectionName) {
        setFocusedCollection(null);
      }
      setSelectedNodeId(null);
      setSelectedNodeData(null);
    },
    [dataset, onDatasetChange, focusedCollection],
  );

  const handleDeleteField = useCallback(
    (collectionName: string, fieldPath: string) => {
      const segments = fieldPath.split(".");
      onDatasetChange({
        ...dataset,
        collections: dataset.collections.map((c) => {
          if (c.name !== collectionName) {
            return c;
          }
          return { ...c, fields: removeFieldAtPath(c.fields, segments) };
        }),
      });
      setSelectedNodeId(null);
      setSelectedNodeData(null);
    },
    [dataset, onDatasetChange],
  );

  const editorActions: DatasetEditorActions = useMemo(
    () => ({
      addCollection: () => {
        setAddModal({
          open: true,
          title: "Add Collection",
          existingNames: dataset.collections.map((c) => c.name),
          mode: "collection",
          onConfirm: (name: string) => {
            handleAddCollection(name);
            setAddModal(CLOSED_MODAL);
          },
        });
      },
      addField: (collectionName: string, parentFieldPath?: string) => {
        const collection = dataset.collections.find(
          (c) => c.name === collectionName,
        );
        const siblingFields = parentFieldPath
          ? getFieldsAtPath(
              collection?.fields ?? [],
              parentFieldPath.split("."),
            )
          : (collection?.fields ?? []);
        const label = parentFieldPath
          ? `Add nested field to "${parentFieldPath}"`
          : `Add field to "${collectionName}"`;
        setAddModal({
          open: true,
          title: label,
          existingNames: siblingFields.map((f) => f.name),
          mode: "field",
          onConfirm: (name: string, fieldData?: Partial<DatasetField>) => {
            handleAddField(collectionName, name, parentFieldPath, fieldData);
            setAddModal(CLOSED_MODAL);
          },
        });
      },
      deleteCollection: handleDeleteCollection,
      deleteField: handleDeleteField,
    }),
    [
      dataset,
      handleAddCollection,
      handleAddField,
      handleDeleteCollection,
      handleDeleteField,
    ],
  );

  const datasetLabel = dataset.name || dataset.fides_key;

  return (
    <DatasetEditorActionsContext.Provider value={editorActions}>
      <div
        ref={reactFlowRef}
        className="size-full"
        style={{ display: "flex", flexDirection: "column" }}
      >
        {/* Breadcrumb navigation */}
        {focusedCollection && (
          <Flex
            align="center"
            gap="small"
            style={{
              padding: "6px 12px",
              borderBottom: "1px solid #E2E8F0",
              backgroundColor: "white",
              flexShrink: 0,
            }}
          >
            <Button
              type="text"
              size="small"
              icon={<Icons.ChevronLeft />}
              onClick={handleBack}
              aria-label="Back to collections"
            />
            <Breadcrumb
              items={[
                {
                  title: (
                    <Button
                      type="link"
                      size="small"
                      onClick={handleBack}
                      style={{ padding: 0, height: "auto" }}
                    >
                      {datasetLabel}
                    </Button>
                  ),
                },
                { title: focusedCollection },
              ]}
            />
          </Flex>
        )}
        <div
          style={{
            flex: "1 1 auto",
            minHeight: 0,
            backgroundColor: palette.FIDESUI_BG_CORINTH,
          }}
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
        <AddNodeModal
          open={addModal.open}
          title={addModal.title}
          existingNames={addModal.existingNames}
          mode={addModal.mode}
          onConfirm={addModal.onConfirm}
          onCancel={() => setAddModal(CLOSED_MODAL)}
        />
      </div>
    </DatasetEditorActionsContext.Provider>
  );
};

const DatasetNodeEditor = (props: DatasetNodeEditorProps) => (
  <ReactFlowProvider>
    <DatasetNodeEditorInner {...props} />
  </ReactFlowProvider>
);

export default DatasetNodeEditor;
