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
  AllowedTypes,
  AllowList,
  CustomFieldDefinitionWithId,
} from "~/types/api";
import { RTKResult } from "~/types/errors";

const generateNewAllowListName = () =>
  Date.now().toString() + Math.random().toString();

const useCreateOrUpdateCustomField = () => {
  const [addCustomFieldDefinition, { isLoading: addIsLoading }] =
    useAddCustomFieldDefinitionMutation();
  const [updateCustomFieldDefinition, { isLoading: updateIsLoading }] =
    useUpdateCustomFieldDefinitionMutation();
  const [upsertAllowList] = useUpsertAllowListMutation();

  const createOrUpdate = async (
    values: CustomFieldsFormValues,
    initialField: CustomFieldDefinitionWithId | undefined,
    initialAllowList: AllowList | undefined,
  ) => {
    if (values.field_type === FieldTypes.OPEN_TEXT) {
      const payload = {
        ...values,
        field_type: AllowedTypes.STRING,
        id: initialField ? initialField.id : undefined,
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
              ? AllowedTypes.STRING
              : // eslint-disable-next-line no-underscore-dangle
                AllowedTypes.STRING_,
          allow_list_id: allowListResult.data?.id,
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
      const fieldPayload = {
        ...rest,
        allow_list_id: allowListResult
          ? // @ts-ignore - we returned early if there was an error so "data" will always be present here
            allowListResult.data.id
          : initialField.allow_list_id,
        field_type:
          values.field_type === FieldTypes.SINGLE_SELECT
            ? AllowedTypes.STRING
            : // eslint-disable-next-line no-underscore-dangle
              AllowedTypes.STRING_,
      };
      const result = await updateCustomFieldDefinition(fieldPayload);
      return result;
    }
    return undefined;
  };

  return {
    createOrUpdate,
    isLoading: addIsLoading || updateIsLoading,
  };
};

export default useCreateOrUpdateCustomField;
