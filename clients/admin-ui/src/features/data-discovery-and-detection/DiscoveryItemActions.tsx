import { ButtonSpinner, CheckIcon, HStack, ViewOffIcon } from "fidesui";
import { useState } from "react";

import { TOP_LEVEL_FIELD_URN_LENGTH } from "~/features/data-discovery-and-detection/utils/isNestedField";
import { DiffStatus, StagedResource } from "~/types/api";

import ActionButton from "./ActionButton";
import {
  useMuteResourceMutation,
  usePromoteResourceMutation,
} from "./discovery-detection.slice";
import { StagedResourceType } from "./types/StagedResourceType";
import { findResourceType } from "./utils/findResourceType";

interface DiscoveryItemActionsProps {
  resource: StagedResource;
}

const DiscoveryItemActions = ({ resource }: DiscoveryItemActionsProps) => {
  const resourceType = findResourceType(resource);
  const [promoteResourceMutation] = usePromoteResourceMutation();
  const [muteResourceMutation] = useMuteResourceMutation();

  const [isProcessingAction, setIsProcessingAction] = useState(false);

  const {
    diff_status: diffStatus,
    child_diff_statuses: childDiffStatus,
    urn,
  } = resource;

  const isSubField = urn.split(".").length > TOP_LEVEL_FIELD_URN_LENGTH;

  // No actions for database level or for nested field subfields
  if (resourceType === StagedResourceType.DATABASE || isSubField) {
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
    itemHasClassificationChanges || childItemsHaveClassificationChanges;

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
