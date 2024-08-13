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

  const isLoading = isPromoteLoading || isMuteLoading;

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
      w="full"
      data-testid="bulk-actions-menu"
    >
      <ButtonGroup>
        <ActionButton
          title="Confirm all"
          icon={<CheckIcon />}
          onClick={() => handleConfirmClicked([resourceUrn])}
          disabled={isLoading}
          variant="solid"
          colorScheme="neutral"
        />
        <ActionButton
          title="Ignore all"
          icon={<ViewOffIcon />}
          disabled={isLoading}
          onClick={() => handleIgnoreClicked([resourceUrn])}
        />
      </ButtonGroup>
    </Flex>
  );
};

export default DiscoveryFieldBulkActions;
