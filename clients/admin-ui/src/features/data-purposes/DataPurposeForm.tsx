import { Button, Flex, Form, Input, Select, Switch } from "fidesui";
import { useRouter } from "next/router";
import { useCallback, useMemo } from "react";

import useTaxonomies from "~/features/common/hooks/useTaxonomies";
import { DATA_PURPOSES_ROUTE } from "~/features/common/nav/routes";
import { formatKey } from "~/features/datastore-connections/system_portal_config/helpers";
import useLegalBasisOptions from "~/features/system/system-form-declaration-tab/useLegalBasisOptions";
import useSpecialCategoryLegalBasisOptions from "~/features/system/system-form-declaration-tab/useSpecialCategoryLegalBasisOptions";

import { DataPurpose } from "./data-purpose.slice";

export interface DataPurposeFormValues {
  name: string;
  fides_key: string;
  description: string;
  data_use: string;
  data_subject: string;
  data_categories: string[];
  legal_basis_for_processing: string;
  flexible_legal_basis_for_processing: boolean;
  impact_assessment_location: string;
  retention_period: string;
  special_category_legal_basis: string;
  features: string[];
}

interface DataPurposeFormProps {
  purpose?: DataPurpose;
  handleSubmit: (values: DataPurposeFormValues) => Promise<void>;
}

const DataPurposeForm = ({ purpose, handleSubmit }: DataPurposeFormProps) => {
  const [form] = Form.useForm<DataPurposeFormValues>();
  const router = useRouter();
  const isEditing = !!purpose;

  const { getDataUses, getDataCategories, getDataSubjects } = useTaxonomies();
  const { legalBasisOptions } = useLegalBasisOptions();
  const { specialCategoryLegalBasisOptions } =
    useSpecialCategoryLegalBasisOptions();

  const legalBasis = Form.useWatch("legal_basis_for_processing", form);

  const dataUseOptions = useMemo(
    () =>
      getDataUses().map((use) => ({
        value: use.fides_key,
        label: use.fides_key,
      })),
    [getDataUses],
  );

  const dataCategoryOptions = useMemo(
    () =>
      getDataCategories().map((cat) => ({
        value: cat.fides_key,
        label: cat.fides_key,
      })),
    [getDataCategories],
  );

  const dataSubjectOptions = useMemo(
    () =>
      getDataSubjects().map((sub) => ({
        value: sub.fides_key,
        label: sub.fides_key,
      })),
    [getDataSubjects],
  );

  const initialValues = useMemo<DataPurposeFormValues>(
    () => ({
      name: purpose?.name ?? "",
      fides_key: purpose?.fides_key ?? "",
      description: purpose?.description ?? "",
      data_use: purpose?.data_use ?? "",
      data_subject: purpose?.data_subject ?? "",
      data_categories: purpose?.data_categories ?? [],
      legal_basis_for_processing: purpose?.legal_basis_for_processing ?? "",
      flexible_legal_basis_for_processing:
        purpose?.flexible_legal_basis_for_processing ?? true,
      impact_assessment_location: purpose?.impact_assessment_location ?? "",
      retention_period: purpose?.retention_period ?? "",
      special_category_legal_basis: purpose?.special_category_legal_basis ?? "",
      features: purpose?.features ?? [],
    }),
    [purpose],
  );

  const handleCancel = useCallback(() => {
    router.push(DATA_PURPOSES_ROUTE);
  }, [router]);

  const handleNameChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (!isEditing) {
        form.setFieldValue("fides_key", formatKey(e.target.value));
      }
    },
    [form, isEditing],
  );

  return (
    <Form
      form={form}
      layout="vertical"
      onFinish={handleSubmit}
      initialValues={initialValues}
      key={purpose?.fides_key ?? "create"}
      data-testid="data-purpose-form"
      style={{ maxWidth: 720 }}
    >
      <Form.Item
        name="name"
        label="Name"
        rules={[{ required: true, message: "Name is required" }]}
      >
        <Input
          placeholder="Enter a name for this data purpose"
          onChange={handleNameChange}
          data-testid="data-purpose-name-input"
        />
      </Form.Item>

      <Form.Item
        name="fides_key"
        label="Key"
        rules={[
          { required: true, message: "Key is required" },
          {
            pattern: /^[a-z0-9_.]+$/,
            message:
              "Key must contain only lowercase letters, numbers, underscores, and dots",
          },
        ]}
        tooltip="Unique identifier for this data purpose. Auto-generated from name."
      >
        <Input
          placeholder="Auto-generated from name"
          disabled={isEditing}
          data-testid="data-purpose-key-input"
        />
      </Form.Item>

      <Form.Item
        name="data_use"
        label="Data use"
        rules={[{ required: true, message: "Data use is required" }]}
        tooltip="For which business purpose is data processed?"
      >
        <Select
          placeholder="Select a data use"
          options={dataUseOptions}
          showSearch
          aria-label="Data use"
          data-testid="data-purpose-data-use-select"
        />
      </Form.Item>

      <Form.Item
        name="data_categories"
        label="Data categories"
        tooltip="Which categories of personal data are collected for this purpose?"
      >
        <Select
          mode="multiple"
          placeholder="Select data categories"
          options={dataCategoryOptions}
          showSearch
          aria-label="Data categories"
          data-testid="data-purpose-categories-select"
        />
      </Form.Item>

      <Form.Item
        name="data_subject"
        label="Data subject"
        tooltip="Who are the subjects for this personal data?"
      >
        <Select
          placeholder="Select a data subject"
          options={dataSubjectOptions}
          showSearch
          allowClear
          aria-label="Data subject"
          data-testid="data-purpose-data-subject-select"
        />
      </Form.Item>

      <Form.Item
        name="description"
        label="Description"
        tooltip="An optional description of this data purpose"
      >
        <Input.TextArea
          placeholder="Enter a description"
          rows={3}
          data-testid="data-purpose-description-input"
        />
      </Form.Item>

      <Form.Item
        name="legal_basis_for_processing"
        label="Legal basis for processing"
        tooltip="What is the legal basis under which personal data is processed for this purpose?"
      >
        <Select
          placeholder="Select a legal basis"
          options={legalBasisOptions}
          allowClear
          aria-label="Legal basis for processing"
          data-testid="data-purpose-legal-basis-select"
        />
      </Form.Item>

      {legalBasis === "Legitimate interests" && (
        <Form.Item
          name="impact_assessment_location"
          label="Impact assessment location"
          tooltip="Where is the legitimate interest impact assessment stored?"
        >
          <Input
            placeholder="Enter assessment location"
            data-testid="data-purpose-impact-assessment-input"
          />
        </Form.Item>
      )}

      <Form.Item
        name="flexible_legal_basis_for_processing"
        label="This legal basis is flexible"
        tooltip="Has the vendor declared that the legal basis may be overridden?"
        valuePropName="checked"
      >
        <Switch data-testid="data-purpose-flexible-basis-switch" />
      </Form.Item>

      <Form.Item
        name="retention_period"
        label="Retention period (days)"
        tooltip="How long is personal data retained for this purpose?"
      >
        <Input
          placeholder="Enter retention period"
          data-testid="data-purpose-retention-input"
        />
      </Form.Item>

      <Form.Item
        name="special_category_legal_basis"
        label="Special category legal basis"
        tooltip="What is the legal basis for processing special category data (GDPR Article 9)?"
      >
        <Select
          placeholder="Select a special category legal basis"
          options={specialCategoryLegalBasisOptions}
          allowClear
          aria-label="Special category legal basis"
          data-testid="data-purpose-special-category-select"
        />
      </Form.Item>

      <Form.Item
        name="features"
        label="Features"
        tooltip="What are some features of how data is processed?"
      >
        <Select
          mode="tags"
          placeholder="Describe features"
          aria-label="Features"
          data-testid="data-purpose-features-select"
        />
      </Form.Item>

      <Flex justify="space-between" className="pt-4">
        <Button onClick={handleCancel} data-testid="cancel-button">
          Cancel
        </Button>
        <Button
          type="primary"
          htmlType="submit"
          data-testid="save-data-purpose-button"
        >
          Save
        </Button>
      </Flex>
    </Form>
  );
};

export default DataPurposeForm;
