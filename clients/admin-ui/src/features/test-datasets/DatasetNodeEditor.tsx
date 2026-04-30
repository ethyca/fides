import "@xyflow/react/dist/style.css";
import "~/features/test-datasets/DatasetNodeEditor.scss";

import type { OnMount } from "@monaco-editor/react";
import {
  Background,
  BackgroundVariant,
  Controls,
  Edge,
  EdgeTypes,
  Node,
  NodeTypes,
  ReactFlow,
  ReactFlowProvider,
  useReactFlow,
} from "@xyflow/react";
import {
  Breadcrumb,
  Button,
  Divider,
  Flex,
  Icons,
  Select,
  Splitter,
  Switch,
  Typography,
} from "fidesui";
import yaml, { YAMLException } from "js-yaml";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { useLocalStorage } from "~/features/common/hooks/useLocalStorage";
import { Editor } from "~/features/common/yaml/helpers";
import { Dataset, DatasetCollection, DatasetField } from "~/types/api";

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
import DatasetNodeDetailPanel, {
  DatasetNodeDetailPanelHandle,
} from "./DatasetNodeDetailPanel";
import DatasetTreeEdge from "./edges/DatasetTreeEdge";
import { buildProtectedPathsByCollection, removeNulls } from "./helpers";
import DatasetCollectionNode from "./nodes/DatasetCollectionNode";
import DatasetFieldNode from "./nodes/DatasetFieldNode";
import DatasetRootNode from "./nodes/DatasetRootNode";
import DatasetTextInputNode, {
  DatasetTextInputNodeType,
} from "./nodes/DatasetTextInputNode";
import useDatasetGraph, {
  collectDatasetCategories,
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
type MonacoDecorationOptions = {
  range: {
    startLineNumber: number;
    startColumn: number;
    endLineNumber: number;
    endColumn: number;
  };
  options: { isWholeLine?: boolean; inlineClassName?: string };
};

const DRAFT_NODE_ID = "draft-node";

const LAYOUT_OPTIONS = { direction: "LR" } as const;

interface DatasetNodeEditorProps {
  dataset: Dataset;
  protectedFields?: ProtectedFieldsInfo;
  onDatasetChange: (dataset: Dataset) => void;
  allowAddCollection?: boolean;
  allowNameEditing?: boolean;
  isSaas?: boolean;
}

const nodeTypes: NodeTypes = {
  datasetRootNode: DatasetRootNode,
  datasetCollectionNode: DatasetCollectionNode,
  datasetFieldNode: DatasetFieldNode,
  datasetTextInputNode: DatasetTextInputNode,
};

const edgeTypes: EdgeTypes = {
  datasetTreeEdge: DatasetTreeEdge,
};

interface DraftNodeState {
  parentId: string;
  mode: "collection" | "field";
  existingNames: string[];
  /** Only set when mode is "field" — the collection the field is being added to. */
  collectionName?: string;
  /** Only set when adding a nested field — dot path of the parent field. */
  parentFieldPath?: string;
}

const DatasetNodeEditorInner = ({
  dataset,
  protectedFields,
  onDatasetChange,
  allowAddCollection = false,
  allowNameEditing = false,
  isSaas = false,
}: DatasetNodeEditorProps) => {
  const reactFlowInstance = useReactFlow();
  const reactFlowRef = useRef<HTMLDivElement>(null);
  const detailPanelRef = useRef<DatasetNodeDetailPanelHandle>(null);

  // Keep a ref to the latest dataset so modal callbacks avoid stale closures
  const datasetRef = useRef(dataset);
  datasetRef.current = dataset;

  const [focusedCollection, setFocusedCollection] = useState<string | null>(
    null,
  );
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [draftNode, setDraftNode] = useState<DraftNodeState | null>(null);
  const [highlightedNodeId, setHighlightedNodeId] = useState<string | null>(
    null,
  );
  const highlightTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const [categoryFilter, setCategoryFilter] = useState<string[]>([]);

  // --- YAML editor state ---
  const YAML_PANEL_DEFAULT_WIDTH = 550;
  const [yamlPanelOpen, setYamlPanelOpen] = useLocalStorage<boolean>(
    "datasetEditor.yamlPanelOpen",
    false,
  );
  const [yamlPanelSize, setYamlPanelSize] = useState(
    yamlPanelOpen ? YAML_PANEL_DEFAULT_WIDTH : 0,
  );
  const [yamlContent, setYamlContent] = useState("");
  const [yamlError, setYamlError] = useState<string | null>(null);
  // Tracks who initiated the last change to prevent sync loops between the
  // YAML panel and the graph. When YAML onChange fires, this is set to "yaml"
  // so the dataset→YAML sync effect skips the redundant re-dump. Under rapid
  // typing, a second debounced onDatasetChange may arrive after the ref is
  // cleared, causing one extra (but idempotent) YAML re-dump — this is cosmetic.
  const changeSourceRef = useRef<"graph" | "yaml" | null>(null);
  const yamlDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const yamlEditorRef = useRef<MonacoEditor | null>(null);
  const yamlDecorationsRef = useRef<MonacoDecorationsCollection | null>(null);

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
    if (yamlPanelOpen) {
      setYamlPanelOpen(false);
      setYamlPanelSize(0);
    } else {
      const cleaned = removeNulls(dataset);
      setYamlContent(yaml.dump(cleaned));
      setYamlError(null);
      setYamlPanelSize(YAML_PANEL_DEFAULT_WIDTH);
      setYamlPanelOpen(true);
    }
  }, [dataset, yamlPanelOpen, setYamlPanelOpen]);

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
            // If the focused collection no longer exists in the parsed
            // dataset (renamed or deleted via YAML), reset to overview.
            if (
              focusedCollection &&
              !parsed.collections.some((c) => c.name === focusedCollection)
            ) {
              setFocusedCollection(null);
            }
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
    [onDatasetChange, focusedCollection],
  );

  // Compute protected YAML line ranges for Monaco decorations
  const protectedRanges = useMemo((): MonacoDecorationOptions[] => {
    if (!yamlPanelOpen || !yamlContent) {
      return [];
    }

    const lines = yamlContent.split("\n");
    const ranges: MonacoDecorationOptions[] = [];

    // Build lookup: collection → Set of field paths (including ancestor paths)
    const protectedPathsByCollection = protectedFields
      ? buildProtectedPathsByCollection(
          protectedFields.protected_collection_fields,
        )
      : new Map<string, Set<string>>();

    let currentCollection = "";
    const fieldStack: [number, string][] = [];

    // Detect the collection indent level from the first `- name:` line
    // instead of hardcoding a threshold.
    const firstNameLine = lines.find((l) => /^(\s*)-\s+name:\s+\S+/.test(l));
    const collectionIndent = firstNameLine
      ? (firstNameLine.match(/^(\s*)-/)?.[1].length ?? null)
      : null;

    lines.forEach((line: string, i: number) => {
      let isProtected = false;

      // Top-level keys outside "collections" are immutable
      if (/^\S/.test(line) && line.includes(":")) {
        const key = line.split(":")[0].trim();
        if (key !== "collections") {
          isProtected = true;
        }
      }

      // Track collection/field structure
      const nameMatch = line.match(/^(\s*)-\s+name:\s+(\S+)/);
      if (nameMatch) {
        const [, indent, name] = nameMatch;
        const indentLevel = indent.length;

        if (collectionIndent !== null && indentLevel <= collectionIndent) {
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

  const selectedNodeData = useMemo(() => {
    if (!selectedNodeId) {
      return null;
    }
    const node = rawNodes.find((n) => n.id === selectedNodeId);
    return (node?.data as CollectionNodeData | FieldNodeData) ?? null;
  }, [rawNodes, selectedNodeId]);

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

  // Clear selection and any pending draft when drilling in/out
  useEffect(() => {
    setSelectedNodeId(null);
    setDraftNode(null);
  }, [focusedCollection]);

  const handleNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      // The draft input node handles its own focus/submit/cancel — ignore
      // ReactFlow's click events for it so we don't blur the input.
      if (node.id === DRAFT_NODE_ID || node.id === DATASET_ROOT_ID) {
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
    detailPanelRef.current?.flush();
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
      if (
        updates.name &&
        updates.name !== collectionName &&
        focusedCollection === collectionName
      ) {
        setFocusedCollection(updates.name);
      }
      onDatasetChange(updated);
    },
    [onDatasetChange, focusedCollection],
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
            fields: updateFieldAtPath(c.fields ?? [], segments, updates),
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
    (collectionName: string, name: string, parentFieldPath?: string) => {
      const { current } = datasetRef;
      const newField: DatasetField = { name };
      onDatasetChange({
        ...current,
        collections: current.collections.map((c) => {
          if (c.name !== collectionName) {
            return c;
          }
          if (!parentFieldPath) {
            return { ...c, fields: [...(c.fields ?? []), newField] };
          }
          const segments = parentFieldPath.split(".");
          return {
            ...c,
            fields: addNestedField(c.fields ?? [], segments, newField),
          };
        }),
      });
      const fieldPath = parentFieldPath ? `${parentFieldPath}.${name}` : name;
      highlightNode(`field-${collectionName}-${fieldPath}`);
    },
    [onDatasetChange, highlightNode],
  );

  // Inject the inline text-input node + animated edge when a draft is active.
  // The submit/cancel callbacks are baked into node data (React Flow custom
  // nodes only receive `data`), so this memo rebuilds whenever the draft
  // descriptor or the add handlers change.
  const { nodesWithDraft, edgesWithDraft } = useMemo(() => {
    if (!draftNode) {
      return { nodesWithDraft: rawNodes, edgesWithDraft: edges };
    }
    const inputNode: DatasetTextInputNodeType = {
      id: DRAFT_NODE_ID,
      position: { x: 0, y: 0 },
      type: "datasetTextInputNode",
      draggable: false,
      selectable: false,
      data: {
        parentId: draftNode.parentId,
        mode: draftNode.mode,
        existingNames: draftNode.existingNames,
        onCancel: () => setDraftNode(null),
        onSubmit: (name: string) => {
          if (draftNode.mode === "collection") {
            handleAddCollection(name);
            setSelectedNodeId(`${COLLECTION_ROOT_PREFIX}${name}`);
          } else if (draftNode.collectionName) {
            handleAddField(
              draftNode.collectionName,
              name,
              draftNode.parentFieldPath,
            );
            const fieldPath = draftNode.parentFieldPath
              ? `${draftNode.parentFieldPath}.${name}`
              : name;
            setSelectedNodeId(`field-${draftNode.collectionName}-${fieldPath}`);
          }
          setDraftNode(null);
        },
      },
    };
    const draftEdge: Edge = {
      id: "draft-edge",
      source: draftNode.parentId,
      target: DRAFT_NODE_ID,
      animated: true,
    };
    // Patch the parent node so it renders its source handle even if it has no
    // real children yet — otherwise the draft edge has nowhere to anchor and
    // the connecting line doesn't appear (e.g. adding the first nested field
    // to a leaf field, or the first field to an empty collection).
    const patchedNodes = rawNodes.map((n) =>
      n.id === draftNode.parentId
        ? { ...n, data: { ...n.data, hasChildren: true } }
        : n,
    );
    return {
      nodesWithDraft: [...patchedNodes, inputNode],
      edgesWithDraft: [...edges, draftEdge],
    };
  }, [rawNodes, edges, draftNode, handleAddCollection, handleAddField]);

  const { nodes: layoutedNodes, edges: layoutedEdges } = useDatasetNodeLayout({
    nodes: nodesWithDraft,
    edges: edgesWithDraft,
    options: LAYOUT_OPTIONS,
  });

  // Merge selection + highlight state into nodes. The draft node is not a
  // real dataset node, so it never matches selectedNodeId / highlightedNodeId.
  const nodes = useMemo(
    () =>
      layoutedNodes.map((node) => ({
        ...node,
        selected: node.id === selectedNodeId,
        data: {
          ...node.data,
          isHighlighted: node.id === highlightedNodeId,
          ...(node.id === DATASET_ROOT_ID && { allowAddCollection }),
        },
      })),
    [layoutedNodes, selectedNodeId, highlightedNodeId, allowAddCollection],
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
          return {
            ...c,
            fields: removeFieldAtPath(c.fields ?? [], segments),
          };
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
        setDraftNode({
          parentId: DATASET_ROOT_ID,
          mode: "collection",
          existingNames: currentDataset.collections.map((c) => c.name),
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
        const parentId = parentFieldPath
          ? `field-${collectionName}-${parentFieldPath}`
          : `${COLLECTION_ROOT_PREFIX}${collectionName}`;
        setDraftNode({
          parentId,
          mode: "field",
          existingNames: siblingFields.map((f) => f.name),
          collectionName,
          parentFieldPath,
        });
      },
      deleteCollection: handleDeleteCollection,
      deleteField: handleDeleteField,
    }),
    [handleDeleteCollection, handleDeleteField],
  );

  const datasetLabel = dataset.name || dataset.fides_key;

  return (
    <DatasetEditorActionsContext.Provider value={editorActions}>
      <Flex ref={reactFlowRef} className="size-full" vertical>
        {/* Toolbar / Breadcrumb navigation */}
        <Flex
          align="center"
          justify="space-between"
          className="shrink-0 border-b border-neutral-2 bg-white px-3 py-1.5"
        >
          <Flex align="center" className="shrink-0">
            <Flex align="center" gap="small" className="shrink-0">
              <Icons.Code size={14} />
              <Typography.Text className="select-none text-xs">
                YAML
              </Typography.Text>
              <Switch
                size="small"
                checked={yamlPanelOpen}
                onChange={handleToggleYamlPanel}
                aria-label="Toggle YAML editor"
              />
            </Flex>
            <Divider vertical className="ml-3 mr-1" />
            {focusedCollection && (
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
                          className="!h-auto !p-0"
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
          </Flex>
          <Flex align="center" gap="small" className="shrink-0">
            {availableCategories.length > 0 && (
              <Select
                mode="multiple"
                allowClear
                placeholder="Filter by category"
                aria-label="Filter by data category"
                options={categoryOptions}
                value={categoryFilter}
                onChange={(value) => setCategoryFilter(value ?? [])}
                className="min-w-[200px] max-w-[400px]"
                size="small"
                showSearch
              />
            )}
          </Flex>
        </Flex>
        <Splitter
          className="min-h-0 flex-auto"
          onResize={(sizes) => setYamlPanelSize(sizes[0])}
        >
          {/* Collapsible YAML editor panel */}
          <Splitter.Panel
            size={yamlPanelSize}
            min={yamlPanelOpen ? 200 : 0}
            max={yamlPanelOpen ? "60%" : 0}
          >
            {yamlPanelOpen && (
              <Flex
                vertical
                className="h-full border-r border-neutral-2 bg-white"
              >
                <Flex
                  align="center"
                  justify="space-between"
                  className="shrink-0 border-b border-neutral-2 px-3 py-1"
                >
                  <Flex align="center" gap="small">
                    <Typography.Text strong className="select-none text-xs">
                      YAML Editor
                    </Typography.Text>
                    {yamlError && (
                      <Typography.Text type="danger" className="text-xs">
                        {yamlError}
                      </Typography.Text>
                    )}
                  </Flex>
                  <Button
                    type="text"
                    size="small"
                    icon={<Icons.Close />}
                    onClick={() => {
                      setYamlPanelOpen(false);
                      setYamlPanelSize(0);
                    }}
                    aria-label="Close YAML editor"
                  />
                </Flex>
                <div className="min-h-0 flex-auto">
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
          </Splitter.Panel>
          <Splitter.Panel>
            <div
              className="h-full"
              style={{ backgroundColor: "var(--fidesui-bg-corinth)" }}
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
                    color="var(--fidesui-neutral-100)"
                    variant={BackgroundVariant.Dots}
                    size={3}
                  />
                  <Controls showInteractive={false} />
                </ReactFlow>
              </DatasetTreeHoverProvider>
            </div>
          </Splitter.Panel>
        </Splitter>
        <DatasetNodeDetailPanel
          ref={detailPanelRef}
          open={!!selectedNodeData}
          onClose={() => {
            setSelectedNodeId(null);
          }}
          nodeData={selectedNodeData}
          onUpdateCollection={handleUpdateCollection}
          onUpdateField={handleUpdateField}
          allowNameEditing={allowNameEditing}
          isSaas={isSaas}
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
