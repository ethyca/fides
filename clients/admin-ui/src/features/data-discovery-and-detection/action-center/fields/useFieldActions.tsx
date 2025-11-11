import { AntMessage as Message, AntModal as Modal } from "fidesui";
import _ from "lodash";

import { pluralize } from "~/features/common/utils";
import { useClassifyStagedResourcesMutation } from "~/features/data-discovery-and-detection/action-center/action-center.slice";
import {
  useApproveStagedResourcesMutation,
  useMuteResourcesMutation,
  usePromoteResourcesMutation,
  useUnmuteResourcesMutation,
  useUpdateResourceCategoryMutation,
} from "~/features/data-discovery-and-detection/discovery-detection.slice";
import { DiffStatus, Field } from "~/types/api";
import { FieldActionType } from "~/types/api/models/FieldActionType";
import { isErrorResult, RTKResult } from "~/types/errors";

import {
  ACTION_ALLOWED_STATUSES,
  FIELD_ACTION_CONFIRMATION_MESSAGE,
  FIELD_ACTION_INTERMEDIATE,
  FIELD_ACTION_LABEL,
} from "./FieldActions.const";
import {
  getActionErrorMessage,
  getActionModalProps,
  getActionSuccessMessage,
} from "./utils";

export const getAvailableActions = (statusList: DiffStatus[]) => {
  const [init, ...availableActions] = statusList.map((status) =>
    Object.values(FieldActionType).flatMap((actionType) =>
      ACTION_ALLOWED_STATUSES[actionType].some((s) => s === status)
        ? [actionType]
        : [],
    ),
  );

  return availableActions.reduce<Readonly<Array<FieldActionType>>>(
    (acc, current) => _.intersection(acc, [...current]),
    init ?? ([] as Readonly<FieldActionType[]>),
  );
};

export const useFieldActions = (
  monitorId: string,
  modalApi: ReturnType<typeof Modal.useModal>[0],
  messageApi: ReturnType<typeof Message.useMessage>[0],
  onRefreshTree?: (urns: string[]) => Promise<void>,
) => {
  const [approveStagedResourcesMutation] = useApproveStagedResourcesMutation();
  const [classifyStagedResourcesMutation] =
    useClassifyStagedResourcesMutation();
  const [ignoreMonitorResultAssetsMutation] = useMuteResourcesMutation();
  const [promoteResourcesMutation] = usePromoteResourcesMutation();
  const [unMuteMonitorResultAssetsMutation] = useUnmuteResourcesMutation();
  const [updateResourcesCategoryMutation] = useUpdateResourceCategoryMutation();

  const handleAction =
    (
      actionType: FieldActionType,
      mutationFn: (
        urns: string[],
        field?: Partial<Field>,
      ) => Promise<RTKResult>,
    ) =>
    async (urns: string[], field?: Partial<Field>) => {
      const key = Date.now();
      const confirmed =
        urns.length === 1 ||
        (await modalApi.confirm(
          getActionModalProps(
            FIELD_ACTION_LABEL[actionType],
            FIELD_ACTION_CONFIRMATION_MESSAGE[actionType](urns.length),
          ),
        ));

      if (!confirmed) {
        return;
      }

      messageApi.open({
        key,
        type: "loading",
        content: `${FIELD_ACTION_INTERMEDIATE[actionType]} ${urns.length} ${pluralize(urns.length, "resource", "resources")}...`,
        duration: 0,
      });

      const result = await mutationFn(urns, field);

      if (isErrorResult(result)) {
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
        content: getActionSuccessMessage(actionType, urns.length),
        duration: 5,
      });

      // Refresh the tree to reflect updated status
      // An indicator may change to empty if there are no child resources that the user is expected to act upon.
      if (onRefreshTree) {
        await onRefreshTree(urns);
      }
    };

  const handleIgnore = async (urns: string[]) => {
    return ignoreMonitorResultAssetsMutation({
      staged_resource_urns: urns,
    });
  };

  const handleUnMute = async (urns: string[]) => {
    return unMuteMonitorResultAssetsMutation({
      staged_resource_urns: urns,
    });
  };

  const handlePromote = async (urns: string[]) => {
    return promoteResourcesMutation({
      staged_resource_urns: urns,
    });
  };

  const handleClassifyStagedResources = async (urns: string[]) => {
    return classifyStagedResourcesMutation({
      monitor_config_key: monitorId,
      staged_resource_urns: urns,
    });
  };

  const handleSetDataCategories = async (
    urns: string[],
    field?: Partial<Field>,
  ) => {
    const [urn] = urns;
    return updateResourcesCategoryMutation({
      monitor_config_id: monitorId,
      staged_resource_urn: urn,
      user_assigned_data_categories:
        field?.user_assigned_data_categories ?? undefined,
    });
  };

  const handleApprove = async (urns: string[]) => {
    return approveStagedResourcesMutation({
      monitor_config_key: monitorId,
      staged_resource_urns: urns,
    });
  };

  return {
    "assign-categories": handleAction(
      FieldActionType.ASSIGN_CATEGORIES,
      handleSetDataCategories,
    ),
    "promote-removals": () => {},
    "un-approve": () => {},
    "un-mute": handleAction(FieldActionType.UN_MUTE, handleUnMute),
    approve: handleAction(FieldActionType.APPROVE, handleApprove),
    classify: handleAction(
      FieldActionType.CLASSIFY,
      handleClassifyStagedResources,
    ),
    mute: handleAction(FieldActionType.MUTE, handleIgnore),
    promote: handleAction(FieldActionType.PROMOTE, handlePromote),
  } satisfies Record<
    FieldActionType,
    (urns: string[], field?: Partial<Field>) => Promise<void> | void
  >;
};
