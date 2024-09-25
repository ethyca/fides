import { ButtonGroup, CheckIcon, Flex, ViewOffIcon } from "fidesui";

import ActionButton from "~/features/data-discovery-and-detection/ActionButton";
import {
  useMuteResourcesMutation,
  usePromoteResourcesMutation,
} from "~/features/data-discovery-and-detection/discovery-detection.slice";

const DiscoveryFieldBulkActions = ({
  resourceUrn,
}: {
  resourceUrn: string;
}) => {
  const [promoteResourcesMutationTrigger, { isLoading: isPromoteLoading }] =
    usePromoteResourcesMutation();
  const [muteResourceMutationTrigger, { isLoading: isMuteLoading }] =
    useMuteResourcesMutation();

  const anyActionIsLoading = isPromoteLoading || isMuteLoading;

  const handleIgnoreClicked = async (urns: string[]) => {
    await muteResourceMutationTrigger({
      staged_resource_urns: urns,
    });
  };

  const handleConfirmClicked = async (urns: string[]) => {
    await promoteResourcesMutationTrigger({
      staged_resource_urns: urns,
    });
  };

  return (
    <Flex
      direction="row"
      align="center"
      justify="center"
      data-testid="bulk-actions-menu"
    >
      <ButtonGroup>
        <ActionButton
          title="Confirm all"
          icon={<CheckIcon />}
          onClick={() => handleConfirmClicked([resourceUrn])}
          isDisabled={anyActionIsLoading}
          isLoading={isPromoteLoading}
          variant="solid"
        />
        <ActionButton
          title="Ignore all"
          icon={<ViewOffIcon />}
          onClick={() => handleIgnoreClicked([resourceUrn])}
          isDisabled={anyActionIsLoading}
          isLoading={isMuteLoading}
        />
      </ButtonGroup>
    </Flex>
  );
};

export default DiscoveryFieldBulkActions;
