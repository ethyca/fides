import { useChakraToast as useToast } from "fidesui";
import { useCallback } from "react";

import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import { StagedResourceAPIResponse } from "~/types/api";

import {
  useBulkMuteIdentityProviderMonitorResultsMutation,
  useBulkPromoteIdentityProviderMonitorResultsMutation,
  useBulkUnmuteIdentityProviderMonitorResultsMutation,
} from "../../discovery-detection.slice";
import { InfrastructureSystemBulkActionType } from "../constants";

interface UseInfrastructureSystemsBulkActionsConfig {
  monitorId: string;
  getRecordKey: (item: StagedResourceAPIResponse) => string;
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
      selectedItems: StagedResourceAPIResponse[],
    ) => {
      // Extract URNs from selected items
      const urns = selectedItems.map((item) => item.urn);

      if (urns.length === 0) {
        toast(
          errorToastParams(
            "No valid systems selected. Please select systems with URNs.",
          ),
        );
        return;
      }

      let result;
      let successMessage: string;

      if (action === InfrastructureSystemBulkActionType.ADD) {
        result = await bulkPromoteIdentityProviderMonitorResultsMutation({
          monitor_config_key: monitorId,
          urns,
        });
        const count = urns.length;
        successMessage = `${count} system${count > 1 ? "s" : ""} ${count > 1 ? "have" : "has"} been promoted to the system inventory.`;
      } else if (action === InfrastructureSystemBulkActionType.IGNORE) {
        result = await bulkMuteIdentityProviderMonitorResultsMutation({
          monitor_config_key: monitorId,
          urns,
        });
        const count = urns.length;
        successMessage = `${count} system${count > 1 ? "s" : ""} ${count > 1 ? "have" : "has"} been ignored.`;
      } else if (action === InfrastructureSystemBulkActionType.RESTORE) {
        result = await bulkUnmuteIdentityProviderMonitorResultsMutation({
          monitor_config_key: monitorId,
          urns,
        });
        const count = urns.length;
        successMessage = `${count} system${count > 1 ? "s" : ""} ${count > 1 ? "have" : "has"} been restored.`;
      } else {
        return;
      }

      if (isErrorResult(result)) {
        toast(errorToastParams(getErrorMessage(result.error)));
      } else {
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
