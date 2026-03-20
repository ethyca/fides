import {
  Button,
  Card,
  Flex,
  Form,
  InputNumber,
  Select,
  Typography,
  useMessage,
} from "fidesui";
import { useEffect, useState } from "react";

import { usePatchDatastoreConnectionSecretsMutation } from "~/features/datastore-connections";
import {
  useGetJiraIssueTypesQuery,
  useGetJiraProjectsQuery,
  useGetJiraTemplateVariablesQuery,
  usePreviewJiraTicketMutation,
} from "~/features/plus/plus.slice";
import { ConnectionConfigurationResponse } from "~/types/api";

import JiraTicketPreviewCard from "./JiraTicketPreviewCard";
import TemplateVariableTextArea from "./TemplateVariableTextArea";

interface JiraConfigTabProps {
  connection: ConnectionConfigurationResponse;
}

interface JiraConfigFormValues {
  project_key?: string;
  issue_type?: string;
  summary_template?: string;
  description_template?: string;
  due_date_type?: string;
  due_date_days?: number;
}

const JiraConfigTab = ({ connection }: JiraConfigTabProps) => {
  const [form] = Form.useForm<JiraConfigFormValues>();
  const message = useMessage();

  // Read saved config from connection secrets
  const secrets = (connection as any)?.secrets as
    | Record<string, any>
    | undefined;

  // Pre-populate form from saved secrets
  useEffect(() => {
    if (secrets) {
      form.setFieldsValue({
        project_key: secrets.project_key || undefined,
        issue_type: secrets.issue_type || undefined,
        summary_template: secrets.summary_template || undefined,
        description_template: secrets.description_template || undefined,
        due_date_type: secrets.due_date_config?.type || "none",
        due_date_days: secrets.due_date_config?.days || undefined,
      });
    }
  }, [secrets, form]);

  const selectedProject = Form.useWatch("project_key", form);
  const dueDateType = Form.useWatch("due_date_type", form);

  // RTK Query hooks
  const { data: projects, isLoading: projectsLoading } =
    useGetJiraProjectsQuery(
      { connectionKey: connection.key },
      { skip: !connection.key },
    );

  const { data: issueTypes, isLoading: issueTypesLoading } =
    useGetJiraIssueTypesQuery(
      { connectionKey: connection.key, projectKey: selectedProject! },
      { skip: !connection.key || !selectedProject },
    );

  const { data: templateVariables } =
    useGetJiraTemplateVariablesQuery(
      { connectionKey: connection.key },
      { skip: !connection.key },
    );

  const [previewJiraTicket] = usePreviewJiraTicketMutation();
  const [patchSecrets, { isLoading: isSaving }] =
    usePatchDatastoreConnectionSecretsMutation();

  const [previewData, setPreviewData] = useState<any>(null);

  const handleProjectChange = () => {
    form.setFieldValue("issue_type", undefined);
  };

  const handlePreview = async () => {
    const values = form.getFieldsValue();
    try {
      const result = await previewJiraTicket({
        connectionKey: connection.key,
        body: {
          summary_template: values.summary_template,
          description_template: values.description_template,
        },
      }).unwrap();
      setPreviewData(result);
    } catch {
      message.error("Failed to preview ticket. Check your templates.");
    }
  };

  const handleSave = async (values: JiraConfigFormValues) => {
    const secretsPayload: Record<string, any> = {
      project_key: values.project_key,
      issue_type: values.issue_type,
      summary_template: values.summary_template,
      description_template: values.description_template,
    };

    if (values.due_date_type && values.due_date_type !== "none") {
      secretsPayload.due_date_config = {
        type: values.due_date_type,
        days: values.due_date_days,
      };
    } else {
      secretsPayload.due_date_config = null;
    }

    try {
      await patchSecrets({
        connection_key: connection.key,
        secrets: secretsPayload,
      }).unwrap();
      message.success("Jira configuration saved");
    } catch {
      message.error("Failed to save configuration");
    }
  };

  return (
    <Flex vertical gap="middle" style={{ paddingTop: 16 }}>
      <Typography.Paragraph type="secondary">
        Configure how Fides creates Jira tickets for privacy requests.
      </Typography.Paragraph>

      <Form form={form} layout="vertical" onFinish={handleSave}>
        <Card title="Project & Issue Type" size="small">
          <Form.Item
            name="project_key"
            label="Project"
            rules={[{ required: true, message: "Select a Jira project" }]}
          >
            <Select
              placeholder="Select a project"
              loading={projectsLoading}
              onChange={handleProjectChange}
              showSearch
              optionFilterProp="label"
              options={projects?.map((p) => ({
                value: p.key,
                label: `${p.name} (${p.key})`,
              }))}
            />
          </Form.Item>
          <Form.Item
            name="issue_type"
            label="Issue type"
            rules={[{ required: true, message: "Select an issue type" }]}
          >
            <Select
              placeholder={
                selectedProject
                  ? "Select an issue type"
                  : "Select a project first"
              }
              loading={issueTypesLoading}
              disabled={!selectedProject}
              options={issueTypes
                ?.filter((t) => !t.subtask)
                .map((t) => ({
                  value: t.name,
                  label: t.name,
                }))}
            />
          </Form.Item>
        </Card>

        <Card
          title="Ticket Templates"
          size="small"
          style={{ marginTop: 16 }}
        >
          <Form.Item
            name="summary_template"
            label="Summary template"
            rules={[{ required: true, message: "Enter a summary template" }]}
          >
            <TemplateVariableTextArea
              variables={templateVariables ?? []}
              rows={2}
              placeholder="e.g. DSR: {{ request_type }} for {{ email }}"
            />
          </Form.Item>

          <Form.Item
            name="description_template"
            label="Description template"
          >
            <TemplateVariableTextArea
              variables={templateVariables ?? []}
              rows={6}
              placeholder="e.g. Privacy request {{ request_id }} submitted on {{ submission_date }}."
            />
          </Form.Item>

          <Button onClick={handlePreview}>Preview ticket</Button>
          {previewData && <JiraTicketPreviewCard data={previewData} />}
        </Card>

        <Card title="Due Date" size="small" style={{ marginTop: 16 }}>
          <Form.Item name="due_date_type" label="Due date calculation">
            <Select
              options={[
                { value: "none", label: "No due date" },
                {
                  value: "fixed_days",
                  label: "Fixed number of days after approval",
                },
              ]}
            />
          </Form.Item>
          {dueDateType === "fixed_days" && (
            <Form.Item
              name="due_date_days"
              label="Days after approval"
              rules={[
                { required: true, message: "Enter number of days" },
              ]}
            >
              <InputNumber min={1} style={{ width: "100%" }} />
            </Form.Item>
          )}
        </Card>

        <Flex justify="end" gap="middle" style={{ marginTop: 16 }}>
          <Button type="primary" htmlType="submit" loading={isSaving}>
            Save configuration
          </Button>
        </Flex>
      </Form>
    </Flex>
  );
};

export default JiraConfigTab;
