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
  Input,
  notification,
  Radio,
  SelectProps,
  Space,
  Text,
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
import PolicyNode, { PolicyNodeType } from "./PolicyNode";

export enum EditorMode {
  Builder = "builder",
  Code = "code",
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
}

const POLICY_NODE_ID = "policy";

const DEFAULT_ZOOM = 1;

const CenterOnInitialLoad = ({ layoutedNodes }: { layoutedNodes: Node[] }) => {
  const { fitView } = useReactFlow();
  const hasCenteredRef = useRef(false);

  useEffect(() => {
    const allMeasured =
      layoutedNodes.length > 0 &&
      layoutedNodes.every((n) => (n as any).measured?.width);

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
        duration: 500,
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
  } = props;

  const [nodes, setNodes, onNodesChange] = useNodesState(
    createPolicyNode(props),
  );
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [lastCreatedNodeId, setLastCreatedNodeId] = useState<string | null>(
    null,
  );
  const clearLastCreatedNodeId = useCallback(
    () => setLastCreatedNodeId(null),
    [],
  );

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
              onNameChange,
              onDescriptionChange,
              onControlGroupChange,
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
      onNameChange,
      onDescriptionChange,
      onControlGroupChange,
      onAddNode,
      handleAddConditionFromNode,
      handleAddActionFromNode,
      handleAddConstraintFromNode,
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

      <Flex gap="large" className="p-6">
        {/* Main area */}
        <Flex vertical flex={1} gap="middle">
          <Radio.Group
            value={mode}
            onChange={(e) => setMode(e.target.value)}
            optionType="button"
            buttonStyle="solid"
            options={[
              { label: "Builder", value: EditorMode.Builder },
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
            <ReactFlowProvider>
              <PolicyCanvasPanel
                name={name}
                description={description}
                controlGroup={controlGroup}
                controlGroupOptions={controlGroupOptions}
                onNameChange={handleNameChange}
                onDescriptionChange={handleDescriptionChange}
                onControlGroupChange={handleControlGroupChange}
                onAddNode={handleAddNode}
              />
            </ReactFlowProvider>
          )}
        </Flex>

        {/* Sidebar */}
        <Flex vertical gap="middle" className="w-80">
          <Flex vertical gap="small">
            <Text>AI assistant</Text>
            <Input.TextArea
              placeholder="Ask AI to help build or explain your policy..."
              aria-label="AI assistant"
              rows={6}
              disabled
              data-testid="ai-chat-placeholder"
            />
          </Flex>
        </Flex>
      </Flex>
    </Layout>
  );
};

export default AccessPolicyEditor;
