import {
  Button,
  Collapse,
  Descriptions,
  Flex,
  Form,
  Modal,
  Select,
  Space,
  Switch,
  Text,
  useMessage,
} from "fidesui";
import { useMemo, useState } from "react";

import { SystemSelect } from "~/features/common/dropdown/SystemSelect";
import { getErrorMessage } from "~/features/common/helpers";
import { RTKErrorResult } from "~/types/errors/api";

import {
  useCreatePrivacyAssessmentMutation,
  useGetAssessmentTemplatesQuery,
} from "./privacy-assessments.slice";
import { TemplateResponse } from "./types";

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
    <Flex align="center">
      <Text strong>{template.name}</Text>
      {template.region && (
        <Text type="secondary" className="ml-2" size="sm">
          {template.region}
        </Text>
      )}
    </Flex>
};

interface GenerateAssessmentsModalProps {
  open: boolean;
  onClose: () => void;
}

export const GenerateAssessmentsModal = ({
  open,
  onClose,
}: GenerateAssessmentsModalProps) => {
  const message = useMessage();
  const [form] = Form.useForm<FormValues>();
  const [selectedTemplateIds, setSelectedTemplateIds] = useState<string[]>([]);

  const { data: templatesData, isLoading: isLoadingTemplates } =
    useGetAssessmentTemplatesQuery({ page: 1, size: 100 });

  const [createAssessment, { isLoading: isCreating }] =
    useCreatePrivacyAssessmentMutation();

  const activeTemplates = useMemo(
    () => (templatesData?.items ?? []).filter((t) => t.is_active !== false),
    [templatesData?.items],
  );

  const selectedTemplates = useMemo(
    () =>
      activeTemplates.filter((t) =>
        selectedTemplateIds.includes(t.assessment_type || t.key),
      ),
    [activeTemplates, selectedTemplateIds],
  );

  const handleCancel = () => {
    form.resetFields();
    setSelectedTemplateIds([]);
    onClose();
  };

  const handleSubmit = async (values: FormValues) => {
    try {
      await createAssessment({
        assessment_types: values.assessment_types,
        system_fides_keys: values.system_fides_keys?.length
          ? values.system_fides_keys
          : null,
        use_llm: values.use_llm,
      }).unwrap();

      message.success(
        "Assessment evaluation queued. Results will appear on the assessments page shortly.",
      );

      form.resetFields();
      setSelectedTemplateIds([]);
      onClose();
    } catch (error) {
      message.error(
        `Failed to queue assessment: ${getErrorMessage(error as RTKErrorResult["error"])}`,
      );
    }
  };

  return (
    <Modal
      title="Generate assessments"
      open={open}
      onCancel={handleCancel}
      footer={null}
      width={600}
    >
      <Space direction="vertical" size="large" className="w-full pt-2">
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{ use_llm: true }}
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
          >
            <Select
              mode="multiple"
              placeholder="Select one or more templates"
              loading={isLoadingTemplates}
              onChange={(values: string[]) => setSelectedTemplateIds(values)}
              showSearch
              optionFilterProp="label"
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

          <Item name="system_fides_keys" label="Systems">
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
          >
            <Switch />
          </Item>

          <Item className="mb-0">
            <Flex gap="middle" justify="flex-end">
              <Button onClick={handleCancel}>Cancel</Button>
              <Button type="primary" htmlType="submit" loading={isCreating}>
                Generate assessments
              </Button>
            </Flex>
          </Item>
        </Form>
      </Space>
    </Modal>
  );
};
