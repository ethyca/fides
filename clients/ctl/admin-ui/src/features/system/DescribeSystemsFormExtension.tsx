import { COUNTRY_OPTIONS } from "~/features/common/countries";
import {
  CustomMultiSelect,
  CustomSelect,
  CustomTextInput,
} from "~/features/common/form/inputs";
import { enumToOptions } from "~/features/common/helpers";
import { DataResponsibilityTitle } from "~/types/api";

import { useGetAllSystemsQuery } from "./system.slice";

const dataResponsibilityOptions = enumToOptions(DataResponsibilityTitle);

const DescribeSystemsFormExtension = () => {
  const { data: systems } = useGetAllSystemsQuery();
  const systemOptions = systems
    ? systems.map((s) => ({ label: s.name ?? s.fides_key, value: s.fides_key }))
    : [];

  return (
    <>
      <CustomSelect
        label="Data responsibility title"
        name="data_responsibility_title"
        options={dataResponsibilityOptions}
        tooltip="An attribute to describe the role of responsibility over the personal data, used when exporting to a data map"
      />
      <CustomMultiSelect
        label="System dependencies"
        name="system_dependencies"
        tooltip="A list of fides keys to model dependencies."
        options={systemOptions}
      />
      <CustomMultiSelect
        name="third_country_transfers"
        label="Geographic location"
        tooltip="An optional array to identify any third countries where data is transited to. For consistency purposes, these fields are required to follow the Alpha-3 code set in ISO 3166-1"
        isSearchable
        options={COUNTRY_OPTIONS}
      />
      <CustomTextInput
        label="Administrating department"
        name="administrating_department"
        tooltip="An optional value to identify the owning department or group of the system within your organization"
      />
    </>
  );
};

export default DescribeSystemsFormExtension;
