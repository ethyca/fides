import { ReactNode } from "react";

import { LegalBasisEnum, SpecialCategoriesEnum } from "~/types/api";

import {
  CustomCreatableMultiSelect,
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
import { Labels, TaxonomyEntity, TaxonomyRTKResult } from "./types";

export interface TaxonomyHookData {
  data?: TaxonomyEntity[];
  isLoading: boolean;
  labels: Labels;
  edit: (entity: TaxonomyEntity) => TaxonomyRTKResult;
  extraFormFields?: ReactNode;
}

const enumToOptions = (e: { [s: number]: string }) =>
  Object.entries(e).map((entry) => ({
    value: entry[1],
    label: entry[1],
  }));

// const enumToOptions = (enum: str) => {
//   return Object.entries(enum).map((entry) => ({
//     value: entry[1],
//     label: entry[1],
//   }));
// }

export const useDataCategory = (): TaxonomyHookData => {
  const { data, isLoading } = useGetAllDataCategoriesQuery();

  const labels = {
    fides_key: "Data category",
    name: "Category name",
    description: "Category description",
    parent_key: "Parent category",
  };

  const [edit] = useUpdateDataCategoryMutation();

  return { data, isLoading, labels, edit };
};

export const useDataUse = (): TaxonomyHookData => {
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
        name="special_categories"
        label={labels.special_category}
        options={specialCategories}
      />
      {/* <CustomCreatableMultiSelect
        name="recipient"
        label="Recipients"
        options={[]}
      /> */}
      {/* TODO: legitimate interest: boolean field */}
      <CustomTextInput
        name="legitimate_interest_impact_assessment"
        label={labels.legitimate_interest_impact_assessment}
      />
    </>
  );

  return { data, isLoading, labels, edit, extraFormFields };
};

export const useDataSubject = (): TaxonomyHookData => {
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

  const extraFormFields = <div>hi</div>;

  return { data, isLoading, labels, edit, extraFormFields };
};

export const useDataQualifier = (): TaxonomyHookData => {
  const { data, isLoading } = useGetAllDataQualifiersQuery();

  const labels = {
    fides_key: "Data qualifier",
    name: "Data qualifier name",
    description: "Data qualifier description",
    parent_key: "Parent data qualifier",
  };

  const [edit] = useUpdateDataQualifierMutation();

  return { data, isLoading, labels, edit };
};
