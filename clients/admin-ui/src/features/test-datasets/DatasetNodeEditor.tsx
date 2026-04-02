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
import { Breadcrumb, Button, Flex, Icons, Select, Typography } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import yaml, { YAMLException } from "js-yaml";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { Editor } from "~/features/common/yaml/helpers";
import { Dataset, DatasetCollection, DatasetField } from "~/types/api";

import AddNodeModal from "./AddNodeModal";
import DatasetEditorActionsContext, {
  DatasetEditorActions,
} from "./context/DatasetEditorActionsContext";
import { DatasetTreeHoverProvider } from "./context/DatasetTreeHoverContext";
import {
  addNestedField,
  getFieldsAtPath,
  removeFieldAtPath,
  updateFieldAtPath,
} from "./dataset-field-helpers";
import DatasetNodeDetailPanel from "./DatasetNodeDetailPanel";
import DatasetTreeEdge from "./edges/DatasetTreeEdge";
import { removeNulls } from "./helpers";
import DatasetCollectionNode from "./nodes/DatasetCollectionNode";
import DatasetFieldNode from "./nodes/DatasetFieldNode";
import DatasetRootNode from "./nodes/DatasetRootNode";
import useDatasetGraph, {
  collectDatasetCategories,
  COLLECTION_ROOT_PREFIX,
  CollectionNodeData,
  DATASET_ROOT_ID,
  FieldNodeData,
  ProtectedFieldsInfo,
} from "./useDatasetGraph";
import useDatasetNodeLayout from "./useDatasetNodeLayout";

const LAYOUT_OPTIONS = { direction: "LR" } as const;

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

  // Keep a ref to the latest dataset so modal callbacks avoid stale closures
  const datasetRef = useRef(dataset);
  datasetRef.current = dataset;

  const [focusedCollection, setFocusedCollection] = useState<string | null>(
    null,
  );
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [addModal, setAddModal] = useState<AddModalState>(CLOSED_MODAL);
  const [highlightedNodeId, setHighlightedNodeId] = useState<string | null>(
    null,
  );
  const highlightTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const [categoryFilter, setCategoryFilter] = useState<string[]>([]);

  // --- YAML editor state ---
  const [yamlPanelOpen, setYamlPanelOpen] = useState(false);
  const [yamlContent, setYamlContent] = useState("");
  const [yamlError, setYamlError] = useState<string | null>(null);
  // Tracks who initiated the last change to prevent sync loops between the
  // YAML panel and the graph. When YAML onChange fires, this is set to "yaml"
  // so the dataset→YAML sync effect skips the redundant re-dump. Under rapid
  // typing, a second debounced onDatasetChange may arrive after the ref is
  // cleared, causing one extra (but idempotent) YAML re-dump — this is cosmetic.
  const changeSourceRef = useRef<"graph" | "yaml" | null>(null);
  const yamlDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Clean up YAML debounce timer on unmount to prevent firing against
  // an unmounted component if the user navigates away while typing.
  useEffect(
    () => () => {
      if (yamlDebounceRef.current) {
        clearTimeout(yamlDebounceRef.current);
      }
    },
    [],
  );

  const highlightNode = useCallback((nodeId: string) => {
    if (highlightTimerRef.current) {
      clearTimeout(highlightTimerRef.current);
    }
    setHighlightedNodeId(nodeId);
    highlightTimerRef.current = setTimeout(() => {
      setHighlightedNodeId(null);
      highlightTimerRef.current = null;
    }, 1500);
  }, []);

  // Sync dataset → YAML when the graph side changes
  useEffect(() => {
    if (!yamlPanelOpen) {
      return;
    }
    if (changeSourceRef.current === "yaml") {
      changeSourceRef.current = null;
      return;
    }
    const cleaned = removeNulls(dataset);
    setYamlContent(yaml.dump(cleaned));
    setYamlError(null);
  }, [dataset, yamlPanelOpen]);

  // Initialize YAML content when panel opens
  const handleToggleYamlPanel = useCallback(() => {
    setYamlPanelOpen((prev) => {
      if (!prev) {
        const cleaned = removeNulls(dataset);
        setYamlContent(yaml.dump(cleaned));
        setYamlError(null);
      }
      return !prev;
    });
  }, [dataset]);

  // Handle YAML editor changes with debounce
  const handleYamlChange = useCallback(
    (value: string | undefined) => {
      const newValue = value || "";
      setYamlContent(newValue);

      if (yamlDebounceRef.current) {
        clearTimeout(yamlDebounceRef.current);
      }

      yamlDebounceRef.current = setTimeout(() => {
        try {
          const parsed = yaml.load(newValue) as Dataset;
          if (
            parsed &&
            typeof parsed === "object" &&
            Array.isArray(parsed.collections)
          ) {
            // Validate that the parsed structure won't crash the graph —
            // e.g. a bare "-" in YAML produces null array entries.
            changeSourceRef.current = "yaml";
            onDatasetChange(parsed);
            setYamlError(null);
          } else {
            setYamlError("Invalid dataset structure");
          }
        } catch (e) {
          if (e instanceof YAMLException) {
            setYamlError(
              `${e.reason}${e.mark ? ` at line ${e.mark.line + 1}` : ""}`,
            );
          } else {
            setYamlError("Invalid YAML");
          }
        }
      }, 500);
    },
    [onDatasetChange],
  );

  const availableCategories = useMemo(
    () => collectDatasetCategories(dataset),
    [dataset],
  );

  const categoryOptions = useMemo(
    () => availableCategories.map((c) => ({ value: c, label: c })),
    [availableCategories],
  );

  const { nodes: rawNodes, edges } = useDatasetGraph(
    dataset,
    protectedFields,
    focusedCollection,
    categoryFilter,
  );
  const { nodes: layoutedNodes, edges: layoutedEdges } = useDatasetNodeLayout({
    nodes: rawNodes,
    edges,
    options: LAYOUT_OPTIONS,
  });

  // Derive selected node data from the current graph instead of stale state
  const selectedNodeData = useMemo(() => {
    if (!selectedNodeId) {
      return null;
    }
    const node = rawNodes.find((n) => n.id === selectedNodeId);
    return (node?.data as CollectionNodeData | FieldNodeData) ?? null;
  }, [rawNodes, selectedNodeId]);

  // Merge selection + highlight state into nodes
  const nodes = useMemo(
    () =>
      layoutedNodes.map((node) => ({
        ...node,
        selected: node.id === selectedNodeId,
        data: {
          ...node.data,
          isHighlighted: node.id === highlightedNodeId,
        },
      })),
    [layoutedNodes, selectedNodeId, highlightedNodeId],
  );

  // Fit view only when the graph structure changes (drill-down or node count),
  // not on metadata edits which don't affect layout.
  const nodeCount = rawNodes.length;
  useEffect(() => {
    if (nodeCount > 0) {
      const timer = setTimeout(() => {
        reactFlowInstance.fitView({ padding: 0.2 });
      }, 150);
      return () => clearTimeout(timer);
    }
    return undefined;
  }, [nodeCount, focusedCollection, reactFlowInstance]);

  // Clear selection when drilling in/out
  useEffect(() => {
    setSelectedNodeId(null);
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
        return;
      }
      setSelectedNodeId(node.id);
    },
    [focusedCollection],
  );

  const handlePaneClick = useCallback(() => {
    setSelectedNodeId(null);
  }, []);

  const handleBack = useCallback(() => {
    setFocusedCollection(null);
  }, []);

  const handleUpdateCollection = useCallback(
    (collectionName: string, updates: Partial<DatasetCollection>) => {
      const { current } = datasetRef;
      const updated: Dataset = {
        ...current,
        collections: current.collections.map((c) =>
          c.name === collectionName ? { ...c, ...updates } : c,
        ),
      };
      onDatasetChange(updated);
    },
    [onDatasetChange],
  );

  const handleUpdateField = useCallback(
    (
      collectionName: string,
      fieldPath: string,
      updates: Partial<DatasetField>,
    ) => {
      const { current } = datasetRef;
      const segments = fieldPath.split(".");
      const updated: Dataset = {
        ...current,
        collections: current.collections.map((c) => {
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
    [onDatasetChange],
  );

  // --- Add / Delete handlers ---

  const handleAddCollection = useCallback(
    (name: string) => {
      const { current } = datasetRef;
      const newCollection: DatasetCollection = {
        name,
        fields: [],
      };
      onDatasetChange({
        ...current,
        collections: [...current.collections, newCollection],
      });
      highlightNode(`${COLLECTION_ROOT_PREFIX}${name}`);
    },
    [onDatasetChange, highlightNode],
  );

  const handleAddField = useCallback(
    (
      collectionName: string,
      name: string,
      parentFieldPath?: string,
      fieldData?: Partial<DatasetField>,
    ) => {
      const { current } = datasetRef;
      const newField: DatasetField = { name, ...fieldData };
      onDatasetChange({
        ...current,
        collections: current.collections.map((c) => {
          if (c.name !== collectionName) {
            return c;
          }
          if (!parentFieldPath) {
            return { ...c, fields: [...c.fields, newField] };
          }
          const segments = parentFieldPath.split(".");
          return {
            ...c,
            fields: addNestedField(c.fields, segments, newField),
          };
        }),
      });
      const fieldPath = parentFieldPath ? `${parentFieldPath}.${name}` : name;
      highlightNode(`field-${collectionName}-${fieldPath}`);
    },
    [onDatasetChange, highlightNode],
  );

  const handleDeleteCollection = useCallback(
    (collectionName: string) => {
      const { current } = datasetRef;
      onDatasetChange({
        ...current,
        collections: current.collections.filter(
          (c) => c.name !== collectionName,
        ),
      });
      if (focusedCollection === collectionName) {
        setFocusedCollection(null);
      }
      setSelectedNodeId(null);
    },
    [onDatasetChange, focusedCollection],
  );

  const handleDeleteField = useCallback(
    (collectionName: string, fieldPath: string) => {
      const { current } = datasetRef;
      const segments = fieldPath.split(".");
      onDatasetChange({
        ...current,
        collections: current.collections.map((c) => {
          if (c.name !== collectionName) {
            return c;
          }
          return { ...c, fields: removeFieldAtPath(c.fields, segments) };
        }),
      });
      setSelectedNodeId(null);
    },
    [onDatasetChange],
  );

  const editorActions: DatasetEditorActions = useMemo(
    () => ({
      addCollection: () => {
        const currentDataset = datasetRef.current;
        setAddModal({
          open: true,
          title: "Add Collection",
          existingNames: currentDataset.collections.map((c) => c.name),
          mode: "collection",
          onConfirm: (name: string) => {
            handleAddCollection(name);
            setAddModal(CLOSED_MODAL);
          },
        });
      },
      addField: (collectionName: string, parentFieldPath?: string) => {
        const currentDataset = datasetRef.current;
        const collection = currentDataset.collections.find(
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
      handleAddCollection,
      handleAddField,
      handleDeleteCollection,
      handleDeleteField,
    ],
  );

  const datasetLabel = dataset.name || dataset.fides_key;

  return (
    <DatasetEditorActionsContext.Provider value={editorActions}>
      <Flex ref={reactFlowRef} className="size-full" vertical>
        {/* Toolbar / Breadcrumb navigation */}
        <Flex
          align="center"
          justify="space-between"
          style={{
            padding: "6px 12px",
            borderBottom: "1px solid var(--fidesui-neutral-200)",
            backgroundColor: "white",
            flexShrink: 0,
          }}
        >
          {focusedCollection ? (
            <Flex align="center" gap="small">
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
          ) : (
            <div />
          )}
          <Flex align="center" gap="small">
            {availableCategories.length > 0 && (
              <Select
                mode="multiple"
                allowClear
                placeholder="Filter by category"
                aria-label="Filter by data category"
                options={categoryOptions}
                value={categoryFilter}
                onChange={(value) => setCategoryFilter(value ?? [])}
                style={{ minWidth: 200, maxWidth: 400 }}
                size="small"
                showSearch
              />
            )}
            <Button
              type="text"
              size="small"
              icon={<Icons.Code />}
              onClick={handleToggleYamlPanel}
              aria-label="Toggle YAML editor"
            >
              YAML
            </Button>
          </Flex>
        </Flex>
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
        {/* Collapsible YAML editor panel */}
        {yamlPanelOpen && (
          <Flex
            vertical
            style={{
              flexShrink: 0,
              height: 300,
              borderTop: "1px solid var(--fidesui-neutral-200)",
              backgroundColor: "white",
            }}
          >
            <Flex
              align="center"
              justify="space-between"
              style={{
                padding: "4px 12px",
                borderBottom: "1px solid var(--fidesui-neutral-200)",
                flexShrink: 0,
              }}
            >
              <Flex align="center" gap="small">
                <Typography.Text
                  strong
                  style={{ fontSize: 12, userSelect: "none" }}
                >
                  YAML Editor
                </Typography.Text>
                {yamlError && (
                  <Typography.Text type="danger" style={{ fontSize: 11 }}>
                    {yamlError}
                  </Typography.Text>
                )}
              </Flex>
              <Button
                type="text"
                size="small"
                icon={<Icons.Close />}
                onClick={() => setYamlPanelOpen(false)}
                aria-label="Close YAML editor"
              />
            </Flex>
            <div style={{ flex: "1 1 auto", minHeight: 0 }}>
              <Editor
                defaultLanguage="yaml"
                value={yamlContent}
                height="100%"
                onChange={handleYamlChange}
                options={{
                  fontFamily: "Menlo",
                  fontSize: 13,
                  minimap: { enabled: false },
                  readOnly: false,
                  hideCursorInOverviewRuler: true,
                  overviewRulerBorder: false,
                  scrollBeyondLastLine: false,
                  lineNumbers: "on",
                }}
                theme="light"
              />
            </div>
          </Flex>
        )}
        <DatasetNodeDetailPanel
          open={!!selectedNodeData}
          onClose={() => {
            setSelectedNodeId(null);
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
      </Flex>
    </DatasetEditorActionsContext.Provider>
  );
};

const DatasetNodeEditor = (props: DatasetNodeEditorProps) => (
  <ReactFlowProvider>
    <DatasetNodeEditorInner {...props} />
  </ReactFlowProvider>
);

export default DatasetNodeEditor;
