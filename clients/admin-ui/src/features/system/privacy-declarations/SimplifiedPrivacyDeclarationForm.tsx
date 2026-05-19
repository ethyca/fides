import { Form, FormInstance, Icons, Typography } from "fidesui";
import { ReactNode, useMemo, useState } from "react";

import { CustomFieldValues } from "~/features/common/custom-fields";
import {
  DataCategoriesFormItem,
  DatasetReferencesFormItem,
  DataSubjectsFormItem,
  DataUseFormItem,
  DeclarationNameFormItem,
} from "~/features/system/privacy-declaration-fields";
import {
  DataCategory,
  Dataset,
  DataSubject,
  DataUse,
  PrivacyDeclarationResponse,
} from "~/types/api";

export type FormValues = PrivacyDeclarationResponse & {
  customFieldValues: CustomFieldValues;
};

const defaultInitialValues: FormValues = {
  data_categories: [],
  data_subjects: [],
  data_use: "",
  dataset_references: [],
  customFieldValues: {},
  id: "",
};

export const transformFormValueToDeclaration = (
  values: FormValues,
): PrivacyDeclarationResponse => {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const { customFieldValues, ...declaration } = values;
  return {
    ...declaration,
    // Fill in an empty string for name because of https://github.com/ethyca/fideslang/issues/98
    name: values.name ?? "",
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
}

export const SavedIndicator = () => (
  <Typography.Text className="text-sm" data-testid="saved-indicator">
    <Icons.CheckmarkFilled color="var(--fidesui-color-success)" /> Saved
  </Typography.Text>
);

interface Props extends DataProps {
  form?: FormInstance<FormValues>;
  onSubmit: (
    values: PrivacyDeclarationResponse,
  ) => Promise<PrivacyDeclarationResponse[] | undefined>;
  initialValues?: PrivacyDeclarationResponse;
  privacyDeclarationId?: string;
  /** Receives a saved indicator when the form has just been saved and is still pristine. */
  renderHeader?: (props: { saved: boolean }) => ReactNode;
  onSavedChange?: (saved: boolean) => void;
}

export const SimplifiedPrivacyDeclarationForm = ({
  form: externalForm,
  onSubmit,
  initialValues: passedInInitialValues,
  privacyDeclarationId,
  renderHeader,
  onSavedChange,
  allDataUses,
  allDataCategories,
  allDataSubjects,
  allDatasets,
}: Props) => {
  const [internalForm] = Form.useForm<FormValues>();
  const form = externalForm ?? internalForm;

  const initialValues = useMemo(
    () => transformPrivacyDeclarationToFormValues(passedInInitialValues),
    [passedInInitialValues],
  );

  const [saved, setSaved] = useState(false);
  const updateSaved = (next: boolean) => {
    setSaved(next);
    onSavedChange?.(next);
  };

  const handleFinish = async (values: FormValues) => {
    const declaration = transformFormValueToDeclaration(values);
    const success = await onSubmit(declaration);
    if (success) {
      updateSaved(true);
    }
  };

  const isEditing = !!privacyDeclarationId;

  return (
    <Form
      form={form}
      layout="vertical"
      key={privacyDeclarationId ?? "new"}
      initialValues={initialValues}
      onFinish={handleFinish}
      onValuesChange={() => {
        if (saved) {
          updateSaved(false);
        }
      }}
      data-testid={`${initialValues.data_use || "new"}-form`}
    >
      {renderHeader?.({ saved })}
      <DataUseFormItem allDataUses={allDataUses} disabled={isEditing} />
      <DeclarationNameFormItem disabled={isEditing} />
      <DataCategoriesFormItem allDataCategories={allDataCategories} disabled />
      <DataSubjectsFormItem
        allDataSubjects={allDataSubjects}
        disabled
        required
      />
      {allDatasets ? (
        <DatasetReferencesFormItem allDatasets={allDatasets} />
      ) : null}
    </Form>
  );
};
