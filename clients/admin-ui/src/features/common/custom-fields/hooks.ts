import { useCallback, useMemo } from "react";

import { useFeatures } from "~/features/common/features";
import { useAlert } from "~/features/common/hooks";
import {
  useBulkUpdateCustomFieldsMutation,
  useGetAllAllowListQuery,
  useGetCustomFieldDefinitionsByResourceTypeQuery,
  useGetCustomFieldsForResourceQuery,
} from "~/features/plus/plus.slice";
import { CustomFieldWithId, ResourceTypes } from "~/types/api";

import { filterWithId } from "./helpers";
import { CustomFieldsFormValues, CustomFieldValues } from "./types";

type UseCustomFieldsOptions = {
  resourceFidesKey?: string;
  resourceType: ResourceTypes;
};

export const useCustomFields = ({
  resourceFidesKey,
  resourceType,
}: UseCustomFieldsOptions) => {
  const { errorAlert } = useAlert();
  const { plus: isEnabled } = useFeatures();

  // This keeps track of the fides key that was initially passed in. If that key started out blank,
  // then we know the API call will just 404.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const queryFidesKey = useMemo(() => resourceFidesKey ?? "", []);

  const allAllowListQuery = useGetAllAllowListQuery(true, {
    skip: !isEnabled,
  });
  const customFieldDefinitionsQuery =
    useGetCustomFieldDefinitionsByResourceTypeQuery(resourceType, {
      skip: !isEnabled,
    });
  const {
    data,
    isLoading: isCustomFieldIsLoading,
    error,
    isError,
  } = useGetCustomFieldsForResourceQuery(resourceFidesKey ?? "", {
    skip: queryFidesKey !== "" && !(isEnabled && queryFidesKey),
  });

  const [bulkUpdateCustomFieldsMutationTrigger] =
    useBulkUpdateCustomFieldsMutation();

  const isLoading =
    allAllowListQuery.isLoading ||
    customFieldDefinitionsQuery.isLoading ||
    isCustomFieldIsLoading;

  const idToAllowListWithOptions = useMemo(
    () =>
      new Map(
        filterWithId(allAllowListQuery.data).map((allowList) => [
          allowList.id,
          {
            ...allowList,
            options: (allowList.allowed_values ?? []).map((value) => ({
              value,
              label: value,
            })),
          },
        ]),
      ),
    [allAllowListQuery.data],
  );

  const activeCustomFieldDefinition = useMemo(
    () => customFieldDefinitionsQuery.data?.filter((cfd) => cfd.active),
    [customFieldDefinitionsQuery.data],
  );

  const idToCustomFieldDefinition = useMemo(
    () =>
      new Map(
        filterWithId(activeCustomFieldDefinition).map((cfd) => [cfd.id, cfd]),
      ),
    [activeCustomFieldDefinition],
  );

  const definitionIdToCustomField: Map<string, CustomFieldWithId> =
    useMemo(() => {
      // @ts-ignore
      if (isError && error?.status === 404) {
        return new Map();
      }
      const newMap = new Map(
        filterWithId(data).map((fd) => [fd.custom_field_definition_id, fd]),
      );
      return newMap;
    }, [data, isError, error]);

  const sortedCustomFieldDefinitionIds = useMemo(() => {
    const ids = [...idToCustomFieldDefinition.keys()];
    ids.sort();
    return ids;
  }, [idToCustomFieldDefinition]);

  /**
   * Transformed version of definitionIdToCustomField to be easy
   * to pass into Formik
   */
  const customFieldValues = useMemo(() => {
    const values: CustomFieldValues = {};
    if (activeCustomFieldDefinition && definitionIdToCustomField) {
      activeCustomFieldDefinition.forEach((value) => {
        const customField = definitionIdToCustomField.get(value.id || "");
        if (customField) {
          if (!!value.allow_list_id && value.field_type === "string[]") {
            values[customField.custom_field_definition_id] = customField.value;
          } else {
            values[customField.custom_field_definition_id] =
              customField.value.toString();
          }
        }
      });
    }
    return values;
  }, [activeCustomFieldDefinition, definitionIdToCustomField]);

  /**
   * Issue a batch of upsert and delete requests that will sync the form selections to the
   * backend.
   */
  const upsertCustomFields = useCallback(
    async (formValues: CustomFieldsFormValues) => {
      if (!isEnabled) {
        return;
      }

      // When creating a resource, the fides key may have initially been blank.
      // But by the time the form is submitted it must not be blank (not undefined, not an empty string).
      const fidesKey =
        "fides_key" in formValues && formValues.fides_key !== ""
          ? formValues.fides_key
          : resourceFidesKey;

      if (!fidesKey) {
        return;
      }

      const { customFieldValues: customFieldValuesFromForm } = formValues;

      // This will be undefined if the form never rendered a `CustomFieldList` that would assign
      // form values.
      if (
        !customFieldValuesFromForm ||
        Object.keys(customFieldValuesFromForm).length === 0
      ) {
        return;
      }

      const upsertList: Array<CustomFieldWithId> = [];
      const deleteList: Array<string> = [];

      sortedCustomFieldDefinitionIds.forEach((definitionId) => {
        const customField = definitionIdToCustomField.get(definitionId);
        const value = customFieldValuesFromForm[definitionId];

        if (
          value === undefined ||
          value === "" ||
          (Array.isArray(value) && value.length === 0)
        ) {
          if (customField?.id) {
            deleteList.push(customField.id);
          }
        } else {
          upsertList.push({
            custom_field_definition_id: definitionId,
            resource_id: fidesKey,
            id: customField?.id,
            value,
          });
        }
      });

      try {
        await bulkUpdateCustomFieldsMutationTrigger({
          resource_type: resourceType,
          resource_id: fidesKey,
          upsert: upsertList,
          delete: deleteList,
        });
      } catch (e) {
        errorAlert(
          `One or more custom fields have failed to save, please try again.`,
        );
        // eslint-disable-next-line no-console
        console.error(e);
      }
    },
    [
      isEnabled,
      definitionIdToCustomField,
      errorAlert,
      resourceFidesKey,
      sortedCustomFieldDefinitionIds,
      bulkUpdateCustomFieldsMutationTrigger,
      resourceType,
    ],
  );

  return {
    customFieldValues,
    definitionIdToCustomField,
    idToAllowListWithOptions,
    idToCustomFieldDefinition,
    isEnabled,
    isLoading,
    sortedCustomFieldDefinitionIds,
    upsertCustomFields,
  };
};
