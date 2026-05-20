/**
 * antd-based privacy declaration form for the system configure / add-system flow.
 *
 * Composes the shared per-field components in `~/features/system/privacy-declaration-fields/`
 * with the modal-only fields (legal basis + impact assessment, special category, third parties,
 * features, retention period). Validation lives on each Form.Item's `rules` array — no Yup.
 */

import { Button, Card, Flex, Form, Input, Select, Spin, Switch } from "fidesui";
import { useMemo } from "react";

import { useAppSelector } from "~/app/hooks";
import {
  CustomFieldValues,
  useCustomFields,
} from "~/features/common/custom-fields";
import { LegacyResourceTypes } from "~/features/common/custom-fields/types";
import { selectLockedForGVL } from "~/features/system/dictionary-form/dict-suggestion.slice";
import {
  DataCategoriesFormItem,
  DatasetReferencesFormItem,
  DataSubjectsFormItem,
  DataUseFormItem,
  DeclarationNameFormItem,
  PrivacyDeclarationCustomFields,
} from "~/features/system/privacy-declaration-fields";
import {
  DataCategory,
  Dataset,
  DataSubject,
  DataUse,
  PrivacyDeclarationResponse,
} from "~/types/api";

import useLegalBasisOptions from "./useLegalBasisOptions";
import useSpecialCategoryLegalBasisOptions from "./useSpecialCategoryLegalBasisOptions";

const LEGITIMATE_INTERESTS = "Legitimate interests";

export type FormValues = Omit<PrivacyDeclarationResponse, "cookies"> & {
  customFieldValues: CustomFieldValues;
};

const defaultInitialValues: FormValues = {
  name: "",
  data_categories: [],
  data_use: "",
  data_subjects: [],
  egress: undefined,
  ingress: undefined,
  features: [],
  legal_basis_for_processing: undefined,
  flexible_legal_basis_for_processing: true,
  impact_assessment_location: "",
  retention_period: "",
  processes_special_category_data: false,
  special_category_legal_basis: undefined,
  data_shared_with_third_parties: false,
  third_parties: "",
  shared_categories: [],
  customFieldValues: {},
  id: "",
};

const transformFormValueToDeclaration = (
  values: FormValues,
): PrivacyDeclarationResponse => {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const { customFieldValues, ...rest } = values;
  return {
    ...rest,
    // fill in an empty string for name: https://github.com/ethyca/fideslang/issues/98
    name: values.name ?? "",
    special_category_legal_basis: values.processes_special_category_data
      ? values.special_category_legal_basis
      : undefined,
    third_parties: values.data_shared_with_third_parties
      ? values.third_parties
      : undefined,
    shared_categories: values.data_shared_with_third_parties
      ? values.shared_categories
      : undefined,
  };
};

export const transformPrivacyDeclarationToFormValues = (
  privacyDeclaration?: PrivacyDeclarationResponse,
  customFieldValues?: CustomFieldValues,
): FormValues =>
  privacyDeclaration
    ? {
        ...privacyDeclaration,
        customFieldValues: customFieldValues ?? {},
      }
    : defaultInitialValues;

export interface DataProps {
  allDataCategories: DataCategory[];
  allDataUses: DataUse[];
  allDataSubjects: DataSubject[];
  allDatasets?: Dataset[];
  includeCustomFields?: boolean;
}

interface Props {
  onSubmit: (
    values: PrivacyDeclarationResponse,
  ) => Promise<PrivacyDeclarationResponse[] | undefined>;
  onCancel: () => void;
  initialValues?: PrivacyDeclarationResponse;
  /** Fires whenever the form transitions to a dirty state. */
  onDirtyChange?: (dirty: boolean) => void;
}

export const PrivacyDeclarationForm = ({
  onSubmit,
  onCancel,
  initialValues: passedInInitialValues,
  onDirtyChange,
  allDataUses,
  allDataCategories,
  allDataSubjects,
  allDatasets,
  includeCustomFields,
}: Props & DataProps) => {
  const privacyDeclarationId = passedInInitialValues?.id;
  const isEditing = !!privacyDeclarationId;
  const lockedForGVL = useAppSelector(selectLockedForGVL);

  const { legalBasisOptions } = useLegalBasisOptions();
  const { specialCategoryLegalBasisOptions } =
    useSpecialCategoryLegalBasisOptions();

  const { customFieldValues, upsertCustomFields, isLoading } = useCustomFields({
    resourceType: LegacyResourceTypes.PRIVACY_DECLARATION,
    resourceFidesKey: privacyDeclarationId,
  });

  const initialValues = useMemo(
    () =>
      transformPrivacyDeclarationToFormValues(
        passedInInitialValues,
        customFieldValues,
      ),
    [passedInInitialValues, customFieldValues],
  );

  const [form] = Form.useForm<FormValues>();

  const handleFinish = async (values: FormValues) => {
    // antd Form only tracks fields with a Form.Item; untracked fields
    // (`id`, `egress`, `ingress`) are silently dropped from `values`. Merge
    // them back in from initialValues so updates aren't mistaken for creates.
    const declaration = transformFormValueToDeclaration({
      ...initialValues,
      ...values,
    });
    const success = await onSubmit(declaration);
    if (success) {
      const matched = success.find(
        (pd) =>
          pd.data_use === values.data_use &&
          (pd.name ? pd.name === values.name : true),
      );
      if (matched?.id) {
        await upsertCustomFields({
          customFieldValues: values.customFieldValues,
          fides_key: matched.id,
        });
      }
    }
  };

  if (isEditing && isLoading) {
    return (
      <Flex justify="center" align="center" className="py-8">
        <Spin />
      </Flex>
    );
  }

  return (
    <Form
      form={form}
      layout="vertical"
      key={privacyDeclarationId ?? "new"}
      initialValues={initialValues}
      onFinish={handleFinish}
      onValuesChange={() => onDirtyChange?.(true)}
      data-testid="declaration-form"
    >
      <Flex vertical gap="middle">
        <Card size="small" title="Data use declaration">
          <DeclarationNameFormItem
            disabled={isEditing}
            label="Declaration name (optional)"
            tooltip="Would you like to append anything to the system name?"
          />
          <DataUseFormItem
            allDataUses={allDataUses}
            disabled={isEditing}
            tooltip="For which business purposes is this data processed?"
          />
          <DataCategoriesFormItem
            allDataCategories={allDataCategories}
            disabled={lockedForGVL}
            required
            tooltip="Which categories of personal data are collected for this purpose?"
          />
          <DataSubjectsFormItem
            allDataSubjects={allDataSubjects}
            tooltip="Who are the subjects for this personal data?"
          />
          <Form.Item
            name="legal_basis_for_processing"
            label="Legal basis for processing"
            tooltip="What is the legal basis under which personal data is processed for this purpose?"
          >
            <Select
              aria-label="Legal basis for processing"
              data-testid="input-legal_basis_for_processing"
              options={legalBasisOptions}
              disabled={lockedForGVL}
              allowClear
            />
          </Form.Item>
          <Form.Item
            noStyle
            shouldUpdate={(prev, curr) =>
              prev.legal_basis_for_processing !==
              curr.legal_basis_for_processing
            }
          >
            {({ getFieldValue }) =>
              getFieldValue("legal_basis_for_processing") ===
              LEGITIMATE_INTERESTS ? (
                <Form.Item
                  name="impact_assessment_location"
                  label="Impact assessment location"
                  tooltip="Where is the legitimate interest impact assessment stored?"
                >
                  <Input
                    aria-label="Impact assessment location"
                    data-testid="input-impact_assessment_location"
                  />
                </Form.Item>
              ) : null
            }
          </Form.Item>
          <Form.Item
            name="flexible_legal_basis_for_processing"
            label="This legal basis is flexible"
            tooltip="Has the vendor declared that the legal basis may be overridden?"
            valuePropName="checked"
          >
            <Switch
              disabled={lockedForGVL}
              data-testid="input-flexible_legal_basis_for_processing"
            />
          </Form.Item>
          <Form.Item
            name="retention_period"
            label="Retention period (days)"
            tooltip="How long is personal data retained for this purpose?"
            className="mb-0"
          >
            <Input
              aria-label="Retention period"
              data-testid="input-retention_period"
              disabled={lockedForGVL}
            />
          </Form.Item>
        </Card>

        <Card size="small" title="Features">
          <Form.Item
            name="features"
            label="Features"
            tooltip="What are some features of how data is processed?"
            className="mb-0"
          >
            <Select
              aria-label="Features"
              data-testid="input-features"
              mode="tags"
              placeholder="Describe features..."
              disabled={lockedForGVL}
            />
          </Form.Item>
        </Card>

        <Card size="small" title="Dataset reference">
          <DatasetReferencesFormItem
            allDatasets={allDatasets ?? []}
            tooltip="Is there a dataset configured for this system?"
          />
        </Card>

        <Card size="small" title="Special category data">
          <Form.Item
            name="processes_special_category_data"
            label="This system processes special category data"
            tooltip="Is this system processing special category data as defined by GDPR Article 9?"
            valuePropName="checked"
            className="mb-0"
          >
            <Switch data-testid="input-processes_special_category_data" />
          </Form.Item>
          <Form.Item
            noStyle
            shouldUpdate={(prev, curr) =>
              prev.processes_special_category_data !==
              curr.processes_special_category_data
            }
          >
            {({ getFieldValue }) =>
              getFieldValue("processes_special_category_data") ? (
                <Form.Item
                  name="special_category_legal_basis"
                  label="Legal basis for processing"
                  tooltip="What is the legal basis under which the special category data is processed?"
                  className="mb-0 mt-4"
                  rules={[
                    {
                      required: true,
                      message: "Legal basis for processing is required",
                    },
                  ]}
                >
                  <Select
                    aria-label="Special category legal basis"
                    data-testid="input-special_category_legal_basis"
                    options={specialCategoryLegalBasisOptions}
                    allowClear
                  />
                </Form.Item>
              ) : null
            }
          </Form.Item>
        </Card>

        <Card size="small" title="Third parties">
          <Form.Item
            name="data_shared_with_third_parties"
            label="This system shares data with 3rd parties for this purpose"
            tooltip="Does this system disclose, sell, or share personal data collected for this business use with 3rd parties?"
            valuePropName="checked"
            className="mb-0"
          >
            <Switch data-testid="input-data_shared_with_third_parties" />
          </Form.Item>
          <Form.Item
            noStyle
            shouldUpdate={(prev, curr) =>
              prev.data_shared_with_third_parties !==
              curr.data_shared_with_third_parties
            }
          >
            {({ getFieldValue }) =>
              getFieldValue("data_shared_with_third_parties") ? (
                <Flex vertical gap="middle" className="mt-4">
                  <Form.Item
                    name="third_parties"
                    label="Third parties"
                    tooltip="Which type of third parties is the data shared with?"
                    className="mb-0"
                  >
                    <Input
                      aria-label="Third parties"
                      data-testid="input-third_parties"
                    />
                  </Form.Item>
                  <Form.Item
                    name="shared_categories"
                    label="Shared categories"
                    tooltip="Which categories of personal data does this system share with third parties?"
                    className="mb-0"
                  >
                    <Select
                      aria-label="Shared categories"
                      data-testid="input-shared_categories"
                      mode="multiple"
                      options={allDataCategories.map((c) => ({
                        value: c.fides_key,
                        label: c.fides_key,
                      }))}
                    />
                  </Form.Item>
                </Flex>
              ) : null
            }
          </Form.Item>
        </Card>

        {includeCustomFields ? (
          <PrivacyDeclarationCustomFields
            privacyDeclarationId={privacyDeclarationId}
          />
        ) : null}

        <Flex justify="end" align="center" gap="small">
          <Button onClick={onCancel} data-testid="cancel-btn">
            Cancel
          </Button>
          <Form.Item shouldUpdate noStyle>
            {() => (
              <Button
                type="primary"
                htmlType="submit"
                data-testid="save-btn"
                disabled={
                  !form.isFieldsTouched() ||
                  form.getFieldsError().some((field) => field.errors.length > 0)
                }
              >
                Save
              </Button>
            )}
          </Form.Item>
        </Flex>
      </Flex>
    </Form>
  );
};
