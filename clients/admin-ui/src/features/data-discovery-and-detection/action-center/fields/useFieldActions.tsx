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

export const useFieldActions = (monitorId: string) => {
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
  };

  return {
    mute: handleIgnore,
    promote: handlePromote,
    "un-mute": handleUnMute,
    classify: handleClassifyStagedResources,
    "assign-categories": handleSetDataCategories,
    approve: handleApprove,
  } satisfies Record<
    FieldActionType,
    (urns: string[], field?: Partial<Field>) => Promise<void> | void
  >;
};
