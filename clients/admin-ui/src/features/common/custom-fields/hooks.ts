import { useCallback, useMemo } from "react";

import { useFeatures } from "~/features/common/features";
import { useAlert } from "~/features/common/hooks";
import {
  useDeleteCustomFieldMutation,
  useGetAllAllowListQuery,
  useGetCustomFieldDefinitionsByResourceTypeQuery,
  useGetCustomFieldsForResourceQuery,
  useUpsertCustomFieldMutation,
} from "~/features/plus/plus.slice";
import { ResourceTypes } from "~/types/api";

import { filterWithId } from "./helpers";
import { CustomFieldsFormValues } from "./types";

type UseCustomFieldsOptions = {
  resourceFidesKey?: string;
  resourceType: ResourceTypes;
};

export const useCustomFields = ({
  resourceFidesKey,
  resourceType,
}: UseCustomFieldsOptions) => {
  const { errorAlert, successAlert } = useAlert();
  const { flags, plus } = useFeatures();
  const isEnabled = flags.customFields && plus;

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

  // The `fixedCacheKey` options will ensure that components referencing the same resource will
  // share mutation info. That won't be too useful, though, because `upsertCustomField` can issue
  // multiple requests: one for each field associated with the resource.
  const [upsertCustomFieldMutationTrigger, upsertCustomFieldMutationResult] =
    useUpsertCustomFieldMutation({ fixedCacheKey: resourceFidesKey });
  const [deleteCustomFieldMutationTrigger, deleteCustomFieldMutationResult] =
    useDeleteCustomFieldMutation({ fixedCacheKey: resourceFidesKey });

  const isLoading =
    allAllowListQuery.isLoading ||
    customFieldDefinitionsQuery.isLoading ||
    isCustomFieldIsLoading ||
    upsertCustomFieldMutationResult.isLoading ||
    deleteCustomFieldMutationResult.isLoading;

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
        ])
      ),
    [allAllowListQuery.data]
  );

  const activeCustomFieldDefinition = useMemo(
    () => customFieldDefinitionsQuery.data?.filter((cfd) => cfd.active),
    [customFieldDefinitionsQuery.data]
  );

  const idToCustomFieldDefinition = useMemo(
    () =>
      new Map(
        filterWithId(activeCustomFieldDefinition).map((cfd) => [cfd.id, cfd])
      ),
    [activeCustomFieldDefinition]
  );

  const definitionIdToCustomField = useMemo(() => {
    console.log("Error: ", error);
    if (isError && error.status === 404) {
      return new Map();
    }
    const newMap = new Map(
      filterWithId(data).map((fd) => [fd.custom_field_definition_id, fd])
    );
    console.log("newMap: ", newMap);
    console.log("customFieldsQuery: ", data);
    return newMap;
  }, [data, isError]);

  const sortedCustomFieldDefinitionIds = useMemo(() => {
    const ids = [...idToCustomFieldDefinition.keys()];
    ids.sort();
    return ids;
  }, [idToCustomFieldDefinition]);

  /**
   * Issue a batch of upsert and delete requests that will sync the form selections to the
   * backend.
   */
  const upsertCustomFields = useCallback(
    async (formValues: CustomFieldsFormValues) => {
      // When creating an resource, the fides key may have initially been blank. But by the time the
      // form is submitted it must not be blank (not undefined, not an empty string).
      const fidesKey = formValues.fides_key || resourceFidesKey;
      if (!fidesKey) {
        return;
      }

      const { definitionIdToCustomFieldValue } = formValues;

      // This will be undefined if the form never rendered a `CustomFieldList` that would assign
      // form values.
      if (!definitionIdToCustomFieldValue) {
        return;
      }

      try {
        // This would be a lot simpler (and more efficient) if the API had an endpoint for updating
        // all the metadata associated with a field, including deleting options that weren't passed.
        await Promise.allSettled(
          sortedCustomFieldDefinitionIds.map((definitionId) => {
            const customField = definitionIdToCustomField.get(definitionId);
            const value = definitionIdToCustomFieldValue[definitionId];

            if (
              value === undefined ||
              value === "" ||
              (Array.isArray(value) && value.length === 0)
            ) {
              if (!customField?.id) {
                return undefined;
              }

              return deleteCustomFieldMutationTrigger(customField);
            }

            const body = {
              custom_field_definition_id: definitionId,
              resource_id: fidesKey,
              id: customField?.id,
              value,
            };

            return upsertCustomFieldMutationTrigger(body);
          })
        );

        successAlert(
          `Custom field(s) successfully saved and added to this ${resourceType} form.`
        );
      } catch (e) {
        errorAlert(
          `One or more custom fields have failed to save, please try again.`
        );
        // eslint-disable-next-line no-console
        console.error(e);
      }
    },
    [
      definitionIdToCustomField,
      deleteCustomFieldMutationTrigger,
      errorAlert,
      resourceFidesKey,
      resourceType,
      sortedCustomFieldDefinitionIds,
      successAlert,
      upsertCustomFieldMutationTrigger,
    ]
  );

  return {
    definitionIdToCustomField,
    idToAllowListWithOptions,
    idToCustomFieldDefinition,
    isEnabled,
    isLoading,
    sortedCustomFieldDefinitionIds,
    upsertCustomFields,
  };
};
