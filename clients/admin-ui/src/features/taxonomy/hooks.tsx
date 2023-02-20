import { ReactNode, useState } from "react";

import { CustomFieldsList } from "~/features/common/custom-fields";
import { useCustomFields } from "~/features/common/custom-fields/hooks";
import { RTKResult } from "~/features/common/types";
import {
  DataCategory,
  DataQualifier,
  DataSubject,
  DataSubjectRightsEnum,
  DataUse,
  IncludeExcludeEnum,
  LegalBasisEnum,
  ResourceTypes,
  SpecialCategoriesEnum,
} from "~/types/api";

import { YesNoOptions } from "../common/constants";
import {
  CustomCreatableMultiSelect,
  CustomRadioGroup,
  CustomSelect,
  CustomTextInput,
} from "../common/form/inputs";
import { enumToOptions } from "../common/helpers";
import {
  useCreateDataQualifierMutation,
  useDeleteDataQualifierMutation,
  useGetAllDataQualifiersQuery,
  useUpdateDataQualifierMutation,
} from "../data-qualifier/data-qualifier.slice";
import {
  useCreateDataSubjectMutation,
  useDeleteDataSubjectMutation,
  useGetAllDataSubjectsQuery,
  useUpdateDataSubjectMutation,
} from "../data-subjects/data-subject.slice";
import {
  useCreateDataUseMutation,
  useDeleteDataUseMutation,
  useGetAllDataUsesQuery,
  useUpdateDataUseMutation,
} from "../data-use/data-use.slice";
import { parentKeyFromFidesKey } from "./helpers";
import {
  useCreateDataCategoryMutation,
  useDeleteDataCategoryMutation,
  useGetAllDataCategoriesQuery,
  useUpdateDataCategoryMutation,
} from "./taxonomy.slice";
import { FormValues, Labels, TaxonomyEntity } from "./types";

export interface TaxonomyHookData<T extends TaxonomyEntity> {
  data?: TaxonomyEntity[];
  isLoading: boolean;
  labels: Labels;
  resourceType?: ResourceTypes;
  entityToEdit: T | null;
  setEntityToEdit: (entity: T | null) => void;
  handleCreate: (
    initialValues: FormValues,
    newValues: FormValues
  ) => RTKResult<TaxonomyEntity>;
  handleEdit: (
    initialValues: FormValues,
    newValues: FormValues
  ) => RTKResult<TaxonomyEntity>;
  handleDelete: (key: string) => RTKResult<string>;
  renderExtraFormFields?: (entity: T) => ReactNode;
  transformEntityToInitialValues: (entity: T) => FormValues;
}

const transformTaxonomyBaseToInitialValues = (t: TaxonomyEntity) => ({
  fides_key: t.fides_key ?? "",
  name: t.name ?? "",
  description: t.description ?? "",
  parent_key: t.parent_key ?? "",
  is_default: t.is_default ?? false,
});

const transformBaseFormValuesToEntity = (
  initialValues: FormValues,
  newValues: FormValues
) => {
  const isCreate = initialValues.fides_key === "";

  // parent_key and fides_keys are immutable
  // parent_key also needs to be undefined, not an empty string, if there is no parent element
  const entity = { ...newValues };
  if (isCreate) {
    const parentKey = parentKeyFromFidesKey(newValues.fides_key);
    entity.parent_key = parentKey === "" ? undefined : parentKey;
  } else {
    entity.parent_key =
      initialValues.parent_key === "" ? undefined : initialValues.parent_key;
    entity.fides_key = initialValues.fides_key;
  }

  delete entity.definitionIdToCustomFieldValue;

  return entity;
};

export const useDataCategory = (): TaxonomyHookData<DataCategory> => {
  const resourceType = ResourceTypes.DATA_CATEGORY;
  const [entityToEdit, setEntityToEdit] = useState<DataCategory | null>(null);

  const { data, isLoading } = useGetAllDataCategoriesQuery();

  const labels = {
    fides_key: "Data category",
    name: "Category name",
    description: "Category description",
    parent_key: "Parent category",
  };

  const [createDataCategoryMutationTrigger] = useCreateDataCategoryMutation();
  const [updateDataCategoryMutationTrigger] = useUpdateDataCategoryMutation();
  const [deleteDataCategoryMutationTrigger] = useDeleteDataCategoryMutation();

  const customFields = useCustomFields({
    resourceFidesKey: entityToEdit?.fides_key,
    resourceType,
  });

  const handleCreate = async (
    initialValues: FormValues,
    newValues: FormValues
  ) => {
    const payload = transformBaseFormValuesToEntity(initialValues, newValues);
    const result = await createDataCategoryMutationTrigger(payload);

    if (customFields.isEnabled) {
      await customFields.upsertCustomFields(newValues);
    }

    return result;
  };

  const handleEdit = async (
    initialValues: FormValues,
    newValues: FormValues
  ) => {
    const payload = transformBaseFormValuesToEntity(initialValues, newValues);
    const result = updateDataCategoryMutationTrigger(payload);

    if (customFields.isEnabled) {
      await customFields.upsertCustomFields(newValues);
    }

    return result;
  };

  const handleDelete = deleteDataCategoryMutationTrigger;

  const renderExtraFormFields = (formValues: FormValues) => (
    <CustomFieldsList
      resourceFidesKey={formValues.fides_key}
      resourceType={resourceType}
    />
  );

  return {
    data,
    isLoading,
    labels,
    resourceType,
    entityToEdit,
    setEntityToEdit,
    handleCreate,
    handleEdit,
    handleDelete,
    renderExtraFormFields,
    transformEntityToInitialValues: transformTaxonomyBaseToInitialValues,
  };
};

export const useDataUse = (): TaxonomyHookData<DataUse> => {
  const resourceType = ResourceTypes.DATA_USE;
  const [entityToEdit, setEntityToEdit] = useState<DataUse | null>(null);

  const { data, isLoading } = useGetAllDataUsesQuery();

  const labels = {
    fides_key: "Data use",
    name: "Data use name",
    description: "Data use description",
    parent_key: "Parent data use",
    legal_basis: "Legal basis",
    special_category: "Special category",
    recipient: "Recipient",
    legitimate_interest: "Legitimate interest",
    legitimate_interest_impact_assessment:
      "Legitimate interest impact assessment",
  };

  const [createDataUseMutationTrigger] = useCreateDataUseMutation();
  const [updateDataUseMutationTrigger] = useUpdateDataUseMutation();
  const [deleteDataUseMutationTrigger] = useDeleteDataUseMutation();

  const transformFormValuesToEntity = (formValues: DataUse) => ({
    ...formValues,
    // text inputs don't like having undefined, so we originally converted
    // to "", but on submission we need to convert back to undefined
    legitimate_interest_impact_assessment:
      formValues.legitimate_interest_impact_assessment === ""
        ? undefined
        : formValues.legitimate_interest_impact_assessment,
    legitimate_interest: !!(
      formValues.legitimate_interest?.toString() === "true"
    ),
    legal_basis:
      formValues.legal_basis?.toString() === ""
        ? undefined
        : formValues.legal_basis,
    special_category:
      formValues.special_category?.toString() === ""
        ? undefined
        : formValues.special_category,
  });

  const customFields = useCustomFields({
    resourceFidesKey: entityToEdit?.fides_key,
    resourceType,
  });

  const handleCreate = async (
    initialValues: FormValues,
    newValues: FormValues
  ) => {
    const payload = transformFormValuesToEntity(
      transformBaseFormValuesToEntity(initialValues, newValues)
    );
    const result = await createDataUseMutationTrigger(payload);

    if (customFields.isEnabled) {
      await customFields.upsertCustomFields(newValues);
    }

    return result;
  };

  const handleEdit = async (
    initialValues: FormValues,
    newValues: FormValues
  ) => {
    const payload = transformFormValuesToEntity(
      transformBaseFormValuesToEntity(initialValues, newValues)
    );
    const result = updateDataUseMutationTrigger(payload);

    if (customFields.isEnabled) {
      await customFields.upsertCustomFields(newValues);
    }

    return result;
  };

  const handleDelete = deleteDataUseMutationTrigger;

  const transformEntityToInitialValues = (du: DataUse) => {
    const base = transformTaxonomyBaseToInitialValues(du);
    return {
      ...base,
      legal_basis: du.legal_basis,
      special_category: du.special_category,
      recipients: du.recipients ?? [],
      legitimate_interest:
        du.legitimate_interest == null
          ? "false"
          : du.legitimate_interest.toString(),
      legitimate_interest_impact_assessment:
        du.legitimate_interest_impact_assessment ?? "",
    };
  };

  const legalBases = enumToOptions(LegalBasisEnum);
  const specialCategories = enumToOptions(SpecialCategoriesEnum);

  const renderExtraFormFields = (formValues: DataUse) => (
    <>
      <CustomSelect
        name="legal_basis"
        label={labels.legal_basis}
        options={legalBases}
        isClearable
      />
      <CustomSelect
        name="special_category"
        label={labels.special_category}
        options={specialCategories}
        isClearable
      />
      <CustomCreatableMultiSelect
        name="recipients"
        label={labels.recipient}
        options={[]}
        size="sm"
      />
      <CustomRadioGroup
        name="legitimate_interest"
        label={labels.legitimate_interest}
        options={YesNoOptions}
      />
      {formValues.legitimate_interest?.toString() === "true" ? (
        <CustomTextInput
          name="legitimate_interest_impact_assessment"
          label={labels.legitimate_interest_impact_assessment}
        />
      ) : null}
      <CustomFieldsList
        resourceFidesKey={formValues.fides_key}
        resourceType={resourceType}
      />
    </>
  );

  return {
    data,
    isLoading,
    labels,
    resourceType,
    entityToEdit,
    setEntityToEdit,
    handleCreate,
    handleEdit,
    handleDelete,
    renderExtraFormFields,
    transformEntityToInitialValues,
  };
};

export const useDataSubject = (): TaxonomyHookData<DataSubject> => {
  const resourceType = ResourceTypes.DATA_SUBJECT;
  const [entityToEdit, setEntityToEdit] = useState<DataSubject | null>(null);

  const { data, isLoading } = useGetAllDataSubjectsQuery();

  const labels = {
    fides_key: "Data subject",
    name: "Data subject name",
    description: "Data subject description",
    rights: "Rights",
    strategy: "Strategy",
    automatic_decisions: "Automatic decisions or profiling",
  };

  const [createDataSubjectMutationTrigger] = useCreateDataSubjectMutation();
  const [updateDataSubjectMutationTrigger] = useUpdateDataSubjectMutation();
  const [deleteDataSubjectMutationTrigger] = useDeleteDataSubjectMutation();

  const transformFormValuesToEntity = (entity: DataSubject) => {
    const transformedEntity: DataSubject = {
      ...entity,
      // @ts-ignore because DataSubjects have their rights field nested, which
      // does not work well when being passed into a form. We unnest them in
      // transformEntityToInitialValues, and it is the unnested value we get back
      // here, but it would make the types of our other components much more complicated
      // to properly type just for this special case
      rights:
        // @ts-ignore for the same reason as above
        entity.rights.length
          ? // @ts-ignore for the same reason as above
            { values: entity.rights, strategy: entity.strategy }
          : undefined,
      automatic_decisions_or_profiling: !!(
        entity.automated_decisions_or_profiling?.toString() === "true"
      ),
    };
    // @ts-ignore for the same reason as above
    delete transformedEntity.strategy;
    return transformedEntity;
  };

  const customFields = useCustomFields({
    resourceFidesKey: entityToEdit?.fides_key,
    resourceType,
  });

  const handleCreate = async (
    initialValues: FormValues,
    newValues: FormValues
  ) => {
    const payload = transformFormValuesToEntity(
      transformBaseFormValuesToEntity(initialValues, newValues)
    );
    const result = await createDataSubjectMutationTrigger(payload);

    if (customFields.isEnabled) {
      await customFields.upsertCustomFields(newValues);
    }

    return result;
  };

  const handleEdit = async (
    initialValues: FormValues,
    newValues: FormValues
  ) => {
    const payload = transformFormValuesToEntity(
      transformBaseFormValuesToEntity(initialValues, newValues)
    );
    const result = updateDataSubjectMutationTrigger(payload);

    if (customFields.isEnabled) {
      await customFields.upsertCustomFields(newValues);
    }

    return result;
  };

  const handleDelete = deleteDataSubjectMutationTrigger;

  const transformEntityToInitialValues = (ds: DataSubject) => {
    const base = transformTaxonomyBaseToInitialValues(ds);
    return {
      ...base,
      rights: ds.rights?.values ?? [],
      strategy: ds.rights?.strategy,
      automatic_decisions_or_profiling:
        ds.automated_decisions_or_profiling == null
          ? "false"
          : ds.automated_decisions_or_profiling.toString(),
    };
  };

  const renderExtraFormFields = (entity: DataSubject) => (
    <>
      <CustomSelect
        name="rights"
        label={labels.rights}
        options={enumToOptions(DataSubjectRightsEnum)}
        isMulti
      />
      {/* @ts-ignore because of discrepancy between form and entity type, again */}
      {entity.rights && entity.rights.length ? (
        <CustomSelect
          name="strategy"
          label={labels.strategy}
          options={enumToOptions(IncludeExcludeEnum)}
        />
      ) : null}
      <CustomRadioGroup
        name="automatic_decisions_or_profiling"
        label={labels.automatic_decisions}
        options={YesNoOptions}
      />
      <CustomFieldsList
        resourceFidesKey={entity.fides_key}
        resourceType={resourceType}
      />
    </>
  );

  return {
    data,
    isLoading,
    labels,
    resourceType,
    entityToEdit,
    setEntityToEdit,
    handleCreate,
    handleEdit,
    handleDelete,
    renderExtraFormFields,
    transformEntityToInitialValues,
  };
};

export const useDataQualifier = (): TaxonomyHookData<DataQualifier> => {
  const { data, isLoading } = useGetAllDataQualifiersQuery();
  const [entityToEdit, setEntityToEdit] = useState<DataQualifier | null>(null);

  const labels = {
    fides_key: "Data qualifier",
    name: "Data qualifier name",
    description: "Data qualifier description",
    parent_key: "Parent data qualifier",
  };

  const [createDataQualifierMutationTrigger] = useCreateDataQualifierMutation();
  const [updateDataQualifierMutationTrigger] = useUpdateDataQualifierMutation();
  const [deleteDataQualifierMutationTrigger] = useDeleteDataQualifierMutation();

  const handleCreate = (initialValues: FormValues, newValues: FormValues) =>
    createDataQualifierMutationTrigger(
      transformBaseFormValuesToEntity(initialValues, newValues)
    );

  const handleEdit = (initialValues: FormValues, newValues: FormValues) =>
    updateDataQualifierMutationTrigger(
      transformBaseFormValuesToEntity(initialValues, newValues)
    );

  const handleDelete = deleteDataQualifierMutationTrigger;

  return {
    data,
    isLoading,
    labels,
    entityToEdit,
    setEntityToEdit,
    handleCreate,
    handleEdit,
    handleDelete,
    transformEntityToInitialValues: transformTaxonomyBaseToInitialValues,
  };
};
