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
import useTaxonomies from "~/features/common/hooks/useTaxonomies";
import { DATA_PURPOSES_ROUTE } from "~/features/common/nav/routes";
import { formatKey } from "~/features/datastore-connections/system_portal_config/helpers";
import useLegalBasisOptions from "~/features/system/system-form-declaration-tab/useLegalBasisOptions";
import useSpecialCategoryLegalBasisOptions from "~/features/system/system-form-declaration-tab/useSpecialCategoryLegalBasisOptions";
import { LegalBasisForProcessingEnum } from "~/types/api";

import {
  type DataPurpose,
  useCreateDataPurposeMutation,
  useUpdateDataPurposeMutation,
} from "./data-purpose.slice";
import { FEATURE_LABELS } from "./purposeUtils";

interface PurposeConfigFormProps {
  purpose?: DataPurpose | null;
  isNew?: boolean;
  onSave?: () => void;
}

interface SectionProps {
  title: string;
  description?: string;
  children: React.ReactNode;
}

const Section = ({ title, description, children }: SectionProps) => (
  <Card size="small">
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

const FEATURE_OPTIONS = Object.entries(FEATURE_LABELS).map(
  ([value, label]) => ({
    value,
    label,
  }),
);

const PurposeConfigForm = ({
  purpose,
  isNew = false,
  onSave,
}: PurposeConfigFormProps) => {
  const router = useRouter();
  const [form] = Form.useForm<Partial<DataPurpose>>();
  const message = useMessage();
  const [createDataPurpose, { isLoading: isCreating }] =
    useCreateDataPurposeMutation();
  const [updateDataPurpose, { isLoading: isUpdating }] =
    useUpdateDataPurposeMutation();

  const { getDataUses, getDataCategories, getDataSubjects } = useTaxonomies();
  const { legalBasisOptions } = useLegalBasisOptions();
  const { specialCategoryLegalBasisOptions } =
    useSpecialCategoryLegalBasisOptions();

  const legalBasis = Form.useWatch("legal_basis_for_processing", form);

  const dataUseOptions = useMemo(
    () =>
      getDataUses().map((du) => ({
        value: du.fides_key,
        label: du.fides_key,
      })),
    [getDataUses],
  );

  const dataCategoryOptions = useMemo(
    () =>
      getDataCategories().map((dc) => ({
        value: dc.fides_key,
        label: dc.fides_key,
      })),
    [getDataCategories],
  );

  const dataSubjectOptions = useMemo(
    () =>
      getDataSubjects().map((ds) => ({
        value: ds.fides_key,
        label: ds.fides_key,
      })),
    [getDataSubjects],
  );

  useEffect(() => {
    if (purpose) {
      form.setFieldsValue(purpose);
    }
  }, [purpose, form]);

  const handleNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (isNew) {
      form.setFieldValue("fides_key", formatKey(e.target.value));
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
      data-testid="data-purpose-form"
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
              <Input
                placeholder="Purpose name"
                onChange={handleNameChange}
                data-testid="data-purpose-name-input"
              />
            </Form.Item>
            <Form.Item
              label={<Text strong>Key</Text>}
              name="fides_key"
              rules={[{ required: true, message: "Key is required" }]}
              tooltip="Auto-generated from the name."
              className="!mb-0 flex-1"
            >
              <Input
                placeholder="purpose_key"
                disabled={!isNew}
                data-testid="data-purpose-key-input"
              />
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
              data-testid="data-purpose-description-input"
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
                data-testid="data-purpose-data-use-select"
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
                data-testid="data-purpose-data-subject-select"
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
              data-testid="data-purpose-categories-select"
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
                options={legalBasisOptions}
                placeholder="Select legal basis"
                allowClear
                data-testid="data-purpose-legal-basis-select"
              />
            </Form.Item>
            <Form.Item
              label={<Text strong>Flexible basis</Text>}
              name="flexible_legal_basis_for_processing"
              valuePropName="checked"
              tooltip="Whether this legal basis can be overridden per-system."
              className="!mb-0"
            >
              <Switch data-testid="data-purpose-flexible-basis-switch" />
            </Form.Item>
          </Flex>
          {legalBasis === LegalBasisForProcessingEnum.LEGITIMATE_INTERESTS && (
            <Form.Item
              label={<Text strong>Impact assessment location</Text>}
              name="impact_assessment_location"
              tooltip="Where is the legitimate interest impact assessment stored?"
              className="!mb-0"
            >
              <Input
                placeholder="Enter assessment location"
                data-testid="data-purpose-impact-assessment-input"
              />
            </Form.Item>
          )}
          <Flex gap="middle">
            <Form.Item
              label={<Text strong>Retention period</Text>}
              name="retention_period"
              className="!mb-0 flex-1"
            >
              <Input
                placeholder="e.g. 365 days"
                data-testid="data-purpose-retention-input"
              />
            </Form.Item>
            <Form.Item
              label={<Text strong>Special category basis</Text>}
              name="special_category_legal_basis"
              tooltip="Required when processing special category data (Article 9 GDPR)."
              className="!mb-0 flex-1"
            >
              <Select
                aria-label="Special category basis"
                options={specialCategoryLegalBasisOptions}
                placeholder="Select basis"
                allowClear
                data-testid="data-purpose-special-category-select"
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
              data-testid="data-purpose-features-select"
            />
          </Form.Item>
        </Section>

        <Flex justify="flex-end" gap="small">
          <Button
            type="default"
            onClick={handleCancel}
            data-testid="cancel-button"
          >
            Cancel
          </Button>
          <Button
            type="primary"
            htmlType="submit"
            loading={isCreating || isUpdating}
            data-testid="save-data-purpose-button"
          >
            Save
          </Button>
        </Flex>
      </Flex>
    </Form>
  );
};

export default PurposeConfigForm;
