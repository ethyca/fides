import {
  Alert,
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
  useMessage,
} from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import { useMemo, useState } from "react";

import { SystemSelect } from "~/features/common/dropdown/SystemSelect";
import { useFeatures } from "~/features/common/features";
import Layout from "~/features/common/Layout";
import { PRIVACY_ASSESSMENTS_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import {
  useCreatePrivacyAssessmentMutation,
  useGetAssessmentTemplatesQuery,
} from "~/features/privacy-assessments";

const { Title, Paragraph } = Typography;
const { Item } = Form;

interface FormValues {
  assessment_type: string;
  system_fides_key?: string;
  use_llm: boolean;
}

const renderTemplateOption = (option: any) => {
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

const NewAssessmentPage: NextPage = () => {
  const { flags } = useFeatures();
  const router = useRouter();
  const message = useMessage();
  const [form] = Form.useForm<FormValues>();

  const [selectedTemplateId, setSelectedTemplateId] = useState<
    string | undefined
  >();

  // Fetch templates
  const { data: templatesData, isLoading: isLoadingTemplates } =
    useGetAssessmentTemplatesQuery();

  const [createAssessment, { isLoading: isCreating }] =
    useCreatePrivacyAssessmentMutation();

  const templates = templatesData?.items ?? [];
  const activeTemplates = templates.filter((t) => t.is_active !== false);

  // Find selected template for description display
  const selectedTemplate = useMemo(
    () => activeTemplates.find((t) => t.assessment_type === selectedTemplateId),
    [activeTemplates, selectedTemplateId],
  );

  const handleTemplateChange = (value: string) => {
    setSelectedTemplateId(value);
  };

  const handleSubmit = async (values: FormValues) => {
    try {
      const result = await createAssessment({
        assessment_type: values.assessment_type,
        system_fides_key: values.system_fides_key || undefined,
        use_llm: values.use_llm,
      }).unwrap();

      message.success(
        `Successfully created ${result.total_created} assessment(s)`,
      );

      // Navigate to assessments list
      router.push(PRIVACY_ASSESSMENTS_ROUTE);
    } catch (error) {
      message.error(
        `Failed to create assessment: ${error instanceof Error ? error.message : "Unknown error"}`,
      );
    }
  };

  const handleCancel = () => {
    router.push(PRIVACY_ASSESSMENTS_ROUTE);
  };

  if (!flags?.alphaDataProtectionAssessments) {
    return (
      <Layout title="New Privacy Assessment">
        <Alert
          type="error"
          message="Feature not available"
          description="This feature is currently behind a feature flag and is not enabled."
        />
      </Layout>
    );
  }

  return (
    <Layout title="New Privacy Assessment">
      <PageHeader
        heading="Create privacy assessment"
        breadcrumbItems={[
          { title: "Privacy assessments", href: PRIVACY_ASSESSMENTS_ROUTE },
          { title: "New assessment" },
        ]}
        isSticky
      />

      <div className="px-10 py-6">
        <div className="mx-auto max-w-3xl">
          <Card>
            <Space direction="vertical" size="large" className="w-full">
              <div>
                <Title level={4}>Assessment details</Title>
                <Paragraph type="secondary">
                  Select the assessment template and system to analyze. You can
                  optionally enable AI-assisted answer generation.
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
                  tooltip="Optionally scope this assessment to a specific system. Leave blank to generate assessments for all systems."
                >
                  <SystemSelect
                    placeholder="Select a system (optional)"
                    allowClear
                  />
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
                    <Button
                      type="primary"
                      htmlType="submit"
                      loading={isCreating}
                    >
                      Create assessment
                    </Button>
                  </Flex>
                </Item>
              </Form>
            </Space>
          </Card>
        </div>
      </div>
    </Layout>
  );
};

export default NewAssessmentPage;
