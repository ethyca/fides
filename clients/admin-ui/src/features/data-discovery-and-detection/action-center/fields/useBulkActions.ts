import { useToast } from "fidesui";

import { getErrorMessage } from "~/features/common/helpers";
import { useAlert } from "~/features/common/hooks";
import { successToastParams } from "~/features/common/toast";
import { FieldActionType } from "~/types/api/models/FieldActionType";
import { isErrorResult } from "~/types/errors";

import { FIELD_ACTION_LABEL } from "./FieldActions.const";
import { useFieldActionsMutation } from "./monitor-fields.slice";
import { MonitorFieldParameters } from "./types";

export const useBulkActions = (
  monitorId: string,
  onRefreshTree?: (urns: string[]) => Promise<void>,
) => {
  const [bulkAction] = useFieldActionsMutation();

  const toast = useToast();
  const { errorAlert } = useAlert();

  const handleBulkAction =
    (actionType: FieldActionType) =>
    async (filterParams: MonitorFieldParameters) => {
      const mutationResult = await bulkAction({
        query: {
          ...filterParams.query,
        },
        path: {
          monitor_config_id: monitorId,
          action_type: actionType,
        },
      });

      if (isErrorResult(mutationResult)) {
        errorAlert(getErrorMessage(mutationResult.error));
        return;
      }

      const actionItemCount = mutationResult.data.task_ids?.length ?? 0;
      toast(
        successToastParams(
          `Successful ${FIELD_ACTION_LABEL[actionType]} action for ${actionItemCount} item${actionItemCount !== 1 ? "s" : ""}`,
        ),
      );

      // Refresh the tree to reflect updated status
      // Note: For bulk actions we can't get the specific URNs affected,
      // so we pass the staged_resource_urn filter if available.
      // If the action is APPROVE, the indicators are not refreshed because the
      // resource approved by the approve action had already been classified,
      // and its parent already had the "change" indicator.
      if (onRefreshTree && actionType !== FieldActionType.APPROVE) {
        const resources = filterParams.query.staged_resource_urn || [];
        await onRefreshTree(resources);
      }
    };

  return {
    "assign-categories": handleBulkAction(FieldActionType.ASSIGN_CATEGORIES),
    "promote-removals": handleBulkAction(FieldActionType.PROMOTE_REMOVALS),
    "un-approve": handleBulkAction(FieldActionType.UN_APPROVE),
    "un-mute": handleBulkAction(FieldActionType.UN_MUTE),
    approve: handleBulkAction(FieldActionType.APPROVE),
    classify: handleBulkAction(FieldActionType.CLASSIFY),
    mute: handleBulkAction(FieldActionType.MUTE),
    promote: handleBulkAction(FieldActionType.PROMOTE),
  } satisfies Record<
    FieldActionType,
    null | ((filterParams: MonitorFieldParameters) => Promise<void> | void)
  >;
};
