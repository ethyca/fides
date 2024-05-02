import { ButtonGroup, CheckIcon, Flex, ViewOffIcon } from "@fidesui/react";

import ActionButton from "~/features/data-discovery-and-detection/ActionButton";
import {
  useMuteResourceMutation,
  usePromoteResourceMutation,
} from "~/features/data-discovery-and-detection/discovery-detection.slice";
import { StagedResourceType } from "~/features/data-discovery-and-detection/types/StagedResourceType";

const DiscoveryBulkActions = ({
  resourceType,
  resourceUrn,
}: {
  resourceType: StagedResourceType;
  resourceUrn: string;
}) => {
  const [promoteResourceMutationTrigger, { isLoading: isPromoteLoading }] =
    usePromoteResourceMutation();
  const [muteResourceMutationTrigger, { isLoading: isMuteLoading }] =
    useMuteResourceMutation();

  const isLoading = isPromoteLoading || isMuteLoading;

  const handleIgnoreClicked = async (urn: string) => {
    await muteResourceMutationTrigger({
      staged_resource_urn: urn,
    });
  };

  const handleConfirmClicked = async (urn: string) => {
    await promoteResourceMutationTrigger({
      staged_resource_urn: urn,
    });
  };

  if (resourceType === StagedResourceType.FIELD) {
    return (
      <Flex direction="row" align="center" justify="center" w="full">
        <ButtonGroup>
          <ActionButton
            title="Confirm all"
            icon={<CheckIcon />}
            onClick={() => handleConfirmClicked(resourceUrn)}
            disabled={isLoading}
            variant="solid"
            colorScheme="primary"
          />
          <ActionButton
            title="Ignore all"
            icon={<ViewOffIcon />}
            disabled={isLoading}
            onClick={() => handleIgnoreClicked(resourceUrn)}
          />
        </ButtonGroup>
      </Flex>
    );
  }

  if (resourceType === StagedResourceType.TABLE) {
    return (
      <Flex direction="row" align="center" justify="center" w="full">
        <ButtonGroup>
          <ActionButton
            title="Confirm all"
            icon={<CheckIcon />}
            onClick={() => handleConfirmClicked(resourceUrn)}
            disabled={isLoading}
            variant="solid"
            colorScheme="primary"
          />
          <ActionButton
            title="Ignore all"
            icon={<ViewOffIcon />}
            disabled={isLoading}
            onClick={() => handleIgnoreClicked(resourceUrn)}
          />
        </ButtonGroup>
      </Flex>
    );
  }

  return null;
};

export default DiscoveryBulkActions;
