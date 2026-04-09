import { useCallback, useMemo } from "react";

import { useGetConnectionConfigDatasetConfigsQuery } from "~/features/datastore-connections";
import {
  useBulkAssignPropertiesMutation,
  useBulkRemovePropertiesMutation,
  useGetPropertyIdsForDatasetQuery,
} from "~/features/properties/dataset-properties.slice";
import { useGetAllPropertiesQuery } from "~/features/properties/property.slice";

/**
 * Hook that manages property assignments for an integration's dataset configs.
 *
 * Returns property options for a select, the initial property IDs, and a
 * `savePropertyAssignments` function to call on form submit with the new set
 * of selected property IDs.
 */
export const useIntegrationPropertySelect = (
  connectionKey: string | undefined,
) => {
  // Fetch dataset configs for this connection
  const { data: datasetConfigsPage } =
    useGetConnectionConfigDatasetConfigsQuery(connectionKey!, {
      skip: !connectionKey,
    });

  const datasetFidesKeys = useMemo(
    () => datasetConfigsPage?.items?.map((dc) => dc.fides_key) ?? [],
    [datasetConfigsPage],
  );

  // Fetch property IDs for the first dataset config (they should all share the
  // same property assignments since we bulk-assign across all of them).
  const primaryFidesKey = datasetFidesKeys[0];
  const { data: propertyIdsData, isLoading: isLoadingPropertyIds } =
    useGetPropertyIdsForDatasetQuery(primaryFidesKey!, {
      skip: !primaryFidesKey,
    });

  const initialPropertyIds = useMemo(
    () => propertyIdsData?.property_ids ?? [],
    [propertyIdsData],
  );

  // Fetch all properties for the dropdown options
  const { data: propertiesPage, isLoading: isLoadingProperties } =
    useGetAllPropertiesQuery({ size: 500 });

  const propertyOptions = useMemo(
    () =>
      propertiesPage?.items?.map((p) => ({
        label: p.name,
        value: p.id!,
      })) ?? [],
    [propertiesPage],
  );

  // Mutations
  const [bulkAssign] = useBulkAssignPropertiesMutation();
  const [bulkRemove] = useBulkRemovePropertiesMutation();

  /**
   * Call on form submit with the current set of selected property IDs.
   * Computes the diff against the initial state and issues bulk-assign/remove.
   */
  const savePropertyAssignments = useCallback(
    async (selectedPropertyIds: string[]) => {
      if (datasetFidesKeys.length === 0) {
        return;
      }

      const initial = new Set(initialPropertyIds);
      const selected = new Set(selectedPropertyIds);

      const toAssign = selectedPropertyIds.filter((id) => !initial.has(id));
      const toRemove = initialPropertyIds.filter((id) => !selected.has(id));

      const promises: Promise<unknown>[] = [];

      if (toAssign.length > 0) {
        promises.push(
          bulkAssign({
            dataset_config_ids: datasetFidesKeys,
            property_ids: toAssign,
          }).unwrap(),
        );
      }

      if (toRemove.length > 0) {
        promises.push(
          bulkRemove({
            dataset_config_ids: datasetFidesKeys,
            property_ids: toRemove,
          }).unwrap(),
        );
      }

      await Promise.all(promises);
    },
    [datasetFidesKeys, initialPropertyIds, bulkAssign, bulkRemove],
  );

  return {
    propertyOptions,
    initialPropertyIds,
    savePropertyAssignments,
    hasDatasets: datasetFidesKeys.length > 0,
    isLoading: isLoadingPropertyIds || isLoadingProperties,
  };
};
