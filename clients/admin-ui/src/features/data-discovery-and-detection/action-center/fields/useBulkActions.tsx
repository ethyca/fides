import { useAntModal, useMessage } from "fidesui";

import { pluralize } from "~/features/common/utils";
import { FieldActionType } from "~/types/api/models/FieldActionType";
import { isErrorResult } from "~/types/errors";

import {
  FIELD_ACTION_CONFIRMATION_MESSAGE,
  FIELD_ACTION_INTERMEDIATE,
  FIELD_ACTION_LABEL,
} from "./FieldActions.const";
import { useFieldActionsMutation } from "./monitor-fields.slice";
import { MonitorFieldParameters } from "./types";
import {
  getActionErrorMessage,
  getActionModalProps,
  getActionSuccessMessage,
} from "./utils";

export const useBulkActions = (
  monitorId: string,
  onRefreshTree?: (urns: string[]) => Promise<void>,
) => {
  const [bulkAction] = useFieldActionsMutation();

  const messageApi = useMessage();
  const modalApi = useAntModal();

  const handleBulkAction =
    (actionType: FieldActionType) =>
    async (
      filterParams: MonitorFieldParameters,
      excluded_resource_urns: string[],
      targetItemCount: number,
    ) => {
      const key = Date.now();
      const confirmed = await modalApi.confirm(
        getActionModalProps(
          FIELD_ACTION_LABEL[actionType],
          FIELD_ACTION_CONFIRMATION_MESSAGE[actionType](targetItemCount),
        ),
      );

      if (!confirmed) {
        return;
      }

      messageApi.open({
        key,
        type: "loading",
        content: `${FIELD_ACTION_INTERMEDIATE[actionType]} ${targetItemCount} ${pluralize(targetItemCount, "resource", "resources")}...`,
        duration: 0,
      });

      const mutationResult = await bulkAction({
        query: {
          ...filterParams.query,
        },
        path: {
          monitor_config_id: monitorId,
          action_type: actionType,
        },
        body: {
          excluded_resource_urns,
        },
      });

      if (isErrorResult(mutationResult)) {
        messageApi.open({
          key,
          type: "error",
          content: getActionErrorMessage(actionType),
          duration: 5,
        });

        return;
      }

      messageApi.open({
        key,
        type: "success",
        content: getActionSuccessMessage(actionType, targetItemCount),
        duration: 5,
      });

      // Refresh the tree to reflect updated status
      // Note: For bulk actions we can't get the specific URNs affected,
      // so we pass the staged_resource_urn filter if available.
      // If the action is REVIEW, the indicators are not refreshed because the
      // resource reviewed by the review action had already been classified,
      // and its parent already had the "change" indicator.
      if (onRefreshTree && actionType !== FieldActionType.REVIEW) {
        const resources = filterParams.query.staged_resource_urn || [];
        await onRefreshTree(resources);
      }
    };

  return {
    "assign-categories": handleBulkAction(FieldActionType.ASSIGN_CATEGORIES),
    "promote-removals": handleBulkAction(FieldActionType.PROMOTE_REMOVALS),
    "un-review": handleBulkAction(FieldActionType.UN_REVIEW),
    "un-mute": handleBulkAction(FieldActionType.UN_MUTE),
    review: handleBulkAction(FieldActionType.REVIEW),
    classify: handleBulkAction(FieldActionType.CLASSIFY),
    mute: handleBulkAction(FieldActionType.MUTE),
    promote: handleBulkAction(FieldActionType.PROMOTE),
  } satisfies Record<
    FieldActionType,
    | null
    | ((
        filterParams: MonitorFieldParameters,
        excluded_resource_urns: string[],
        targetItemCount: number,
      ) => Promise<void> | void)
  >;
};
