import { useToast } from "fidesui";

import { getErrorMessage } from "~/features/common/helpers";
import { useAlert } from "~/features/common/hooks";
import { successToastParams } from "~/features/common/toast";
import { FieldActionType } from "~/types/api/models/FieldActionType";
import { isErrorResult } from "~/types/errors";

import { FIELD_ACTION_LABEL } from "./FieldActions.const";
import { useFieldActionsMutation } from "./monitor-fields.slice";
import { MonitorFieldParameters } from "./types";

export const useBulkActions = (monitorId: string) => {
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
    };

  return {
    mute: handleBulkAction(FieldActionType.MUTE),
    promote: handleBulkAction(FieldActionType.PROMOTE),
    "un-mute": handleBulkAction(FieldActionType.UN_MUTE),
    classify: handleBulkAction(FieldActionType.CLASSIFY),
    "assign-categories": handleBulkAction(FieldActionType.ASSIGN_CATEGORIES),
    approve: handleBulkAction(FieldActionType.APPROVE),
  } satisfies Record<
    FieldActionType,
    null | ((filterParams: MonitorFieldParameters) => Promise<void> | void)
  >;
};
