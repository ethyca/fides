import { CheckIcon, HStack, RepeatIcon, ViewOffIcon } from "fidesui";

import { useAlert } from "~/features/common/hooks";
import { DiscoveryMonitorItem } from "~/features/data-discovery-and-detection/types/DiscoveryMonitorItem";
import getResourceName from "~/features/data-discovery-and-detection/utils/getResourceName";
import { DiffStatus } from "~/types/api";

import ActionButton from "../../ActionButton";
import {
  useConfirmResourceMutation,
  useMuteResourceMutation,
  usePromoteResourceMutation,
} from "../../discovery-detection.slice";

interface DiscoveryItemActionsProps {
  resource: DiscoveryMonitorItem;
}

const DiscoveryItemActionsCell = ({ resource }: DiscoveryItemActionsProps) => {
  const [confirmResourceMutation, { isLoading: confirmIsLoading }] =
    useConfirmResourceMutation();
  const [promoteResourceMutation, { isLoading: promoteIsLoading }] =
    usePromoteResourceMutation();
  const [muteResourceMutation, { isLoading: muteIsLoading }] =
    useMuteResourceMutation();

  const anyActionIsLoading =
    promoteIsLoading || muteIsLoading || confirmIsLoading;

  const {
    diff_status: diffStatus,
    child_diff_statuses: childDiffStatus,
    // eslint-disable-next-line @typescript-eslint/naming-convention
    top_level_field_name,
  } = resource;

  const { successAlert } = useAlert();

  const isSubField = !!top_level_field_name;

  const itemHasClassificationChanges =
    diffStatus === DiffStatus.CLASSIFICATION_ADDITION ||
    diffStatus === DiffStatus.CLASSIFICATION_UPDATE;

  const childItemsHaveClassificationChanges =
    childDiffStatus &&
    (childDiffStatus[DiffStatus.CLASSIFICATION_ADDITION] ||
      childDiffStatus[DiffStatus.CLASSIFICATION_UPDATE]);

  const showPromoteAction =
    (itemHasClassificationChanges || childItemsHaveClassificationChanges) &&
    !isSubField;

  const showMuteAction =
    itemHasClassificationChanges || childItemsHaveClassificationChanges;

  return (
    <HStack onClick={(e) => e.stopPropagation()}>
      {showPromoteAction && (
        <ActionButton
          title="Confirm"
          icon={<CheckIcon />}
          onClick={async () => {
            await promoteResourceMutation({
              staged_resource_urn: resource.urn,
            });
            successAlert(
              `These changes have been added to a Fides dataset. To view, navigate to "Manage datasets".`,
              `Table changes confirmed`,
            );
          }}
          disabled={anyActionIsLoading}
          loading={promoteIsLoading}
        />
      )}
      {showMuteAction && (
        <ActionButton
          title="Ignore"
          icon={<ViewOffIcon />}
          onClick={async () => {
            await muteResourceMutation({
              staged_resource_urn: resource.urn,
            });
            successAlert(
              `Ignored changes will not be added to a Fides dataset.`,
              `${resource.name || "Changes"} ignored`,
            );
          }}
          disabled={anyActionIsLoading}
          loading={muteIsLoading}
        />
      )}
      <ActionButton
        title="Reclassify"
        icon={<RepeatIcon />}
        onClick={async () => {
          await confirmResourceMutation({
            staged_resource_urn: resource.urn,
            monitor_config_id: resource.monitor_config_id!,
            start_classification: true,
            classify_monitored_resources: true,
          });
          successAlert(
            `Reclassification of ${getResourceName(resource) || "the resource"} has begun.  The results may take some time to appear in the “Data discovery“ tab.`,
            `Reclassification started`,
          );
        }}
        disabled={anyActionIsLoading}
        loading={confirmIsLoading}
      />
    </HStack>
  );
};

export default DiscoveryItemActionsCell;
