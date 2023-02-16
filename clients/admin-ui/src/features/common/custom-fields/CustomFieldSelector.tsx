import { useField } from "formik";
import { useEffect } from "react";

import { CustomSelect } from "~/features/common/form/inputs";
import { AllowedTypes } from "~/types/api";

import {
  AllowListWithOptions,
  CustomFieldDefinitionExisting,
  CustomFieldExisting,
} from "./types";

type Props = {
  allowList: AllowListWithOptions;
  customField?: CustomFieldExisting;
  customFieldDefinition: CustomFieldDefinitionExisting;
};

export const CustomFieldSelector = ({
  allowList,
  customField,
  customFieldDefinition,
}: Props) => {
  const name = `definitionIdToCustomFieldValue.${customFieldDefinition.id}`;
  const label = customFieldDefinition.name;
  const tooltip = customFieldDefinition.description;
  const { options } = allowList;

  const [, meta, helpers] = useField({ name });

  // This is a bit of a hack to set the initial value of the selector based on the CustomField
  // returned by the API (if any). The "correct" way to do this would be to have the `initialValues`
  // passed to `Formik` include the API values mapped by definition ID. However, because custom
  // fields are so dynamic and depend on multiple API calls, mixing that logic into the (already
  // complex) taxonomy form initialization isn't feasible for now. Those values are created by:
  // src/features/taxonomy/hooks.tsx.
  useEffect(
    () => {
      if (!customField?.value) {
        return;
      }

      if (meta.touched) {
        return;
      }

      helpers.setValue(
        customFieldDefinition.field_type !== AllowedTypes.STRING
          ? customField.value
          : customField.value.toString(),
        false
      );
    },
    // This should only ever run once, on first render.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    []
  );

  return (
    <CustomSelect
      isClearable
      isMulti={customFieldDefinition.field_type !== AllowedTypes.STRING}
      label={label}
      name={name}
      options={options}
      tooltip={tooltip}
      defaultValue={customField?.value ?? ""}
    />
  );
};
