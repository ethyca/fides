import "@xyflow/react/dist/style.css";

import {
  Background,
  BackgroundVariant,
  Node,
  NodeTypes,
  ReactFlow,
  ReactFlowProvider,
} from "@xyflow/react";
import {
  Button,
  Flex,
  Icons,
  Input,
  notification,
  Radio,
  Space,
  Text,
} from "fidesui";
import { useCallback, useMemo, useState } from "react";

import Layout from "~/features/common/Layout";
import { ACCESS_POLICIES_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import { Editor } from "~/features/common/yaml/helpers";

import { AccessPolicy } from "./access-policies.slice";
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

interface AccessPolicyFormProps {
  policyId?: string;
  initialValues?: AccessPolicy;
  onSave?: (values: SidebarFormValues, yaml: string) => void;
  onDelete?: () => void;
}

const nodeTypes: NodeTypes = { policyNode: PolicyNode };

interface PolicyCanvasPanelProps {
  name: string;
  description: string;
  controlGroup?: string;
  onNameChange: (value: string) => void;
  onDescriptionChange: (value: string) => void;
  onControlGroupChange: (value: string | undefined) => void;
}

const PolicyCanvasPanel = ({
  name,
  description,
  controlGroup,
  onNameChange,
  onDescriptionChange,
  onControlGroupChange,
}: PolicyCanvasPanelProps) => {
  const nodes: Node[] = useMemo(
    () => [
      {
        id: "policy",
        type: "policyNode",
        position: { x: 0, y: 0 },
        data: {
          name,
          description,
          controlGroup,
          onNameChange,
          onDescriptionChange,
          onControlGroupChange,
        },
      } satisfies PolicyNodeType,
    ],
    [
      name,
      description,
      controlGroup,
      onNameChange,
      onDescriptionChange,
      onControlGroupChange,
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
        nodes={nodes}
        edges={[]}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.5 }}
      >
        <Background variant={BackgroundVariant.Dots} gap={16} size={1} />
      </ReactFlow>
    </div>
  );
};

const AccessPolicyForm = ({
  policyId,
  initialValues,
  onSave,
  onDelete,
}: AccessPolicyFormProps) => {
  const isNew = !policyId;

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
                onNameChange={handleNameChange}
                onDescriptionChange={handleDescriptionChange}
                onControlGroupChange={handleControlGroupChange}
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

export default AccessPolicyForm;
