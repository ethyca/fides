import {
  Button,
  Flex,
  Form,
  Modal,
  Select,
  Typography,
  useMessage,
} from "fidesui";
import { useState } from "react";

import TemplateVariableInput from "~/features/common/TemplateVariableInput";
import { usePatchDatastoreConnectionSecretsMutation } from "~/features/datastore-connections";
import {
  useGetJiraIssueTypesQuery,
  useGetJiraProjectsQuery,
  useGetJiraStatusesQuery,
  useGetJiraTemplateVariablesQuery,
  usePreviewJiraTicketMutation,
} from "~/features/plus/plus.slice";
import { ConnectionConfigurationResponse, JiraTicketData } from "~/types/api";

const DUE_DATE_TYPE_NONE = "none";
const DUE_DATE_TYPE_FIXED_DAYS = "fixed_days";
const DUE_DATE_OPTIONS = [
  { value: DUE_DATE_TYPE_NONE, label: "No due date" },
  { value: "7", label: "7 days" },
  { value: "14", label: "14 days" },
  { value: "30", label: "30 days" },
  { value: "45", label: "45 days" },
  { value: "60", label: "60 days" },
];

interface JiraConfigTabProps {
  connection: ConnectionConfigurationResponse;
}

interface JiraConfigFormValues {
  project_key?: string;
  issue_type?: string;
  completion_status?: string;
  summary_template?: string;
  description_template?: string;
  due_date_days?: string;
}

const JiraConfigTab = ({ connection }: JiraConfigTabProps) => {
  const [form] = Form.useForm<JiraConfigFormValues>();
  const message = useMessage();
  const [previewVisible, setPreviewVisible] = useState(false);
  const [previewData, setPreviewData] = useState<JiraTicketData | null>(null);

  const secrets = (connection as any)?.secrets as
    | Record<string, any>
    | undefined;

  const selectedProject = Form.useWatch("project_key", form);
  const selectedIssueType = Form.useWatch("issue_type", form);
  const summaryTemplate = Form.useWatch("summary_template", form);
  const descriptionTemplate = Form.useWatch("description_template", form);

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

  const { data: statuses, isLoading: statusesLoading } =
    useGetJiraStatusesQuery(
      {
        connectionKey: connection.key,
        projectKey: selectedProject!,
        issueType: selectedIssueType!,
      },
      { skip: !connection.key || !selectedProject || !selectedIssueType },
    );

  const { data: templateVariables } = useGetJiraTemplateVariablesQuery(
    { connectionKey: connection.key },
    { skip: !connection.key },
  );

  const [patchSecrets, { isLoading: isSaving }] =
    usePatchDatastoreConnectionSecretsMutation();

  const [previewJiraTicket, { isLoading: isPreviewing }] =
    usePreviewJiraTicketMutation();

  const handleProjectChange = () => {
    form.setFieldValue("issue_type", undefined);
    form.setFieldValue("completion_status", undefined);
  };

  const handlePreview = async () => {
    setPreviewData(null);
    try {
      const result = await previewJiraTicket({
        connectionKey: connection.key,
        summary_template: summaryTemplate,
        description_template: descriptionTemplate,
      }).unwrap();
      setPreviewData(result);
      setPreviewVisible(true);
    } catch {
      message.error("Failed to generate preview");
    }
  };

  const handleSave = async (values: JiraConfigFormValues) => {
    const secretsPayload: Record<string, any> = {
      project_key: values.project_key,
      issue_type: values.issue_type,
      completion_status: values.completion_status || null,
      summary_template: values.summary_template,
      description_template: values.description_template,
    };

    if (values.due_date_days && values.due_date_days !== DUE_DATE_TYPE_NONE) {
      secretsPayload.due_date_config = {
        type: DUE_DATE_TYPE_FIXED_DAYS,
        days: parseInt(values.due_date_days, 10),
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
    <Flex vertical gap="middle" className="max-w-screen-md pt-4">
      <Typography.Paragraph type="secondary">
        Configure how Fides creates Jira tickets for privacy requests.
      </Typography.Paragraph>

      <Form
        form={form}
        layout="vertical"
        onFinish={handleSave}
        initialValues={{
          project_key: secrets?.project_key || undefined,
          issue_type: secrets?.issue_type || undefined,
          completion_status: secrets?.completion_status || undefined,
          summary_template: secrets?.summary_template || undefined,
          description_template: secrets?.description_template || undefined,
          due_date_days:
            secrets?.due_date_config?.type === DUE_DATE_TYPE_FIXED_DAYS
              ? String(secrets.due_date_config.days)
              : DUE_DATE_TYPE_NONE,
        }}
      >
        <Form.Item
          name="project_key"
          label="Project"
          rules={[{ required: true, message: "Select a Jira project" }]}
        >
          <Select
            aria-label="Project"
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
            aria-label="Issue type"
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

        <Form.Item
          name="completion_status"
          label="Completion trigger"
          tooltip="Which Jira status should trigger Fides to mark the request as complete? Leave as default to use any Done-category status."
        >
          <Select
            aria-label="Completion trigger"
            placeholder="Default (any Done-category status)"
            loading={statusesLoading}
            disabled={!selectedProject}
            allowClear
            showSearch
            optionFilterProp="label"
            options={statuses?.map((s) => ({
              value: s.name,
              label: s.name,
            }))}
          />
        </Form.Item>

        <Form.Item
          name="summary_template"
          label="Summary template"
          rules={[{ required: true, message: "Enter a summary template" }]}
          tooltip="Insert template variables with /"
        >
          <TemplateVariableInput
            variables={templateVariables ?? []}
            rows={2}
            placeholder={`e.g. "DSR: __REQUEST_TYPE__ for __EMAIL__"; Enter / for variables`}
          />
        </Form.Item>

        <Form.Item
          name="description_template"
          label="Description template"
          tooltip="Insert template variables with /"
        >
          <TemplateVariableInput
            variables={templateVariables ?? []}
            rows={6}
            placeholder={`e.g. "Privacy request __REQUEST_ID__ submitted on __SUBMISSION_DATE__"; Enter / for variables`}
          />
        </Form.Item>

        <Form.Item
          name="due_date_days"
          label="Due date (time after approval)"
          className="mt-4"
        >
          <Select aria-label="Due date" options={DUE_DATE_OPTIONS} />
        </Form.Item>

        <Flex justify="end" gap="middle" className="mt-4">
          <Button
            onClick={handlePreview}
            loading={isPreviewing}
            disabled={!summaryTemplate}
          >
            Preview ticket
          </Button>
          <Button type="primary" htmlType="submit" loading={isSaving}>
            Save configuration
          </Button>
        </Flex>
      </Form>

      <Modal
        title="Ticket preview"
        open={previewVisible}
        onCancel={() => setPreviewVisible(false)}
        footer={null}
      >
        {previewData && (
          <Flex vertical gap="small">
            <div>
              <Typography.Text strong>Summary</Typography.Text>
              <Typography.Paragraph className="mt-1">
                {previewData.summary}
              </Typography.Paragraph>
            </div>
            <div>
              <Typography.Text strong>Description</Typography.Text>
              <Typography.Paragraph className="mt-1 whitespace-pre-wrap">
                {previewData.description}
              </Typography.Paragraph>
            </div>
          </Flex>
        )}
      </Modal>
    </Flex>
  );
};

export default JiraConfigTab;
