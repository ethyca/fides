import { ReactNode } from "react";

import {
  DataCategory,
  DataQualifier,
  DataSubject,
  DataSubjectRightsEnum,
  DataUse,
  IncludeExcludeEnum,
  LegalBasisEnum,
  SpecialCategoriesEnum,
} from "~/types/api";

import {
  CustomCreatableMultiSelect,
  CustomMultiSelect,
  CustomSelect,
  CustomTextInput,
} from "../common/form/inputs";
import {
  useGetAllDataQualifiersQuery,
  useUpdateDataQualifierMutation,
} from "../data-qualifier/data-qualifier.slice";
import {
  useGetAllDataSubjectsQuery,
  useUpdateDataSubjectMutation,
} from "../data-subjects/data-subject.slice";
import {
  useGetAllDataUsesQuery,
  useUpdateDataUseMutation,
} from "../data-use/data-use.slice";
import {
  useGetAllDataCategoriesQuery,
  useUpdateDataCategoryMutation,
} from "./data-categories.slice";
import type { FormValues } from "./TaxonomyFormBase";
import { Labels, TaxonomyEntity, TaxonomyRTKResult } from "./types";

export interface TaxonomyHookData<T extends TaxonomyEntity> {
  data?: TaxonomyEntity[];
  isLoading: boolean;
  labels: Labels;
  edit: (entity: T) => TaxonomyRTKResult;
  extraFormFields?: ReactNode;
  transformEntityToInitialValues: (entity: T) => FormValues;
}

const enumToOptions = (e: { [s: number]: string }) =>
  Object.entries(e).map((entry) => ({
    value: entry[1],
    label: entry[1],
  }));

const transformTaxonomyBaseToInitialValues = (t: TaxonomyEntity) => ({
  fides_key: t.fides_key ?? "",
  name: t.name ?? "",
  description: t.description ?? "",
  parent_key: t.parent_key ?? "",
  is_default: t.is_default ?? false,
});

export const useDataCategory = (): TaxonomyHookData<DataCategory> => {
  const { data, isLoading } = useGetAllDataCategoriesQuery();

  const labels = {
    fides_key: "Data category",
    name: "Category name",
    description: "Category description",
    parent_key: "Parent category",
  };

  const [edit] = useUpdateDataCategoryMutation();

  return {
    data,
    isLoading,
    labels,
    edit,
    transformEntityToInitialValues: transformTaxonomyBaseToInitialValues,
  };
};

export const useDataUse = (): TaxonomyHookData<DataUse> => {
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

  const [edit] = useUpdateDataUseMutation();
  const handleEdit = (entity: DataUse) =>
    edit({
      ...entity,
      // text inputs don't like having undefined, so we originally converted
      // to "", but on submission we need to convert back to undefined
      legitimate_interest_impact_assessment:
        entity.legitimate_interest_impact_assessment ?? undefined,
    });

  const transformEntityToInitialValues = (du: DataUse) => {
    const base = transformTaxonomyBaseToInitialValues(du);
    return {
      ...base,
      legal_basis: du.legal_basis,
      special_category: du.special_category,
      recipients: du.recipients ?? [],
      legitimate_interest: du.legitimate_interest,
      legitimate_interest_impact_assessment:
        du.legitimate_interest_impact_assessment ?? "",
    };
  };

  const legalBases = enumToOptions(LegalBasisEnum);
  const specialCategories = enumToOptions(SpecialCategoriesEnum);

  const extraFormFields = (
    <>
      <CustomSelect
        name="legal_basis"
        label={labels.legal_basis}
        options={legalBases}
      />
      <CustomSelect
        name="special_category"
        label={labels.special_category}
        options={specialCategories}
      />
      <CustomCreatableMultiSelect
        name="recipients"
        label="Recipients"
        options={[]}
        size="sm"
      />
      {/* TODO: legitimate interest: boolean field */}
      <CustomTextInput
        name="legitimate_interest_impact_assessment"
        label={labels.legitimate_interest_impact_assessment}
      />
    </>
  );

  return {
    data,
    isLoading,
    labels,
    edit: handleEdit,
    extraFormFields,
    transformEntityToInitialValues,
  };
};

export const useDataSubject = (): TaxonomyHookData<DataSubject> => {
  const { data, isLoading } = useGetAllDataSubjectsQuery();

  const labels = {
    fides_key: "Data subject",
    name: "Data subject name",
    description: "Data subject description",
    parent_key: "Parent data subject",
    rights: "Rights",
    strategy: "Strategy",
    automatic_decisions: "Automatic decisions or profiling",
  };

  const [edit] = useUpdateDataSubjectMutation();

  const handleEdit = (entity: TaxonomyEntity) => {
    const transformedEntity = {
      ...entity,
      // @ts-ignore because DataSubjects have their rights field nested, which
      // does not work well when being passed into a form. We unnest them in
      // transformEntityToInitialValues, and it is the unnested value we get back
      // here, but it would make the types of our other components much more complicated
      // to properly type just for this special case
      rights: { values: entity.rights, strategy: entity.strategy },
    };
    return edit(transformedEntity);
  };

  const transformEntityToInitialValues = (ds: DataSubject) => {
    const base = transformTaxonomyBaseToInitialValues(ds);
    return {
      ...base,
      rights: ds.rights?.values ?? [],
      strategy: ds.rights?.strategy,
      automatic_decisions: ds.automated_decisions_or_profiling,
    };
  };

  const extraFormFields = (
    <>
      <CustomMultiSelect
        name="rights"
        label={labels.rights}
        options={enumToOptions(DataSubjectRightsEnum)}
      />
      <CustomSelect
        name="strategy"
        label={labels.strategy}
        options={enumToOptions(IncludeExcludeEnum)}
      />
      {/* TODO: automatic decisions: boolean field */}
    </>
  );

  return {
    data,
    isLoading,
    labels,
    edit: handleEdit,
    extraFormFields,
    transformEntityToInitialValues,
  };
};

export const useDataQualifier = (): TaxonomyHookData<DataQualifier> => {
  const { data, isLoading } = useGetAllDataQualifiersQuery();

  const labels = {
    fides_key: "Data qualifier",
    name: "Data qualifier name",
    description: "Data qualifier description",
    parent_key: "Parent data qualifier",
  };

  const [edit] = useUpdateDataQualifierMutation();

  return {
    data,
    isLoading,
    labels,
    edit,
    transformEntityToInitialValues: transformTaxonomyBaseToInitialValues,
  };
};
