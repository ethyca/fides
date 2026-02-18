import {
  Button,
  Card,
  Descriptions,
  Flex,
  Form,
  Select,
  Space,
  Switch,
  Text,
  Typography,
  useNotification,
} from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import { useMemo, useState } from "react";

import { SystemSelect } from "~/features/common/dropdown/SystemSelect";
import { getErrorMessage } from "~/features/common/helpers";
import Layout from "~/features/common/Layout";
import { PRIVACY_ASSESSMENTS_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import {
  TemplateResponse,
  useCreatePrivacyAssessmentMutation,
  useGetAssessmentTemplatesQuery,
} from "~/features/privacy-assessments";
import { RTKErrorResult } from "~/types/errors/api";

const { Title, Paragraph } = Typography;
const { Item } = Form;

const EVALUATION_NOTIFICATION_KEY = "evaluation-progress";

interface FormValues {
  assessment_type: string;
  system_fides_key?: string;
  use_llm: boolean;
}

interface TemplateOptionData {
  value: string;
  label: string;
  template: TemplateResponse;
}

const renderTemplateOption = (option: { data: TemplateOptionData }) => {
  const { template } = option.data;
  return (
    <div>
      <Text strong>{template.name}</Text>
      {template.region && (
        <Text type="secondary" className="ml-2 text-xs">
          {template.region}
        </Text>
      )}
    </div>
  );
};

const EvaluateAssessmentPage: NextPage = () => {
  const router = useRouter();
  const notificationApi = useNotification();
  const [form] = Form.useForm<FormValues>();

  const [selectedTemplateId, setSelectedTemplateId] = useState<
    string | undefined
  >();

  // Fetch templates
  const { data: templatesData, isLoading: isLoadingTemplates } =
    useGetAssessmentTemplatesQuery({ page: 1, size: 100 });

  const [createAssessment] = useCreatePrivacyAssessmentMutation();

  const activeTemplates = useMemo(
    () => (templatesData?.items ?? []).filter((t) => t.is_active !== false),
    [templatesData?.items],
  );

  // Find selected template for description display
  const selectedTemplate = useMemo(
    () =>
      activeTemplates.find(
        (t) =>
          t.assessment_type === selectedTemplateId ||
          t.key === selectedTemplateId,
      ),
    [activeTemplates, selectedTemplateId],
  );

  const handleTemplateChange = (value: string) => {
    setSelectedTemplateId(value);
  };

  const handleSubmit = (values: FormValues) => {
    // 1. Show in-progress notification
    notificationApi.info({
      key: EVALUATION_NOTIFICATION_KEY,
      message: "Evaluation in progress",
      description:
        "Your assessment is being evaluated. This may take a moment.",
      duration: 0, // Don't auto-close
    });

    // 2. Redirect immediately
    router.push(PRIVACY_ASSESSMENTS_ROUTE);

    // 3. Fire mutation (no await) with callbacks
    createAssessment({
      assessment_type: values.assessment_type,
      system_fides_key: values.system_fides_key || undefined,
      use_llm: values.use_llm,
    })
      .unwrap()
      .then((result) => {
        notificationApi.success({
          key: EVALUATION_NOTIFICATION_KEY,
          message: "Evaluation complete",
          description: `Successfully evaluated ${result.total_created} system(s).`,
        });
      })
      .catch((error) => {
        const errorMessage = getErrorMessage(
          (error as RTKErrorResult["error"]) ?? "An unexpected error occurred.",
        );
        notificationApi.error({
          key: EVALUATION_NOTIFICATION_KEY,
          message: "Evaluation failed",
          description: errorMessage,
        });
      });
  };

  const handleCancel = () => {
    router.push(PRIVACY_ASSESSMENTS_ROUTE);
  };

  return (
    <Layout title="Evaluate assessments">
      <PageHeader
        heading="Evaluate assessments"
        breadcrumbItems={[
          { title: "Privacy assessments", href: PRIVACY_ASSESSMENTS_ROUTE },
          { title: "Evaluate" },
        ]}
        isSticky
      />

      <div className="py-6">
        <div className="max-w-3xl">
          <Space direction="vertical" size="large" className="w-full">
            <div>
              <Title level={4}>Evaluation details</Title>
              <Paragraph type="secondary">
                Select an assessment template and optionally scope to a specific
                system. Assessments will be created or re-evaluated for the
                selected scope.
              </Paragraph>
            </div>

            <Form
              form={form}
              layout="vertical"
              onFinish={handleSubmit}
              initialValues={{
                use_llm: true,
              }}
            >
              <Item
                name="assessment_type"
                label="Assessment template"
                rules={[
                  {
                    required: true,
                    message: "Please select an assessment template",
                  },
                ]}
                tooltip="Choose the type of privacy assessment based on your regulatory requirements"
              >
                <Select
                  placeholder="Select a template"
                  loading={isLoadingTemplates}
                  onChange={handleTemplateChange}
                  showSearch
                  optionFilterProp="label"
                  aria-label="Assessment template"
                  options={activeTemplates.map((template) => ({
                    value: template.assessment_type || template.key,
                    label: template.name,
                    template,
                  }))}
                  optionRender={renderTemplateOption}
                />
              </Item>

              {selectedTemplate && (
                <Card type="inner" className="mb-6">
                  <Descriptions column={1} size="small">
                    {selectedTemplate.description && (
                      <Descriptions.Item label="Description">
                        {selectedTemplate.description}
                      </Descriptions.Item>
                    )}
                    {selectedTemplate.authority && (
                      <Descriptions.Item label="Authority">
                        {selectedTemplate.authority}
                      </Descriptions.Item>
                    )}
                    {selectedTemplate.legal_reference && (
                      <Descriptions.Item label="Legal reference">
                        {selectedTemplate.legal_reference}
                      </Descriptions.Item>
                    )}
                  </Descriptions>
                </Card>
              )}

              <Item
                name="system_fides_key"
                label="System"
                tooltip="Optionally scope this assessment to a specific system. Leave blank to evaluate all systems."
              >
                <SystemSelect placeholder="All systems" allowClear />
              </Item>

              <Item
                name="use_llm"
                label="AI-assisted answers"
                valuePropName="checked"
                tooltip="Enable AI to automatically generate initial answers based on your system configuration"
              >
                <Switch />
              </Item>

              <Item className="mb-0">
                <Flex gap="middle" justify="flex-end">
                  <Button onClick={handleCancel}>Cancel</Button>
                  <Button type="primary" htmlType="submit">
                    Run evaluation
                  </Button>
                </Flex>
              </Item>
            </Form>
          </Space>
        </div>
      </div>
    </Layout>
  );
};

export default EvaluateAssessmentPage;
