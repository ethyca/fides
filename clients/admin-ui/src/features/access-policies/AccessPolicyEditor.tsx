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
  notification,
  Radio,
  SelectProps,
  Space,
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
import ActionNode, { ActionNodeType } from "./ActionNode";
import ConditionNode, { ConditionNodeType } from "./ConditionNode";
import ConstraintNode, { ConstraintNodeType } from "./ConstraintNode";
import LabeledEdge from "./LabeledEdge";
import { nodesToYaml, yamlToNodesAndEdges } from "./policy-yaml";
import PolicyNode, { PolicyNodeType } from "./PolicyNode";
import {
  ActionType,
  ConditionOperator,
  ConditionProperty,
  ConsentValue,
  ConstraintType,
  UserOperator,
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
  name: string;
  description: string;
  controlGroup?: string;
  controlGroupOptions: NonNullable<SelectProps["options"]>;
  onNameChange: (value: string) => void;
  onDescriptionChange: (value: string) => void;
  onControlGroupChange: (value: string | undefined) => void;
  onAddNode?: () => void;
  onYamlChange?: (yaml: string) => void;
  initialYaml?: string;
}

const POLICY_NODE_ID = "policy";

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
      name: props.name,
      description: props.description,
      controlGroup: props.controlGroup,
      controlGroupOptions: props.controlGroupOptions,
      onNameChange: props.onNameChange,
      onDescriptionChange: props.onDescriptionChange,
      onControlGroupChange: props.onControlGroupChange,
      onAddNode: props.onAddNode,
    },
  } satisfies PolicyNodeType,
];

const PolicyCanvasPanel = (props: PolicyCanvasPanelProps) => {
  const {
    name,
    description,
    controlGroup,
    controlGroupOptions,
    onNameChange,
    onDescriptionChange,
    onControlGroupChange,
    onAddNode,
    onYamlChange,
    initialYaml,
  } = props;

  const initialResult = useMemo(
    () => (initialYaml ? yamlToNodesAndEdges(initialYaml) : null),
    // Only run once on mount
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

  // Wrap policy-level field changes so the nodes state stays in sync for nodesToYaml
  const handleNameChange = useCallback(
    (value: string) => {
      updateNodeData(POLICY_NODE_ID, { name: value });
      onNameChange(value);
    },
    [updateNodeData, onNameChange],
  );

  const handleDescriptionChange = useCallback(
    (value: string) => {
      updateNodeData(POLICY_NODE_ID, { description: value });
      onDescriptionChange(value);
    },
    [updateNodeData, onDescriptionChange],
  );

  const handleControlGroupChange = useCallback(
    (value: string | undefined) => {
      updateNodeData(POLICY_NODE_ID, { controlGroup: value });
      onControlGroupChange(value);
    },
    [updateNodeData, onControlGroupChange],
  );

  // Derive YAML from nodes/edges and call onYamlChange
  useEffect(() => {
    if (!onYamlChange) {
      return;
    }
    const derived = nodesToYaml(nodes, edges);
    onYamlChange(derived);
  }, [nodes, edges, onYamlChange]);

  const { nodes: layoutedNodes, edges: layoutedEdges } = useMemo(
    () =>
      getLayoutedElements(nodes, edges, "LR", {
        ranksep: 80,
        nodesep: 60,
        nodeWidth: 320,
        nodeHeight: 100,
      }),
    [nodes, edges],
  );

  const handleAddConditionFromNode = useCallback(
    (sourceNodeId: string) => {
      const sourceNode = nodes.find((n) => n.id === sourceNodeId);
      if (!sourceNode) {
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

      let label: string | undefined;
      if (sourceNode.type === "actionNode") {
        label = "when";
      } else if (sourceNode.type === "conditionNode") {
        label = "and";
      }

      const newEdge: Edge = {
        id: `e-${sourceNodeId}-${conditionId}`,
        source: sourceNodeId,
        target: conditionId,
        type: "labeledEdge",
        data: label ? { label } : undefined,
      };

      setNodes((nds) => [...nds, newNode]);
      setEdges((eds) => [...eds, newEdge]);
      setLastCreatedNodeId(conditionId);
    },
    [nodes, setNodes, setEdges],
  );

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

  const handleAddConstraintFromNode = useCallback(
    (sourceNodeId: string) => {
      const sourceNode = nodes.find((n) => n.id === sourceNodeId);
      if (!sourceNode) {
        return;
      }

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

      const newEdge: Edge = {
        id: `e-${sourceNodeId}-${constraintId}`,
        source: sourceNodeId,
        target: constraintId,
        type: "labeledEdge",
        data: { label: "unless" },
      };

      setNodes((nds) => [...nds, newNode]);
      setEdges((eds) => [...eds, newEdge]);
      setLastCreatedNodeId(constraintId);
    },
    [nodes, setNodes, setEdges],
  );

  const policyHasChildren = edges.some((e) => e.source === POLICY_NODE_ID);

  const nodesWithCallbacks = useMemo(
    () =>
      layoutedNodes.map((node) => {
        if (node.id === POLICY_NODE_ID && node.type === "policyNode") {
          return {
            ...node,
            data: {
              ...node.data,
              name,
              description,
              controlGroup,
              controlGroupOptions,
              onNameChange: handleNameChange,
              onDescriptionChange: handleDescriptionChange,
              onControlGroupChange: handleControlGroupChange,
              onAddNode,
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
              onAddNode,
              onAddCondition: () => handleAddConditionFromNode(node.id),
              hasChildren,
              onActionTypeChange: (value: ActionType) =>
                updateNodeData(node.id, { actionType: value }),
            },
          };
        }
        if (node.type === "conditionNode") {
          const hasChildren = edges.some((e) => e.source === node.id);
          return {
            ...node,
            data: {
              ...node.data,
              onAddNode,
              onAddCondition: () => handleAddConditionFromNode(node.id),
              onAddConstraint: () => handleAddConstraintFromNode(node.id),
              hasChildren,
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
              onConstraintTypeChange: (value: ConstraintType) =>
                updateNodeData(node.id, {
                  constraintType: value,
                  preferenceKey: undefined,
                  consentValue: undefined,
                  userKey: undefined,
                  userValue: undefined,
                  userOperator: undefined,
                }),
              onPreferenceKeyChange: (value: string) =>
                updateNodeData(node.id, { preferenceKey: value }),
              onConsentValueChange: (value: ConsentValue) =>
                updateNodeData(node.id, { consentValue: value }),
              onUserKeyChange: (value: string) =>
                updateNodeData(node.id, { userKey: value }),
              onUserValueChange: (value: string) =>
                updateNodeData(node.id, { userValue: value }),
              onUserOperatorChange: (value: UserOperator) =>
                updateNodeData(node.id, { userOperator: value }),
            },
          };
        }
        return node;
      }),
    [
      layoutedNodes,
      edges,
      name,
      description,
      controlGroup,
      controlGroupOptions,
      handleNameChange,
      handleDescriptionChange,
      handleControlGroupChange,
      onAddNode,
      handleAddConditionFromNode,
      handleAddActionFromNode,
      handleAddConstraintFromNode,
      updateNodeData,
      policyHasChildren,
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
        edges={layoutedEdges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        defaultEdgeOptions={{ type: "labeledEdge" }}
        defaultViewport={{ x: 0, y: 0, zoom: DEFAULT_ZOOM }}
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

  const { data: controlGroups = [] } = useGetControlGroupsQuery();

  const controlGroupOptions = useMemo(
    () => controlGroups.map((cg) => ({ value: cg.key, label: cg.label })),
    [controlGroups],
  );

  const [mode, setMode] = useState<EditorMode>(EditorMode.Builder);
  const [yamlValue, setYamlValue] = useState<string>(initialValues?.yaml ?? "");
  const [name, setName] = useState(initialValues?.name ?? "");
  const [description, setDescription] = useState(
    initialValues?.description ?? "",
  );
  const [controlGroup, setControlGroup] = useState<string | undefined>(
    initialValues?.control_group,
  );

  // Key that forces PolicyCanvasPanel to re-mount when switching from code to builder/split
  const [canvasKey, setCanvasKey] = useState(0);

  const handleModeChange = useCallback(
    (newMode: EditorMode) => {
      // When switching from code-only to a canvas mode, re-parse the YAML into nodes
      if (mode === EditorMode.Code && newMode !== EditorMode.Code) {
        setCanvasKey((k) => k + 1);
      }
      setMode(newMode);
    },
    [mode],
  );

  const handleYamlChange = useCallback((derivedYaml: string) => {
    setYamlValue(derivedYaml);
  }, []);

  const handleSave = () => {
    if (!name.trim()) {
      notification.error({ message: "Name is required." });
      return;
    }
    onSave?.({ name, description, control_group: controlGroup }, yamlValue);
  };

  const handleNameChange = useCallback((value: string) => setName(value), []);
  const handleDescriptionChange = useCallback(
    (value: string) => setDescription(value),
    [],
  );
  const handleControlGroupChange = useCallback(
    (value: string | undefined) => setControlGroup(value),
    [],
  );

  const handleAddNode = useCallback(() => {
    // TODO: implement add node logic
  }, []);

  const handleExport = () => {
    const blob = new Blob([yamlValue], { type: "text/yaml" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${name || "policy"}.yaml`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const title = isNew ? "New access policy" : "Edit access policy";
  const breadcrumbTitle = isNew ? "New policy" : name || (policyId as string);

  const canvasPanel = (
    <PolicyCanvasPanel
      key={canvasKey}
      name={name}
      description={description}
      controlGroup={controlGroup}
      controlGroupOptions={controlGroupOptions}
      onNameChange={handleNameChange}
      onDescriptionChange={handleDescriptionChange}
      onControlGroupChange={handleControlGroupChange}
      onAddNode={handleAddNode}
      onYamlChange={handleYamlChange}
      initialYaml={yamlValue || undefined}
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
              <Button
                icon={<Icons.TrashCan />}
                onClick={onDelete}
                danger
                aria-label="Delete policy"
                data-testid="delete-btn"
              />
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
            { label: "Split", value: EditorMode.Split },
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
