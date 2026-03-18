import "@xyflow/react/dist/style.css";

import type { OnMount } from "@monaco-editor/react";
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
import { Breadcrumb, Button, Flex, Icons, Typography } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import yaml, { YAMLException } from "js-yaml";
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import { Editor } from "~/features/common/yaml/helpers";
import { Dataset, DatasetCollection, DatasetField } from "~/types/api";

import AddNodeModal from "./AddNodeModal";
import DatasetEditorActionsContext, {
  DatasetEditorActions,
} from "./context/DatasetEditorActionsContext";
import { DatasetTreeHoverProvider } from "./context/DatasetTreeHoverContext";
import DatasetNodeDetailPanel from "./DatasetNodeDetailPanel";
import DatasetTreeEdge from "./edges/DatasetTreeEdge";
import { buildProtectedPathsByCollection, removeNulls } from "./helpers";
import DatasetCollectionNode from "./nodes/DatasetCollectionNode";
import DatasetFieldNode from "./nodes/DatasetFieldNode";
import DatasetRootNode from "./nodes/DatasetRootNode";
import useDatasetGraph, {
  COLLECTION_ROOT_PREFIX,
  CollectionNodeData,
  DATASET_ROOT_ID,
  FieldNodeData,
  ProtectedFieldsInfo,
} from "./useDatasetGraph";
import useDatasetNodeLayout from "./useDatasetNodeLayout";

type MonacoEditor = Parameters<OnMount>[0];
type MonacoDecorationsCollection = ReturnType<
  MonacoEditor["createDecorationsCollection"]
>;
type MonacoDecorationOptions = Parameters<
  MonacoEditor["createDecorationsCollection"]
>[0][number];

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

  // --- YAML editor state ---
  const [yamlPanelOpen, setYamlPanelOpen] = useState(false);
  const [yamlContent, setYamlContent] = useState("");
  const [yamlError, setYamlError] = useState<string | null>(null);
  // Tracks who initiated the last change to prevent sync loops
  const changeSourceRef = useRef<"graph" | "yaml" | null>(null);
  const yamlDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const yamlEditorRef = useRef<MonacoEditor | null>(null);
  const yamlDecorationsRef = useRef<MonacoDecorationsCollection | null>(null);

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

  // Compute protected YAML line ranges for Monaco decorations
  const protectedRanges = useMemo((): MonacoDecorationOptions[] => {
    if (!yamlPanelOpen || !protectedFields || !yamlContent) {
      return [];
    }

    const lines = yamlContent.split("\n");
    const ranges: MonacoDecorationOptions[] = [];

    // Build lookup: collection → Set of field paths (including ancestor paths)
    const protectedPathsByCollection = buildProtectedPathsByCollection(
      protectedFields.protected_collection_fields,
    );

    const immutableSet = new Set(protectedFields.immutable_fields);
    let currentCollection = "";
    const fieldStack: [number, string][] = [];

    lines.forEach((line: string, i: number) => {
      let isProtected = false;

      // Top-level immutable keys (fides_key, name, description, etc.)
      if (/^\S/.test(line) && line.includes(":")) {
        const key = line.split(":")[0].trim();
        if (immutableSet.has(key)) {
          isProtected = true;
        }
      }

      // Track collection/field structure
      const nameMatch = line.match(/^(\s*)-\s+name:\s+(\S+)/);
      if (nameMatch) {
        const [, indent, name] = nameMatch;
        const indentLevel = indent.length;

        if (indentLevel <= 4) {
          currentCollection = name;
          fieldStack.length = 0;
        } else {
          while (
            fieldStack.length > 0 &&
            fieldStack[fieldStack.length - 1][0] >= indentLevel
          ) {
            fieldStack.pop();
          }
          fieldStack.push([indentLevel, name]);

          if (protectedPathsByCollection.has(currentCollection)) {
            const currentPath = fieldStack.map(([, n]) => n).join(".");
            if (
              protectedPathsByCollection
                .get(currentCollection)!
                .has(currentPath)
            ) {
              isProtected = true;
            }
          }
        }
      }

      if (isProtected) {
        ranges.push({
          range: {
            startLineNumber: i + 1,
            startColumn: 1,
            endLineNumber: i + 1,
            endColumn: line.length + 1,
          },
          options: {
            isWholeLine: true,
            inlineClassName: "immutable-line",
          },
        });
      }
    });

    return ranges;
  }, [yamlPanelOpen, protectedFields, yamlContent]);

  // Apply decorations when ranges change or editor is available
  const applyYamlDecorations = useCallback(() => {
    const monacoEditor = yamlEditorRef.current;
    if (!monacoEditor) {
      return;
    }
    if (yamlDecorationsRef.current) {
      yamlDecorationsRef.current.set(protectedRanges);
    } else {
      yamlDecorationsRef.current =
        monacoEditor.createDecorationsCollection(protectedRanges);
    }
  }, [protectedRanges]);

  useEffect(() => {
    applyYamlDecorations();
  }, [applyYamlDecorations]);

  // Inject immutable-line style and clean up on unmount
  useEffect(() => {
    const styleId = "immutable-line-style";
    if (!document.getElementById(styleId)) {
      const style = document.createElement("style");
      style.id = styleId;
      style.textContent = ".immutable-line { opacity: 0.5; }";
      document.head.appendChild(style);
    }
    return () => {
      document.getElementById(styleId)?.remove();
    };
  }, []);

  const { nodes: rawNodes, edges } = useDatasetGraph(
    dataset,
    protectedFields,
    focusedCollection,
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
      highlightNode(`${COLLECTION_ROOT_PREFIX}${name}`);
    },
    [dataset, onDatasetChange, highlightNode],
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
    [dataset, onDatasetChange, highlightNode],
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
    },
    [dataset, onDatasetChange],
  );

  const editorActions: DatasetEditorActions = useMemo(
    () => ({
      addCollection: () => {
        const { current } = datasetRef;
        setAddModal({
          open: true,
          title: "Add Collection",
          existingNames: current.collections.map((c) => c.name),
          mode: "collection",
          onConfirm: (name: string) => {
            handleAddCollection(name);
            setAddModal(CLOSED_MODAL);
          },
        });
      },
      addField: (collectionName: string, parentFieldPath?: string) => {
        const { current } = datasetRef;
        const collection = current.collections.find(
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
      <div
        ref={reactFlowRef}
        className="size-full"
        style={{ display: "flex", flexDirection: "column" }}
      >
        {/* Toolbar / Breadcrumb navigation */}
        <Flex
          align="center"
          justify="space-between"
          style={{
            padding: "6px 12px",
            borderBottom: "1px solid #E2E8F0",
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
          <div
            style={{
              flexShrink: 0,
              height: 300,
              borderTop: "1px solid #E2E8F0",
              display: "flex",
              flexDirection: "column",
              backgroundColor: "white",
            }}
          >
            <Flex
              align="center"
              justify="space-between"
              style={{
                padding: "4px 12px",
                borderBottom: "1px solid #E2E8F0",
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
                onMount={(editor) => {
                  yamlEditorRef.current = editor;
                  applyYamlDecorations();
                }}
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
          </div>
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
