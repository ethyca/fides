import { Stack } from "@fidesui/react";

import { useAppSelector } from "~/app/hooks";
import {
  CustomMultiSelect,
  CustomSelect,
  CustomTextInput,
} from "~/features/common/form/inputs";
import {
  selectDataQualifiers,
  useGetAllDataQualifiersQuery,
} from "~/features/data-qualifier/data-qualifier.slice";
import {
  selectDataSubjects,
  useGetAllDataSubjectsQuery,
} from "~/features/data-subjects/data-subject.slice";
import {
  selectDataUses,
  useGetAllDataUsesQuery,
} from "~/features/data-use/data-use.slice";
import {
  selectDataCategories,
  useGetAllDataCategoriesQuery,
} from "~/features/taxonomy/taxonomy.slice";

import PrivacyDeclarationFormExtension from "./PrivacyDeclarationFormExtension";

interface Props {
  abridged?: boolean;
}
const PrivacyDeclarationForm = ({ abridged }: Props) => {
  // Query subscriptions:
  useGetAllDataCategoriesQuery();
  useGetAllDataSubjectsQuery();
  useGetAllDataQualifiersQuery();
  useGetAllDataUsesQuery();

  const allDataCategories = useAppSelector(selectDataCategories);
  const allDataSubjects = useAppSelector(selectDataSubjects);
  const allDataUses = useAppSelector(selectDataUses);
  const allDataQualifiers = useAppSelector(selectDataQualifiers);

  return (
    <Stack spacing={4}>
      <CustomTextInput
        name="name"
        label="Declaration name"
        tooltip="A system may have multiple privacy declarations, so each declaration should have a name to distinguish them clearly."
      />
      <CustomMultiSelect
        name="data_categories"
        label="Data categories"
        options={allDataCategories?.map((data) => ({
          value: data.fides_key,
          label: data.fides_key,
        }))}
        tooltip="What type of data is your system processing? This could be various types of user or system data."
      />
      <CustomSelect
        id="data_use"
        label="Data use"
        name="data_use"
        options={allDataUses.map((data) => ({
          value: data.fides_key,
          label: data.fides_key,
        }))}
        tooltip="What is the system using the data for. For example, is it for third party advertising or perhaps simply providing system operations."
      />
      <CustomMultiSelect
        name="data_subjects"
        label="Data subjects"
        options={allDataSubjects.map((data) => ({
          value: data.fides_key,
          label: data.fides_key,
        }))}
        tooltip="Whose data are you processing? This could be customers, employees or any other type of user in your system."
      />
      <CustomSelect
        id="data_qualifier"
        label="Data qualifier"
        name="data_qualifier"
        options={allDataQualifiers.map((data) => ({
          value: data.fides_key,
          label: data.fides_key,
        }))}
        tooltip="How identifiable is the user in the data in this system? For instance, is it anonymized data where the user is truly unknown/unidentifiable, or it is partially identifiable data?"
      />
      {!abridged ? <PrivacyDeclarationFormExtension /> : null}
    </Stack>
  );
};

export default PrivacyDeclarationForm;
