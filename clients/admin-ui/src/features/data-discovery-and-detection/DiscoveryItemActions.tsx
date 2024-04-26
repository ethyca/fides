import { ButtonSpinner, CheckIcon, HStack } from "@fidesui/react";
import { useState } from "react";

import { StagedResource } from "~/types/api";
import ActionButton from "./ActionButton";
import { findResourceType } from "./utils/findResourceType";

import { usePromoteResourceMutation } from "./discovery-detection.slice";
import { StagedResourceType } from "./types/StagedResourceType";

interface DiscoveryItemActionsProps {
  resource: StagedResource;
}

const DiscoveryItemActions: React.FC<DiscoveryItemActionsProps> = ({
  resource,
}) => {
  const resourceType = findResourceType(resource);
  const [promoteResourceMutation] = usePromoteResourceMutation();

  const [isProcessingAction, setIsProcessingAction] = useState(false);

  const {} = resource;

  // No actions for database level
  if (resourceType === StagedResourceType.DATABASE) {
    return null;
  }

  const showPromoteAction = true;

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

      {isProcessingAction ? <ButtonSpinner position="static" /> : null}
    </HStack>
  );
};

export default DiscoveryItemActions;
