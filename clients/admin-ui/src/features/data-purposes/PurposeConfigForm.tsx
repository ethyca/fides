import {
  Button,
  Card,
  Flex,
  Form,
  Input,
  Select,
  Switch,
  Text,
  Title,
  useMessage,
} from "fidesui";
import { useRouter } from "next/router";
import { useEffect, useMemo } from "react";

import { isErrorResult } from "~/features/common/helpers";
import { DATA_PURPOSES_ROUTE } from "~/features/common/nav/routes";
import { useGetAllDataSubjectsQuery } from "~/features/data-subjects/data-subject.slice";
import { useGetAllDataUsesQuery } from "~/features/data-use/data-use.slice";
import { useGetAllDataCategoriesQuery } from "~/features/taxonomy/data-category.slice";

import {
  FEATURE_OPTIONS,
  LEGAL_BASIS_OPTIONS,
  SPECIAL_CATEGORY_LEGAL_BASIS_OPTIONS,
} from "./constants";
import {
  type DataPurpose,
  useCreateDataPurposeMutation,
  useUpdateDataPurposeMutation,
} from "./data-purpose.slice";

interface PurposeConfigFormProps {
  purpose?: DataPurpose | null;
  isNew?: boolean;
  onSave?: () => void;
}

const slugify = (text: string): string =>
  text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_|_$/g, "");

interface SectionProps {
  title: string;
  description?: string;
  children: React.ReactNode;
}

const Section = ({ title, description, children }: SectionProps) => (
  <Card size="small" style={{ borderColor: "#e8e8e8" }}>
    <Flex vertical gap="middle">
      <div>
        <Title level={5} className="!mb-0">
          {title}
        </Title>
        {description && (
          <Text type="secondary" className="text-xs">
            {description}
          </Text>
        )}
      </div>
      {children}
    </Flex>
  </Card>
);

const PurposeConfigForm = ({
  purpose,
  isNew = false,
  onSave,
}: PurposeConfigFormProps) => {
  const router = useRouter();
  const [form] = Form.useForm();
  const message = useMessage();
  const [createDataPurpose, { isLoading: isCreating }] =
    useCreateDataPurposeMutation();
  const [updateDataPurpose, { isLoading: isUpdating }] =
    useUpdateDataPurposeMutation();

  const { data: dataUses } = useGetAllDataUsesQuery();
  const { data: dataCategories } = useGetAllDataCategoriesQuery();
  const { data: dataSubjects } = useGetAllDataSubjectsQuery();

  const dataUseOptions = useMemo(
    () =>
      (dataUses ?? []).map((du) => ({
        value: du.fides_key,
        label: du.fides_key,
      })),
    [dataUses],
  );

  const dataCategoryOptions = useMemo(
    () =>
      (dataCategories ?? []).map((dc) => ({
        value: dc.fides_key,
        label: dc.fides_key,
      })),
    [dataCategories],
  );

  const dataSubjectOptions = useMemo(
    () =>
      (dataSubjects ?? []).map((ds) => ({
        value: ds.fides_key,
        label: ds.fides_key,
      })),
    [dataSubjects],
  );

  useEffect(() => {
    if (purpose) {
      form.setFieldsValue(purpose);
    }
  }, [purpose, form]);

  const handleNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (isNew) {
      form.setFieldValue("fides_key", slugify(e.target.value));
    }
  };

  const handleFinish = async (values: Partial<DataPurpose>) => {
    if (isNew) {
      const result = await createDataPurpose(values);
      if (isErrorResult(result)) {
        message.error("Could not create purpose");
        return;
      }
    } else if (purpose) {
      const result = await updateDataPurpose({
        fidesKey: purpose.fides_key,
        ...values,
      });
      if (isErrorResult(result)) {
        message.error("Could not update purpose");
        return;
      }
    }
    message.success("Purpose saved");
    onSave?.();
  };

  const handleCancel = () => {
    router.push(DATA_PURPOSES_ROUTE);
  };

  return (
    <Form
      form={form}
      layout="vertical"
      onFinish={handleFinish}
      initialValues={
        purpose ?? {
          flexible_legal_basis_for_processing: false,
          data_categories: [],
          features: [],
        }
      }
      className="max-w-3xl"
    >
      <Flex vertical gap="large">
        <Section
          title="General"
          description="Basic information about this purpose."
        >
          <Flex gap="middle">
            <Form.Item
              label={<Text strong>Name</Text>}
              name="name"
              rules={[{ required: true, message: "Name is required" }]}
              className="!mb-0 flex-1"
            >
              <Input placeholder="Purpose name" onChange={handleNameChange} />
            </Form.Item>
            <Form.Item
              label={<Text strong>Key</Text>}
              name="fides_key"
              rules={[{ required: true, message: "Key is required" }]}
              tooltip="Auto-generated from the name."
              className="!mb-0 flex-1"
            >
              <Input placeholder="purpose_key" disabled={!isNew} />
            </Form.Item>
          </Flex>
          <Form.Item
            label={<Text strong>Description</Text>}
            name="description"
            className="!mb-0"
          >
            <Input.TextArea
              rows={3}
              placeholder="Describe the purpose of this data processing activity"
            />
          </Form.Item>
        </Section>

        <Section
          title="Data classification"
          description="Define what data is processed, who it belongs to, and how it's used."
        >
          <Flex gap="middle">
            <Form.Item
              label={<Text strong>Data use</Text>}
              name="data_use"
              rules={[{ required: true, message: "Data use is required" }]}
              className="!mb-0 flex-1"
            >
              <Select
                aria-label="Data use"
                options={dataUseOptions}
                placeholder="Select data use"
                showSearch
              />
            </Form.Item>
            <Form.Item
              label={<Text strong>Data subject</Text>}
              name="data_subject"
              tooltip="Whose data is being processed?"
              className="!mb-0 flex-1"
            >
              <Select
                aria-label="Data subject"
                options={dataSubjectOptions}
                placeholder="Select data subject"
                showSearch
                allowClear
              />
            </Form.Item>
          </Flex>
          <Form.Item
            label={<Text strong>Data categories</Text>}
            name="data_categories"
            tooltip="What type of data does this purpose process?"
            className="!mb-0"
          >
            <Select
              aria-label="Data categories"
              mode="multiple"
              options={dataCategoryOptions}
              placeholder="Select data categories"
              showSearch
            />
          </Form.Item>
        </Section>

        <Section
          title="Legal & compliance"
          description="Legal justification and retention requirements."
        >
          <Flex gap="middle">
            <Form.Item
              label={<Text strong>Legal basis</Text>}
              name="legal_basis_for_processing"
              tooltip="The legal justification for processing data under this purpose."
              className="!mb-0 flex-1"
            >
              <Select
                aria-label="Legal basis"
                options={LEGAL_BASIS_OPTIONS}
                placeholder="Select legal basis"
                allowClear
              />
            </Form.Item>
            <Form.Item
              label={<Text strong>Flexible basis</Text>}
              name="flexible_legal_basis_for_processing"
              valuePropName="checked"
              tooltip="Whether this legal basis can be overridden per-system."
              className="!mb-0"
            >
              <Switch />
            </Form.Item>
          </Flex>
          <Flex gap="middle">
            <Form.Item
              label={<Text strong>Retention period</Text>}
              name="retention_period"
              className="!mb-0 flex-1"
            >
              <Input placeholder="e.g. 365 days" />
            </Form.Item>
            <Form.Item
              label={<Text strong>Special category basis</Text>}
              name="special_category_legal_basis"
              tooltip="Required when processing special category data (Article 9 GDPR)."
              className="!mb-0 flex-1"
            >
              <Select
                aria-label="Special category basis"
                options={SPECIAL_CATEGORY_LEGAL_BASIS_OPTIONS}
                placeholder="Select basis"
                allowClear
              />
            </Form.Item>
          </Flex>
        </Section>

        <Section
          title="Technical"
          description="Technical capabilities and features used by this purpose."
        >
          <Form.Item
            label={<Text strong>Features</Text>}
            name="features"
            tooltip="Technical capabilities used by this purpose."
            className="!mb-0"
          >
            <Select
              aria-label="Features"
              mode="multiple"
              options={FEATURE_OPTIONS}
              placeholder="Select features"
            />
          </Form.Item>
        </Section>

        <Flex justify="flex-end" gap="small">
          <Button type="default" onClick={handleCancel}>
            Cancel
          </Button>
          <Button
            type="primary"
            htmlType="submit"
            loading={isCreating || isUpdating}
          >
            Save
          </Button>
        </Flex>
      </Flex>
    </Form>
  );
};

export default PurposeConfigForm;
