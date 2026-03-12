import "@xyflow/react/dist/style.css";

import {
  Background,
  BackgroundVariant,
  ReactFlow,
  ReactFlowProvider,
} from "@xyflow/react";
import {
  Button,
  Flex,
  Form,
  Icons,
  Input,
  Radio,
  Select,
  Space,
  Text,
} from "fidesui";
import { useState } from "react";

import Layout from "~/features/common/Layout";
import { ACCESS_POLICIES_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import { Editor } from "~/features/common/yaml/helpers";

import { AccessPolicy } from "./access-policies.slice";

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

const BuilderModePanel = () => (
  <div
    style={{
      height: "calc(100vh - 220px)",
      border: "1px solid var(--ant-color-border)",
      borderRadius: "var(--ant-border-radius-lg)",
    }}
  >
    <ReactFlow nodes={[]} edges={[]} fitView>
      <Background variant={BackgroundVariant.Dots} gap={16} size={1} />
    </ReactFlow>
  </div>
);

const AccessPolicyForm = ({
  policyId,
  initialValues,
  onSave,
  onDelete,
}: AccessPolicyFormProps) => {
  const isNew = !policyId;
  const [form] = Form.useForm<SidebarFormValues>();

  const [mode, setMode] = useState<EditorMode>(EditorMode.Builder);
  const [yamlValue, setYamlValue] = useState<string>(initialValues?.yaml ?? "");

  const handleFinish = (values: SidebarFormValues) => {
    onSave?.(values, yamlValue);
  };

  const handleExport = () => {
    const blob = new Blob([yamlValue], { type: "text/yaml" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${initialValues?.name ?? "policy"}.yaml`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const title = isNew ? "New access policy" : "Edit access policy";
  const breadcrumbTitle = isNew
    ? "New policy"
    : (initialValues?.name ?? (policyId as string));

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
            <Button
              type="primary"
              onClick={() => form.submit()}
              data-testid="save-btn"
            >
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
              <BuilderModePanel />
            </ReactFlowProvider>
          )}
        </Flex>

        {/* Sidebar */}
        <Flex vertical gap="middle" className="w-80">
          <Form
            form={form}
            layout="vertical"
            initialValues={{
              name: initialValues?.name ?? "",
              description: initialValues?.description ?? "",
              control_group: initialValues?.control_group,
            }}
            onFinish={handleFinish}
          >
            <Form.Item
              label="Name"
              name="name"
              rules={[{ required: true, message: "Name is required" }]}
            >
              <Input />
            </Form.Item>
            <Form.Item label="Description" name="description">
              <Input />
            </Form.Item>
            <Form.Item label="Control group" name="control_group">
              <Select
                placeholder="Select control group"
                options={[]}
                data-testid="control-group-select"
                aria-label="Select control group"
              />
            </Form.Item>
          </Form>

          {/* AI chat placeholder */}
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
