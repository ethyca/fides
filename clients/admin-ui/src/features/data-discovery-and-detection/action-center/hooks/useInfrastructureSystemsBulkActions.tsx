import { useChakraToast as useToast } from "fidesui";
import { useCallback } from "react";

import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import { StagedResourceAPIResponse } from "~/types/api";
import { DiffStatus } from "~/types/api/models/DiffStatus";

import {
  useBulkMuteIdentityProviderMonitorResultsMutation,
  useBulkPromoteIdentityProviderMonitorResultsMutation,
  useBulkUnmuteIdentityProviderMonitorResultsMutation,
} from "../../discovery-detection.slice";
import { InfrastructureSystemBulkActionType } from "../constants";

interface InfrastructureSystemsFilters {
  search?: string;
  diff_status?: DiffStatus | DiffStatus[];
  vendor_id?: string | string[];
  data_uses?: string[];
}

interface UseInfrastructureSystemsBulkActionsConfig {
  monitorId: string;
  onSuccess?: () => void;
}

export const useInfrastructureSystemsBulkActions = ({
  monitorId,
  onSuccess,
}: UseInfrastructureSystemsBulkActionsConfig) => {
  const toast = useToast();

  const [
    bulkPromoteIdentityProviderMonitorResultsMutation,
    { isLoading: isBulkPromoting },
  ] = useBulkPromoteIdentityProviderMonitorResultsMutation();

  const [
    bulkMuteIdentityProviderMonitorResultsMutation,
    { isLoading: isBulkMuting },
  ] = useBulkMuteIdentityProviderMonitorResultsMutation();

  const [
    bulkUnmuteIdentityProviderMonitorResultsMutation,
    { isLoading: isBulkUnmuting },
  ] = useBulkUnmuteIdentityProviderMonitorResultsMutation();

  const isBulkActionInProgress =
    isBulkPromoting || isBulkMuting || isBulkUnmuting;

  const handleBulkAction = useCallback(
    async (
      action: InfrastructureSystemBulkActionType,
      selectionData:
        | {
            mode: "explicit";
            selectedItems: StagedResourceAPIResponse[];
          }
        | {
            mode: "all";
            filters: InfrastructureSystemsFilters;
            excludeUrns: string[];
          },
    ) => {
      let result;
      let successMessage: string;
      let count: number;

      if (selectionData.mode === "explicit") {
        // Extract URNs from selected items
        const urns = selectionData.selectedItems
          .map((item) => item.urn)
          .filter((urn): urn is string => Boolean(urn));

        if (urns.length === 0) {
          toast(
            errorToastParams(
              "No valid systems selected. Please select systems with URNs.",
            ),
          );
          return;
        }

        count = urns.length;

        if (action === InfrastructureSystemBulkActionType.ADD) {
          result = await bulkPromoteIdentityProviderMonitorResultsMutation({
            monitor_config_key: monitorId,
            urns,
          });
        } else if (action === InfrastructureSystemBulkActionType.IGNORE) {
          result = await bulkMuteIdentityProviderMonitorResultsMutation({
            monitor_config_key: monitorId,
            urns,
          });
        } else if (action === InfrastructureSystemBulkActionType.RESTORE) {
          result = await bulkUnmuteIdentityProviderMonitorResultsMutation({
            monitor_config_key: monitorId,
            urns,
          });
        } else {
          return;
        }
      } else {
        // Filter-based selection (select all with exclusions)
        const { filters, excludeUrns } = selectionData;

        // Build filter payload - only include non-empty filters
        const filterPayload: {
          search?: string;
          diff_status?: DiffStatus | DiffStatus[];
          vendor_id?: string | string[];
          data_uses?: string[];
        } = {};

        if (filters.search) {
          filterPayload.search = filters.search;
        }
        if (filters.diff_status) {
          filterPayload.diff_status = filters.diff_status;
        }
        if (filters.vendor_id) {
          filterPayload.vendor_id = filters.vendor_id;
        }
        if (filters.data_uses) {
          filterPayload.data_uses = filters.data_uses;
        }

        // If all filters are empty, use empty object to match all
        const hasFilters = Object.keys(filterPayload).length > 0;

        const bulkSelectionPayload = hasFilters
          ? {
              filters: filterPayload,
              exclude_urns: excludeUrns.length > 0 ? excludeUrns : undefined,
            }
          : {
              filters: {},
              exclude_urns: excludeUrns.length > 0 ? excludeUrns : undefined,
            };

        // We don't know the exact count until the backend processes it
        // Use a placeholder that will be updated from the response
        count = 0;

        if (action === InfrastructureSystemBulkActionType.ADD) {
          result = await bulkPromoteIdentityProviderMonitorResultsMutation({
            monitor_config_key: monitorId,
            bulkSelection: bulkSelectionPayload,
          });
        } else if (action === InfrastructureSystemBulkActionType.IGNORE) {
          result = await bulkMuteIdentityProviderMonitorResultsMutation({
            monitor_config_key: monitorId,
            bulkSelection: bulkSelectionPayload,
          });
        } else if (action === InfrastructureSystemBulkActionType.RESTORE) {
          result = await bulkUnmuteIdentityProviderMonitorResultsMutation({
            monitor_config_key: monitorId,
            bulkSelection: bulkSelectionPayload,
          });
        } else {
          return;
        }

        // Extract count from response if available
        if (!isErrorResult(result) && result.data) {
          const responseData = result.data as any;
          if (responseData.summary?.successful !== undefined) {
            count = responseData.summary.successful;
          } else if (responseData.summary?.total_requested !== undefined) {
            count = responseData.summary.total_requested;
          }
        }
      }

      if (isErrorResult(result)) {
        toast(errorToastParams(getErrorMessage(result.error)));
      } else {
        // Use count from response if available, otherwise use estimated count
        const finalCount =
          count > 0
            ? count
            : selectionData.mode === "explicit"
              ? selectionData.selectedItems.length
              : 0;

        if (action === InfrastructureSystemBulkActionType.ADD) {
          successMessage = `${finalCount} system${finalCount > 1 ? "s" : ""} ${finalCount > 1 ? "have" : "has"} been promoted to the system inventory.`;
        } else if (action === InfrastructureSystemBulkActionType.IGNORE) {
          successMessage = `${finalCount} system${finalCount > 1 ? "s" : ""} ${finalCount > 1 ? "have" : "has"} been ignored.`;
        } else if (action === InfrastructureSystemBulkActionType.RESTORE) {
          successMessage = `${finalCount} system${finalCount > 1 ? "s" : ""} ${finalCount > 1 ? "have" : "has"} been restored.`;
        } else {
          return;
        }

        toast(successToastParams(successMessage));
        onSuccess?.();
      }
    },
    [
      monitorId,
      bulkPromoteIdentityProviderMonitorResultsMutation,
      bulkMuteIdentityProviderMonitorResultsMutation,
      bulkUnmuteIdentityProviderMonitorResultsMutation,
      toast,
      onSuccess,
    ],
  );

  return {
    handleBulkAction,
    isBulkActionInProgress,
  };
};
