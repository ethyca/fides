import { CheckIcon, HStack, ViewOffIcon } from "fidesui";

import { useAlert } from "~/features/common/hooks";
import { DiscoveryMonitorItem } from "~/features/data-discovery-and-detection/types/DiscoveryMonitorItem";
import { DiffStatus } from "~/types/api";

import ActionButton from "../../ActionButton";
import {
  useMuteResourceMutation,
  usePromoteResourceMutation,
} from "../../discovery-detection.slice";

interface DiscoveryItemActionsProps {
  resource: DiscoveryMonitorItem;
}

const DiscoveryItemActionsCell = ({ resource }: DiscoveryItemActionsProps) => {
  const [promoteResourceMutation, { isLoading: promoteIsLoading }] =
    usePromoteResourceMutation();
  const [muteResourceMutation, { isLoading: muteIsLoading }] =
    useMuteResourceMutation();

  const anyActionIsLoading = promoteIsLoading || muteIsLoading;

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
    </HStack>
  );
};

export default DiscoveryItemActionsCell;
