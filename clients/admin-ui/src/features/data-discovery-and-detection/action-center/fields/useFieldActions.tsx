import { useToast } from "fidesui";
import _ from "lodash";

import { getErrorMessage } from "~/features/common/helpers";
import { useAlert } from "~/features/common/hooks";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import { useClassifyStagedResourcesMutation } from "~/features/data-discovery-and-detection/action-center/action-center.slice";
import {
  useApproveStagedResourcesMutation,
  useMuteResourcesMutation,
  usePromoteResourcesMutation,
  useUnmuteResourcesMutation,
  useUpdateResourceCategoryMutation,
} from "~/features/data-discovery-and-detection/discovery-detection.slice";
import { Field } from "~/types/api";
import { FieldActionType } from "~/types/api/models/FieldActionType";
import { isErrorResult } from "~/types/errors";

import { AVAILABLE_ACTIONS, FIELD_ACTION_LABEL } from "./FieldActions.const";
import { ResourceStatusLabel } from "./MonitorFields.const";

export const getAvailableActions = (statusList: ResourceStatusLabel[]) => {
  const [init, ...availableActions] = statusList.map(
    (status) => AVAILABLE_ACTIONS[status],
  );

  return availableActions.reduce<Readonly<Array<FieldActionType>>>(
    (acc, current) => _.intersection(acc, [...current]),
    init ?? ([] as Readonly<FieldActionType[]>),
  );
};

export const useFieldActions = (
  monitorId: string,
  onRefreshTree?: (urns: string[]) => Promise<void>,
) => {
  const [ignoreMonitorResultAssetsMutation] = useMuteResourcesMutation();
  const [unMuteMonitorResultAssetsMutation] = useUnmuteResourcesMutation();

  const [classifyStagedResourcesMutation] =
    useClassifyStagedResourcesMutation();
  const [updateResourcesCategoryMutation] = useUpdateResourceCategoryMutation();
  const [promoteResourcesMutation] = usePromoteResourcesMutation();
  const [approveStagedResourcesMutation] = useApproveStagedResourcesMutation();

  const toast = useToast();
  const { errorAlert } = useAlert();

  const toastSuccess = (actionType: FieldActionType, itemCount: number) =>
    toast(
      successToastParams(
        `Successful ${FIELD_ACTION_LABEL[actionType]} action for ${itemCount} item${itemCount !== 1 ? "s" : ""}`,
      ),
    );

  const handleIgnore = async (urns: string[]) => {
    const mutationResult = await ignoreMonitorResultAssetsMutation({
      staged_resource_urns: urns,
    });

    if (isErrorResult(mutationResult)) {
      errorAlert(getErrorMessage(mutationResult.error));
      return;
    }

    toastSuccess(FieldActionType.MUTE, urns.length);

    // Refresh the tree to reflect updated status
    // An indicator may change to empty if there are no child resources that the user is expected to act upon.
    if (onRefreshTree) {
      await onRefreshTree(urns);
    }
  };

  const handleUnMute = async (urns: string[]) => {
    const mutationResult = await unMuteMonitorResultAssetsMutation({
      staged_resource_urns: urns,
    });

    if (isErrorResult(mutationResult)) {
      errorAlert(getErrorMessage(mutationResult.error));
      return;
    }

    toastSuccess(FieldActionType.UN_MUTE, urns.length);

    // Refresh the tree to reflect updated status
    // An indicator can change to "addition" or "change" since the user could now act on its unmuted children
    if (onRefreshTree) {
      await onRefreshTree(urns);
    }
  };

  const handlePromote = async (urns: string[]) => {
    const mutationResult = await promoteResourcesMutation({
      staged_resource_urns: urns,
    });

    if (isErrorResult(mutationResult)) {
      errorAlert(getErrorMessage(mutationResult.error));
      return;
    }

    toastSuccess(FieldActionType.PROMOTE, urns.length);

    // Refresh the tree to reflect updated status
    // An indicator can change to empty if all its children were promoted.
    if (onRefreshTree) {
      await onRefreshTree(urns);
    }
  };

  const handleClassifyStagedResources = async (urns: string[]) => {
    const result = await classifyStagedResourcesMutation({
      monitor_config_key: monitorId,
      staged_resource_urns: urns,
    });

    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
      return;
    }

    toastSuccess(FieldActionType.CLASSIFY, urns.length);

    // Refresh the tree to reflect updated status
    // The indicators of the parents of affected children may change to "change" if it was not already in that state.
    if (onRefreshTree) {
      await onRefreshTree(urns);
    }
  };

  const handleSetDataCategories = async (
    urns: string[],
    field?: Partial<Field>,
  ) => {
    const [urn] = urns;
    const mutationResult = await updateResourcesCategoryMutation({
      monitor_config_id: monitorId,
      staged_resource_urn: urn,
      user_assigned_data_categories:
        field?.user_assigned_data_categories ?? undefined,
    });

    if (isErrorResult(mutationResult)) {
      errorAlert(getErrorMessage(mutationResult.error));
      return;
    }

    toastSuccess(FieldActionType.ASSIGN_CATEGORIES, urns.length);

    // Refresh the tree to reflect updated status
    // The indicators for the parents of affected children may change to "change" if all of their children were additions.
    if (onRefreshTree) {
      await onRefreshTree(urns);
    }
  };

  const handleApprove = async (urns: string[]) => {
    const mutationResult = await approveStagedResourcesMutation({
      monitor_config_key: monitorId,
      staged_resource_urns: urns,
    });

    if (isErrorResult(mutationResult)) {
      errorAlert(getErrorMessage(mutationResult.error));
      return;
    }

    toastSuccess(FieldActionType.APPROVE, urns.length);

    // The indicators are not refreshed because the resource approved by the approve action had already been classified,
    // and its parent already had the "change" indicator.
  };

  return {
    "assign-categories": handleSetDataCategories,
    "promote-removals": () => {},
    "un-approve": () => {},
    "un-mute": handleUnMute,
    approve: handleApprove,
    classify: handleClassifyStagedResources,
    mute: handleIgnore,
    promote: handlePromote,
  } satisfies Record<
    FieldActionType,
    (urns: string[], field?: Partial<Field>) => Promise<void> | void
  >;
};
