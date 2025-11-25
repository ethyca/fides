import { isEqual } from "lodash";

import { isErrorResult } from "~/features/common/helpers";
import { FieldTypes } from "~/features/custom-fields/constants";
import { CustomFieldsFormValues } from "~/features/custom-fields/CustomFieldFormValues";
import {
  useAddCustomFieldDefinitionMutation,
  useUpdateCustomFieldDefinitionMutation,
  useUpsertAllowListMutation,
} from "~/features/plus/plus.slice";
import {
  AllowList,
  CustomFieldDefinitionWithId,
} from "~/types/api";
import { RTKResult } from "~/types/errors";
import { LegacyAllowedTypes } from "~/features/common/custom-fields/types";

const generateNewAllowListName = () =>
  Date.now().toString() + Math.random().toString();

// Normalize resource_type from key-form selection
// taxonomy:data_category -> data_category (custom metadata endpoint will map as needed)
// system:information -> system
// system:data use -> privacy declaration
const normalizeResourceType = (rt: string): string => {
  if (rt.startsWith("taxonomy:")) {
    return rt.split(":", 2)[1];
  }
  if (rt === "system:information") {
    return "system";
  }
  if (rt === "system:data use") {
    return "privacy declaration";
  }
  return rt;
};

const useCreateOrUpdateCustomField = () => {
  const [addCustomFieldDefinition, { isLoading: addIsLoading }] =
    useAddCustomFieldDefinitionMutation();
  const [updateCustomFieldDefinition, { isLoading: updateIsLoading }] =
    useUpdateCustomFieldDefinitionMutation();
  const [upsertAllowList] = useUpsertAllowListMutation();

  const createOrUpdate = async (
    values: CustomFieldsFormValues,
    initialField: CustomFieldDefinitionWithId | undefined = undefined,
    initialAllowList: AllowList | undefined = undefined,
  ) => {
    const normalizedResourceType = normalizeResourceType(
      values.resource_type as string,
    );
    if (values.field_type === FieldTypes.OPEN_TEXT) {
      const payload = {
        ...values,
        field_type: LegacyAllowedTypes.STRING,
        id: initialField ? initialField.id : undefined,
        resource_type: normalizedResourceType,
      };
      let result: RTKResult | undefined;
      if (!initialField) {
        result = await addCustomFieldDefinition(payload);
      } else {
        result = await updateCustomFieldDefinition(payload);
      }
      return result;
    }
    if (
      values.field_type === FieldTypes.SINGLE_SELECT ||
      values.field_type === FieldTypes.MULTIPLE_SELECT
    ) {
      if (!initialField) {
        const { options, ...rest } = values;
        // first create the allow list
        const allowListPayload = {
          name: generateNewAllowListName(),
          allowed_values: options ?? [],
        };
        const allowListResult = await upsertAllowList(allowListPayload);
        if (isErrorResult(allowListResult)) {
          return allowListResult;
        }
        // then create the field using the new allow list's id
        const fieldPayload = {
          ...rest,
          field_type:
            values.field_type === FieldTypes.SINGLE_SELECT
              ? LegacyAllowedTypes.STRING
              : LegacyAllowedTypes.STRING_ARRAY,
          allow_list_id: allowListResult.data?.id,
          resource_type: normalizedResourceType,
        };
        const result = await addCustomFieldDefinition(fieldPayload);
        return result;
      }
      // update  the allow list if it's changed
      let allowListResult: RTKResult | undefined;
      const { options, ...rest } = values;
      if (!isEqual(initialAllowList?.allowed_values, options)) {
        const allowListPayload = {
          ...initialAllowList,
          name: initialAllowList?.name ?? generateNewAllowListName(),
          id: initialAllowList?.id,
          allowed_values: options ?? [],
        };
        allowListResult = await upsertAllowList(allowListPayload);
        if (isErrorResult(allowListResult)) {
          return allowListResult;
        }
      }
      // then update the field
      const fieldPayload: CustomFieldDefinitionWithId = {
        ...rest,
        id: initialField.id,
        allow_list_id:
          allowListResult && !isErrorResult(allowListResult)
            ? (allowListResult.data as AllowList).id
            : initialField.allow_list_id,
        resource_type: normalizedResourceType,
        field_type:
          values.field_type === FieldTypes.SINGLE_SELECT
            ? LegacyAllowedTypes.STRING
            : LegacyAllowedTypes.STRING_ARRAY,
      };
      const result = await updateCustomFieldDefinition(fieldPayload);
      return result;
    }
    // field type is a taxonomy
    const { value_type: valueType, ...rest } = values;
    const payload = {
      ...rest,
      id: initialField ? initialField.id : undefined,
      field_type: valueType,
      resource_type: normalizedResourceType,
    };
    let result: RTKResult | undefined;
    if (!initialField) {
      result = await addCustomFieldDefinition(payload);
    } else {
      result = await updateCustomFieldDefinition(payload);
    }
    return result;
  };

  return {
    createOrUpdate,
    isLoading: addIsLoading || updateIsLoading,
  };
};

export default useCreateOrUpdateCustomField;
