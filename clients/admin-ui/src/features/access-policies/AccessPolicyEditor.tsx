import "@xyflow/react/dist/style.css";

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
  useEdgesState,
  useNodesState,
  useReactFlow,
} from "@xyflow/react";
import {
  Button,
  Flex,
  Icons,
  Popconfirm,
  Radio,
  SelectProps,
  Space,
  useMessage,
} from "fidesui";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import Layout from "~/features/common/Layout";
import { ACCESS_POLICIES_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import { Editor } from "~/features/common/yaml/helpers";
import { getLayoutedElements } from "~/features/datamap/layout-utils";

import {
  AccessPolicy,
  useGetControlGroupsQuery,
} from "./access-policies.slice";
import ConstraintNode, { ConstraintNodeType } from "./ConstraintNode";
import ActionNode, { ActionNodeType } from "./DecisionNode";
import LabeledEdge from "./LabeledEdge";
import ConditionNode, { ConditionNodeType } from "./MatchNode";
import {
  deriveLayoutEdges,
  nodesToYaml,
  parseYaml,
  POLICY_NODE_ID,
  yamlToNodesAndEdges,
} from "./policy-yaml";
import PolicyNode, { PolicyNodeType } from "./PolicyNode";
import {
  ActionType,
  ConditionOperator,
  ConditionProperty,
  ConsentRequirement,
  ConstraintType,
  DataFlowDirection,
  DataFlowOperator,
  GeoOperator,
} from "./types";

export enum EditorMode {
  Builder = "builder",
  Code = "code",
  Split = "split",
}

export interface SidebarFormValues {
  name: string;
  description: string;
  control_group?: string;
}

interface AccessPolicyEditorProps {
  policyId?: string;
  initialValues?: AccessPolicy;
  onSave?: (values: SidebarFormValues, yaml: string) => void;
  onDelete?: () => void;
}

const nodeTypes: NodeTypes = {
  actionNode: ActionNode,
  conditionNode: ConditionNode,
  constraintNode: ConstraintNode,
  policyNode: PolicyNode,
};

const edgeTypes: EdgeTypes = {
  labeledEdge: LabeledEdge,
};

interface PolicyCanvasPanelProps {
  controls: string[];
  controlOptions: NonNullable<SelectProps["options"]>;
  onControlsChange: (value: string[]) => void;
  onYamlChange?: (yaml: string) => void;
  initialYaml?: string;
  syncKey?: number;
}

const DEFAULT_ZOOM = 1;

const CenterOnInitialLoad = ({ layoutedNodes }: { layoutedNodes: Node[] }) => {
  const { fitView } = useReactFlow();
  const hasCenteredRef = useRef(false);

  useEffect(() => {
    const allMeasured =
      layoutedNodes.length > 0 &&
      layoutedNodes.every(
        (n) => (n as Node & { measured?: { width?: number } }).measured?.width,
      );

    if (hasCenteredRef.current || !allMeasured) {
      return undefined;
    }
    hasCenteredRef.current = true;
    const timer = setTimeout(
      () =>
        fitView({
          nodes: layoutedNodes,
          minZoom: DEFAULT_ZOOM,
          maxZoom: DEFAULT_ZOOM,
          padding: 0.5,
          duration: 0,
        }),
      100,
    );
    return () => clearTimeout(timer);
  }, [layoutedNodes, fitView]);

  return null;
};

const CenterOnNewNode = ({
  lastCreatedNodeId,
  layoutedNodes,
  onCentered,
}: {
  lastCreatedNodeId: string | null;
  layoutedNodes: Node[];
  onCentered: () => void;
}) => {
  const { fitView, getZoom } = useReactFlow();
  useEffect(() => {
    if (!lastCreatedNodeId || layoutedNodes.length === 0) {
      return undefined;
    }

    const node = layoutedNodes.find((n) => n.id === lastCreatedNodeId);
    if (!node) {
      return undefined;
    }

    const zoom = getZoom();
    const timer = setTimeout(() => {
      fitView({
        nodes: [node],
        minZoom: zoom,
        maxZoom: zoom,
        padding: 0.5,
        duration: 400,
      });
      onCentered();
    }, 150);

    return () => clearTimeout(timer);
  }, [lastCreatedNodeId, layoutedNodes, fitView, getZoom, onCentered]);

  return null;
};

const createPolicyNode = (props: PolicyCanvasPanelProps): Node[] => [
  {
    id: POLICY_NODE_ID,
    type: "policyNode",
    position: { x: 0, y: 0 },
    style: { width: 300 },
    data: {
      name: "",
      description: "",
      fidesKey: "",
      enabled: true,
      priority: 0,
      controls: props.controls,
      controlOptions: props.controlOptions,
      actionMessage: "",
      onNameChange: () => {},
      onDescriptionChange: () => {},
      onFidesKeyChange: () => {},
      onEnabledChange: () => {},
      onPriorityChange: () => {},
      onControlsChange: props.onControlsChange,
      onActionMessageChange: () => {},
    },
  } satisfies PolicyNodeType,
];

/** Find the last node in a vertical chain of a given type. */
const findLastInChain = (
  nodeType: string,
  nodes: Node[],
  edges: Edge[],
): Node | undefined => {
  const typed = nodes.filter((n) => n.type === nodeType);
  if (typed.length === 0) {
    return undefined;
  }
  // The last node has no outgoing edge to another node of the same type
  return typed.find(
    (n) =>
      !edges.some(
        (e) =>
          e.source === n.id &&
          nodes.find((t) => t.id === e.target)?.type === nodeType,
      ),
  );
};

/** Find the first node of a type (the one whose incoming edge is NOT from same type). */
const findFirstOfType = (
  nodeType: string,
  nodes: Node[],
  edges: Edge[],
): Node | undefined => {
  const typed = nodes.filter((n) => n.type === nodeType);
  if (typed.length === 0) {
    return undefined;
  }
  return typed.find(
    (n) =>
      !edges.some(
        (e) =>
          e.target === n.id &&
          nodes.find((t) => t.id === e.source)?.type === nodeType,
      ),
  );
};

const PolicyCanvasPanel = (props: PolicyCanvasPanelProps) => {
  const {
    controls,
    controlOptions,
    onControlsChange,
    onYamlChange,
    initialYaml,
    syncKey,
  } = props;

  const initialResult = useMemo(
    () => (initialYaml ? yamlToNodesAndEdges(initialYaml) : null),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [],
  );

  const [nodes, setNodes, onNodesChange] = useNodesState(
    initialResult?.nodes ?? createPolicyNode(props),
  );
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>(
    initialResult?.edges ?? [],
  );
  const [lastCreatedNodeId, setLastCreatedNodeId] = useState<string | null>(
    null,
  );
  const clearLastCreatedNodeId = useCallback(
    () => setLastCreatedNodeId(null),
    [],
  );

  // When syncKey increments (Code → Builder switch), re-parse initialYaml
  const prevSyncKeyRef = useRef<number | undefined>(undefined);
  useEffect(() => {
    if (syncKey === undefined || syncKey === prevSyncKeyRef.current) {
      return;
    }
    prevSyncKeyRef.current = syncKey;
    const parsed = initialYaml ? yamlToNodesAndEdges(initialYaml) : null;
    if (parsed) {
      setNodes(parsed.nodes);
      setEdges(parsed.edges);
    } else {
      setNodes(createPolicyNode(props));
      setEdges([]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [syncKey]);

  const updateNodeData = useCallback(
    (nodeId: string, updates: Record<string, unknown>) => {
      setNodes((nds) =>
        nds.map((n) =>
          n.id === nodeId ? { ...n, data: { ...n.data, ...updates } } : n,
        ),
      );
    },
    [setNodes],
  );

  const deleteConditionNode = useCallback(
    (nodeId: string) => {
      const remainingConditions = nodes.filter(
        (n) => n.type === "conditionNode" && n.id !== nodeId,
      );

      if (remainingConditions.length === 0) {
        // Last condition: also remove all constraints
        const removeIds = new Set<string>([nodeId]);
        nodes
          .filter((n) => n.type === "constraintNode")
          .forEach((n) => removeIds.add(n.id));
        setNodes((nds) => nds.filter((n) => !removeIds.has(n.id)));
        setEdges((eds) =>
          eds.filter(
            (e) => !removeIds.has(e.source) && !removeIds.has(e.target),
          ),
        );
        return;
      }

      // Find incoming and outgoing edges for chain surgery
      const incomingEdge = edges.find((e) => e.target === nodeId);
      const outgoingAndEdge = edges.find(
        (e) =>
          e.source === nodeId &&
          nodes.find((n) => n.id === e.target)?.type === "conditionNode",
      );
      const outgoingUnlessEdge = edges.find(
        (e) =>
          e.source === nodeId &&
          nodes.find((n) => n.id === e.target)?.type === "constraintNode",
      );

      const newEdges: Edge[] = [];

      // Reconnect chain: incoming → next condition
      if (incomingEdge && outgoingAndEdge) {
        newEdges.push({
          ...incomingEdge,
          id: `e-${incomingEdge.source}-${outgoingAndEdge.target}`,
          target: outgoingAndEdge.target,
        });
      }

      // Transfer "unless" edge to next condition if this was first
      if (outgoingUnlessEdge) {
        const nextCondId = outgoingAndEdge?.target;
        if (nextCondId) {
          newEdges.push({
            ...outgoingUnlessEdge,
            id: `e-${nextCondId}-${outgoingUnlessEdge.target}`,
            source: nextCondId,
          });
        }
      }

      setNodes((nds) => nds.filter((n) => n.id !== nodeId));
      setEdges((eds) => [
        ...eds.filter((e) => e.source !== nodeId && e.target !== nodeId),
        ...newEdges,
      ]);
    },
    [nodes, edges, setNodes, setEdges],
  );

  const deleteConstraintNode = useCallback(
    (nodeId: string) => {
      const incomingEdge = edges.find((e) => e.target === nodeId);
      const outgoingAndEdge = edges.find(
        (e) =>
          e.source === nodeId &&
          nodes.find((n) => n.id === e.target)?.type === "constraintNode",
      );

      const newEdges: Edge[] = [];

      // Reconnect: incoming → next constraint
      if (incomingEdge && outgoingAndEdge) {
        newEdges.push({
          ...incomingEdge,
          id: `e-${incomingEdge.source}-${outgoingAndEdge.target}`,
          target: outgoingAndEdge.target,
        });
      }

      setNodes((nds) => nds.filter((n) => n.id !== nodeId));
      setEdges((eds) => [
        ...eds.filter((e) => e.source !== nodeId && e.target !== nodeId),
        ...newEdges,
      ]);
    },
    [nodes, edges, setNodes, setEdges],
  );

  const handleNameChange = useCallback(
    (value: string) => updateNodeData(POLICY_NODE_ID, { name: value }),
    [updateNodeData],
  );

  const handleDescriptionChange = useCallback(
    (value: string) => updateNodeData(POLICY_NODE_ID, { description: value }),
    [updateNodeData],
  );

  const handleFidesKeyChange = useCallback(
    (value: string) => updateNodeData(POLICY_NODE_ID, { fidesKey: value }),
    [updateNodeData],
  );

  const handleEnabledChange = useCallback(
    (value: boolean) => updateNodeData(POLICY_NODE_ID, { enabled: value }),
    [updateNodeData],
  );

  const handlePriorityChange = useCallback(
    (value: number) => updateNodeData(POLICY_NODE_ID, { priority: value }),
    [updateNodeData],
  );

  const handleControlsChange = useCallback(
    (value: string[]) => {
      updateNodeData(POLICY_NODE_ID, { controls: value });
      onControlsChange(value);
    },
    [updateNodeData, onControlsChange],
  );

  // Derive YAML from nodes/edges
  useEffect(() => {
    if (!onYamlChange) {
      return;
    }
    const derived = nodesToYaml(nodes, edges);
    onYamlChange(derived);
  }, [nodes, edges, onYamlChange]);

  const layoutEdges = useMemo(
    () => deriveLayoutEdges(nodes, edges),
    [nodes, edges],
  );

  const nodeSizes = useMemo(() => {
    const sizes: Record<string, { width: number; height: number }> = {};
    nodes.forEach((n) => {
      if (n.type === "conditionNode") {
        sizes[n.id] = { width: 320, height: 310 };
      } else if (n.type === "constraintNode") {
        sizes[n.id] = { width: 320, height: 380 };
      }
    });
    return sizes;
  }, [nodes]);

  const { nodes: layoutedNodes } = useMemo(
    () =>
      getLayoutedElements(nodes, layoutEdges, "LR", {
        ranksep: 80,
        nodesep: 60,
        nodeWidth: 320,
        nodeHeight: 100,
        nodeSizes,
        topAlign: true,
      }),
    [nodes, layoutEdges, nodeSizes],
  );

  const handleAddCondition = useCallback(() => {
    const actionNode = nodes.find((n) => n.type === "actionNode");
    if (!actionNode) {
      return;
    }

    const conditionCount = nodes.filter(
      (n) => n.type === "conditionNode",
    ).length;
    const conditionId = `condition-${conditionCount + 1}`;

    const newNode: ConditionNodeType = {
      id: conditionId,
      type: "conditionNode",
      position: { x: 0, y: 0 },
      style: { width: 300 },
      data: {},
    };

    let newEdge: Edge;

    if (conditionCount === 0) {
      // First condition: horizontal from action
      newEdge = {
        id: `e-${actionNode.id}-${conditionId}`,
        source: actionNode.id,
        target: conditionId,
        type: "labeledEdge",
        data: { label: "when" },
      };
    } else {
      // Chain: vertical "and" from last condition
      const lastCond = findLastInChain("conditionNode", nodes, edges);
      const sourceId = lastCond?.id ?? actionNode.id;
      newEdge = {
        id: `e-${sourceId}-${conditionId}`,
        source: sourceId,
        target: conditionId,
        sourceHandle: "bottom",
        targetHandle: "top",
        type: "labeledEdge",
        data: { label: "and" },
      };
    }

    setNodes((nds) => [...nds, newNode]);
    setEdges((eds) => [...eds, newEdge]);
    setLastCreatedNodeId(conditionId);
  }, [nodes, edges, setNodes, setEdges]);

  const handleAddActionFromNode = useCallback(
    (sourceNodeId: string) => {
      const sourceNode = nodes.find((n) => n.id === sourceNodeId);
      if (!sourceNode) {
        return;
      }

      const actionCount = nodes.filter((n) => n.type === "actionNode").length;
      const actionId = `action-${actionCount + 1}`;

      const newNode: ActionNodeType = {
        id: actionId,
        type: "actionNode",
        position: { x: 0, y: 0 },
        style: { width: 300 },
        data: {},
      };

      const newEdge: Edge = {
        id: `e-${sourceNodeId}-${actionId}`,
        source: sourceNodeId,
        target: actionId,
        type: "labeledEdge",
      };

      setNodes((nds) => [...nds, newNode]);
      setEdges((eds) => [...eds, newEdge]);
      setLastCreatedNodeId(actionId);
    },
    [nodes, setNodes, setEdges],
  );

  const handleAddConstraint = useCallback(() => {
    const constraintCount = nodes.filter(
      (n) => n.type === "constraintNode",
    ).length;
    const constraintId = `constraint-${constraintCount + 1}`;

    const newNode: ConstraintNodeType = {
      id: constraintId,
      type: "constraintNode",
      position: { x: 0, y: 0 },
      style: { width: 300 },
      data: {},
    };

    let newEdge: Edge;

    if (constraintCount === 0) {
      // First constraint: horizontal from first condition
      const firstCond = findFirstOfType("conditionNode", nodes, edges);
      const sourceId = firstCond?.id ?? "condition-1";
      newEdge = {
        id: `e-${sourceId}-${constraintId}`,
        source: sourceId,
        target: constraintId,
        type: "labeledEdge",
        data: { label: "unless" },
      };
    } else {
      // Chain: vertical "and" from last constraint
      const lastCons = findLastInChain("constraintNode", nodes, edges);
      const sourceId = lastCons?.id ?? `constraint-${constraintCount}`;
      newEdge = {
        id: `e-${sourceId}-${constraintId}`,
        source: sourceId,
        target: constraintId,
        sourceHandle: "bottom",
        targetHandle: "top",
        type: "labeledEdge",
        data: { label: "and" },
      };
    }

    setNodes((nds) => [...nds, newNode]);
    setEdges((eds) => [...eds, newEdge]);
    setLastCreatedNodeId(constraintId);
  }, [nodes, edges, setNodes, setEdges]);

  const policyHasChildren = edges.some((e) => e.source === POLICY_NODE_ID);
  const constraintsExist = nodes.some((n) => n.type === "constraintNode");
  const firstConditionId = findFirstOfType("conditionNode", nodes, edges)?.id;
  const lastConditionId = findLastInChain("conditionNode", nodes, edges)?.id;
  const firstConstraintId = findFirstOfType("constraintNode", nodes, edges)?.id;
  const lastConstraintId = findLastInChain("constraintNode", nodes, edges)?.id;

  const nodesWithCallbacks = useMemo(
    () =>
      layoutedNodes.map((node) => {
        if (node.id === POLICY_NODE_ID && node.type === "policyNode") {
          return {
            ...node,
            data: {
              ...node.data,
              controls,
              controlOptions,
              onNameChange: handleNameChange,
              onDescriptionChange: handleDescriptionChange,
              onFidesKeyChange: handleFidesKeyChange,
              onEnabledChange: handleEnabledChange,
              onPriorityChange: handlePriorityChange,
              onControlsChange: handleControlsChange,
              onAddAction: () => handleAddActionFromNode(POLICY_NODE_ID),
              hasChildren: policyHasChildren,
            },
          };
        }
        if (node.type === "actionNode") {
          const hasChildren = edges.some((e) => e.source === node.id);
          return {
            ...node,
            data: {
              ...node.data,
              onAddCondition: handleAddCondition,
              hasChildren,
              onActionTypeChange: (value: ActionType) =>
                updateNodeData(node.id, { actionType: value }),
              onActionMessageChange: (value: string) =>
                updateNodeData(node.id, { actionMessage: value }),
            },
          };
        }
        if (node.type === "conditionNode") {
          return {
            ...node,
            data: {
              ...node.data,
              isFirstOfType: node.id === firstConditionId,
              isLastOfType: node.id === lastConditionId,
              onAddCondition: handleAddCondition,
              onAddConstraint: handleAddConstraint,
              onDelete: () => deleteConditionNode(node.id),
              hasChildren: constraintsExist,
              onPropertyChange: (value: ConditionProperty) =>
                updateNodeData(node.id, { property: value, values: [] }),
              onValuesChange: (values: string[]) =>
                updateNodeData(node.id, { values }),
              onOperatorChange: (value: ConditionOperator) =>
                updateNodeData(node.id, { operator: value }),
            },
          };
        }
        if (node.type === "constraintNode") {
          return {
            ...node,
            data: {
              ...node.data,
              isFirstOfType: node.id === firstConstraintId,
              isLastOfType: node.id === lastConstraintId,
              onAddConstraint: handleAddConstraint,
              onDelete: () => deleteConstraintNode(node.id),
              onConstraintTypeChange: (value: ConstraintType) =>
                updateNodeData(node.id, {
                  constraintType: value,
                  // Reset all type-specific fields
                  privacyNoticeKey: undefined,
                  consentRequirement: undefined,
                  geoField: undefined,
                  geoOperator: undefined,
                  geoValues: undefined,
                  dataFlowDirection: undefined,
                  dataFlowOperator: undefined,
                  dataFlowSystems: undefined,
                }),
              // Consent callbacks
              onPrivacyNoticeKeyChange: (value: string) =>
                updateNodeData(node.id, { privacyNoticeKey: value }),
              onConsentRequirementChange: (value: ConsentRequirement) =>
                updateNodeData(node.id, { consentRequirement: value }),
              // Geo location callbacks
              onGeoFieldChange: (value: string) =>
                updateNodeData(node.id, { geoField: value }),
              onGeoOperatorChange: (value: GeoOperator) =>
                updateNodeData(node.id, { geoOperator: value }),
              onGeoValuesChange: (value: string[]) =>
                updateNodeData(node.id, { geoValues: value }),
              // Data flow callbacks
              onDataFlowDirectionChange: (value: DataFlowDirection) =>
                updateNodeData(node.id, { dataFlowDirection: value }),
              onDataFlowOperatorChange: (value: DataFlowOperator) =>
                updateNodeData(node.id, { dataFlowOperator: value }),
              onDataFlowSystemsChange: (value: string[]) =>
                updateNodeData(node.id, { dataFlowSystems: value }),
            },
          };
        }
        return node;
      }),
    [
      layoutedNodes,
      edges,
      controls,
      controlOptions,
      handleNameChange,
      handleDescriptionChange,
      handleFidesKeyChange,
      handleEnabledChange,
      handlePriorityChange,
      handleControlsChange,
      handleAddCondition,
      handleAddActionFromNode,
      handleAddConstraint,
      deleteConditionNode,
      deleteConstraintNode,
      updateNodeData,
      policyHasChildren,
      constraintsExist,
      firstConditionId,
      lastConditionId,
      firstConstraintId,
      lastConstraintId,
    ],
  );

  return (
    <div
      style={{
        height: "calc(100vh - 220px)",
        border: "1px solid var(--ant-color-border)",
        borderRadius: "var(--ant-border-radius-lg)",
      }}
    >
      <ReactFlow
        nodes={nodesWithCallbacks}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        defaultEdgeOptions={{ type: "labeledEdge" }}
        defaultViewport={{ x: 0, y: 0, zoom: DEFAULT_ZOOM }}
        nodesConnectable={false}
      >
        <Background variant={BackgroundVariant.Dots} gap={16} size={1} />
        <Controls />
        <CenterOnInitialLoad layoutedNodes={layoutedNodes} />
        <CenterOnNewNode
          lastCreatedNodeId={lastCreatedNodeId}
          layoutedNodes={layoutedNodes}
          onCentered={clearLastCreatedNodeId}
        />
      </ReactFlow>
    </div>
  );
};

const AccessPolicyEditor = ({
  policyId,
  initialValues,
  onSave,
  onDelete,
}: AccessPolicyEditorProps) => {
  const isNew = !policyId;
  const messageApi = useMessage();

  const { data: controlGroups = [] } = useGetControlGroupsQuery();

  const controlOptions = useMemo(
    () => controlGroups.map((cg) => ({ value: cg.key, label: cg.label })),
    [controlGroups],
  );

  const [mode, setMode] = useState<EditorMode>(EditorMode.Builder);
  const [yamlValue, setYamlValue] = useState<string>(initialValues?.yaml ?? "");
  const [controls, setControls] = useState<string[]>(
    initialValues?.controls ?? [],
  );
  const [syncKey, setSyncKey] = useState(0);

  const handleModeChange = useCallback(
    (newMode: EditorMode) => {
      if (mode === EditorMode.Code && newMode !== EditorMode.Code) {
        setSyncKey((k) => k + 1);
      }
      setMode(newMode);
    },
    [mode],
  );

  const handleYamlChange = useCallback((derivedYaml: string) => {
    setYamlValue(derivedYaml);
  }, []);

  const handleSave = () => {
    const parsed = parseYaml(yamlValue);
    const name = parsed?.name ?? "";
    if (!name.trim()) {
      messageApi.error("Name is required.");
      return;
    }
    onSave?.(
      {
        name,
        description: parsed?.description ?? "",
        control_group: controls.length > 0 ? controls.join(",") : undefined,
      },
      yamlValue,
    );
  };

  const handleControlsChange = useCallback(
    (value: string[]) => setControls(value),
    [],
  );

  const parsedForDisplay = useMemo(() => parseYaml(yamlValue), [yamlValue]);
  const displayName = parsedForDisplay?.name ?? "";

  const handleExport = () => {
    const blob = new Blob([yamlValue], { type: "text/yaml" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${displayName || "policy"}.yaml`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const title = isNew ? "New access policy" : "Edit access policy";
  const breadcrumbTitle = isNew
    ? "New policy"
    : displayName || (policyId as string);

  const canvasPanel = (
    <PolicyCanvasPanel
      controls={controls}
      controlOptions={controlOptions}
      onControlsChange={handleControlsChange}
      onYamlChange={handleYamlChange}
      initialYaml={yamlValue || undefined}
      syncKey={syncKey}
    />
  );

  return (
    <Layout title={title}>
      <PageHeader
        heading={title}
        breadcrumbItems={[
          { title: "Access policies", href: ACCESS_POLICIES_ROUTE },
          { title: breadcrumbTitle },
        ]}
        isSticky
        rightContent={
          <Space>
            {!isNew && (
              <Popconfirm
                title="Delete policy"
                description="Are you sure you want to delete this policy?"
                onConfirm={onDelete}
                okText="Delete"
                okButtonProps={{ danger: true }}
                cancelText="Cancel"
              >
                <Button
                  icon={<Icons.TrashCan />}
                  danger
                  aria-label="Delete policy"
                  data-testid="delete-btn"
                />
              </Popconfirm>
            )}
            <Button
              icon={<Icons.Download />}
              onClick={handleExport}
              data-testid="export-btn"
            >
              Export
            </Button>
            <Button type="primary" onClick={handleSave} data-testid="save-btn">
              Save
            </Button>
          </Space>
        }
      />

      <Flex vertical gap="middle">
        <Radio.Group
          value={mode}
          onChange={(e) => handleModeChange(e.target.value)}
          optionType="button"
          buttonStyle="solid"
          options={[
            { label: "Builder", value: EditorMode.Builder },
            ...(process.env.NEXT_PUBLIC_APP_ENV === "development"
              ? [{ label: "Split (dev only)", value: EditorMode.Split }]
              : []),
            { label: "Code", value: EditorMode.Code },
          ]}
          data-testid="mode-toggle"
        />

        {mode === EditorMode.Code && (
          <Editor
            defaultLanguage="yaml"
            value={yamlValue}
            height="calc(100vh - 220px)"
            onChange={(val) => setYamlValue(val ?? "")}
            options={{
              fontFamily: "Menlo",
              fontSize: 13,
              minimap: { enabled: false },
            }}
            theme="light"
          />
        )}

        {mode === EditorMode.Builder && (
          <ReactFlowProvider>{canvasPanel}</ReactFlowProvider>
        )}

        {mode === EditorMode.Split && (
          <Flex gap="middle">
            <div style={{ flex: "0 0 60%" }}>
              <ReactFlowProvider>{canvasPanel}</ReactFlowProvider>
            </div>
            <div style={{ flex: "0 0 calc(40% - 8px)" }}>
              <Editor
                defaultLanguage="yaml"
                value={yamlValue}
                height="calc(100vh - 220px)"
                options={{
                  fontFamily: "Menlo",
                  fontSize: 13,
                  minimap: { enabled: false },
                  readOnly: true,
                  domReadOnly: true,
                }}
                theme="light"
              />
            </div>
          </Flex>
        )}
      </Flex>
    </Layout>
  );
};

export default AccessPolicyEditor;
