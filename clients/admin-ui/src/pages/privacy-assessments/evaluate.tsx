import {
  Button,
  Collapse,
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

interface FormValues {
  assessment_types: string[];
  system_fides_keys?: string[];
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
        <Text type="secondary" className="ml-2" size="sm">
          {template.region}
        </Text>
      )}
    </div>
  );
};

const EvaluateAssessmentPage: NextPage = () => {
  const router = useRouter();
  const message = useMessage();
  const [form] = Form.useForm<FormValues>();

  const [selectedTemplateIds, setSelectedTemplateIds] = useState<string[]>([]);

  // Fetch templates
  const { data: templatesData, isLoading: isLoadingTemplates } =
    useGetAssessmentTemplatesQuery({ page: 1, size: 100 });

  const [createAssessment, { isLoading: isCreating }] =
    useCreatePrivacyAssessmentMutation();

  const activeTemplates = useMemo(
    () => (templatesData?.items ?? []).filter((t) => t.is_active !== false),
    [templatesData?.items],
  );

  // Find selected templates for description display
  const selectedTemplates = useMemo(
    () =>
      activeTemplates.filter((t) =>
        selectedTemplateIds.includes(t.assessment_type || t.key),
      ),
    [activeTemplates, selectedTemplateIds],
  );

  const handleTemplateChange = (values: string[]) => {
    setSelectedTemplateIds(values);
  };

  const handleSubmit = async (values: FormValues) => {
    try {
      await createAssessment({
        assessment_types: values.assessment_types,
        system_fides_keys:
          values.system_fides_keys && values.system_fides_keys.length > 0
            ? values.system_fides_keys
            : null,
        use_llm: values.use_llm,
      }).unwrap();

      message.success(
        "Assessment evaluation queued. Results will appear on the assessments page shortly.",
      );

      router.push(PRIVACY_ASSESSMENTS_ROUTE);
    } catch (error) {
      message.error(
        `Failed to queue assessment: ${getErrorMessage(error as RTKErrorResult["error"])}`,
      );
    }
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
                name="assessment_types"
                label="Assessment templates"
                rules={[
                  {
                    required: true,
                    message: "Please select at least one assessment template",
                  },
                ]}
                tooltip="Choose one or more privacy assessment types based on your regulatory requirements"
              >
                <Select
                  mode="multiple"
                  placeholder="Select one or more templates"
                  loading={isLoadingTemplates}
                  onChange={handleTemplateChange}
                  showSearch
                  optionFilterProp="label"
                  aria-label="Assessment templates"
                  options={activeTemplates.map((template) => ({
                    value: template.assessment_type || template.key,
                    label: template.name,
                    template,
                  }))}
                  optionRender={renderTemplateOption}
                />
              </Item>

              {selectedTemplates.length > 0 && (
                <Collapse
                  className="mb-6"
                  items={selectedTemplates.map((template) => ({
                    key: template.key,
                    label: (
                      <Flex align="center" gap="small">
                        <Text strong>{template.name}</Text>
                        {template.region && (
                          <Text type="secondary" size="sm">
                            {template.region}
                          </Text>
                        )}
                      </Flex>
                    ),
                    children: (
                      <Descriptions column={1} size="small">
                        {template.description && (
                          <Descriptions.Item label="Description">
                            {template.description}
                          </Descriptions.Item>
                        )}
                        {template.authority && (
                          <Descriptions.Item label="Authority">
                            {template.authority}
                          </Descriptions.Item>
                        )}
                        {template.legal_reference && (
                          <Descriptions.Item label="Legal reference">
                            {template.legal_reference}
                          </Descriptions.Item>
                        )}
                      </Descriptions>
                    ),
                  }))}
                />
              )}

              <Item
                name="system_fides_keys"
                label="Systems"
                tooltip="Optionally scope this assessment to specific systems. Leave blank to evaluate all systems."
              >
                <SystemSelect
                  mode="multiple"
                  placeholder="All systems"
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
                  <Button type="primary" htmlType="submit" loading={isCreating}>
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
