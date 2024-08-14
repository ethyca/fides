import { ButtonSpinner, CheckIcon, HStack, ViewOffIcon } from "fidesui";
import { useState } from "react";

import { useAlert } from "~/features/common/hooks";
import { DiscoveryMonitorItem } from "~/features/data-discovery-and-detection/types/DiscoveryMonitorItem";
import { DiffStatus } from "~/types/api";

import ActionButton from "./ActionButton";
import {
  useMuteResourceMutation,
  usePromoteResourceMutation,
} from "./discovery-detection.slice";
import { StagedResourceType } from "./types/StagedResourceType";
import { findResourceType } from "./utils/findResourceType";

interface DiscoveryItemActionsProps {
  resource: DiscoveryMonitorItem;
}

const DiscoveryItemActions = ({ resource }: DiscoveryItemActionsProps) => {
  const resourceType = findResourceType(resource);
  const [promoteResourceMutation] = usePromoteResourceMutation();
  const [muteResourceMutation] = useMuteResourceMutation();

  const [isProcessingAction, setIsProcessingAction] = useState(false);

  const {
    diff_status: diffStatus,
    child_diff_statuses: childDiffStatus,
    // eslint-disable-next-line @typescript-eslint/naming-convention
    top_level_field_name,
  } = resource;

  const { successAlert } = useAlert();

  const isSubField = !!top_level_field_name;

  // No actions for database level or for nested field subfields
  if (resourceType === StagedResourceType.DATABASE) {
    return null;
  }

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
            setIsProcessingAction(true);
            await promoteResourceMutation({
              staged_resource_urn: resource.urn,
            });
            successAlert(
              `These changes have been added to a Fides dataset. To view, navigate to "Manage datasets".`,
              `Table changes confirmed`,
            );
            setIsProcessingAction(false);
          }}
          disabled={isProcessingAction}
        />
      )}
      {showMuteAction && (
        <ActionButton
          title="Ignore"
          icon={<ViewOffIcon />}
          onClick={async () => {
            setIsProcessingAction(true);
            await muteResourceMutation({
              staged_resource_urn: resource.urn,
            });
            setIsProcessingAction(false);
          }}
          disabled={isProcessingAction}
        />
      )}

      {isProcessingAction ? <ButtonSpinner position="static" /> : null}
    </HStack>
  );
};

export default DiscoveryItemActions;
