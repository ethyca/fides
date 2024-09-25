import { ButtonGroup, CheckIcon, Flex, Text, ViewOffIcon } from "fidesui";

import ActionButton from "~/features/data-discovery-and-detection/ActionButton";
import {
  useMuteResourcesMutation,
  usePromoteResourcesMutation,
} from "~/features/data-discovery-and-detection/discovery-detection.slice";

const DiscoveryTableBulkActions = ({
  selectedUrns,
}: {
  selectedUrns: string[];
}) => {
  const [promoteResourcesMutationTrigger, { isLoading: isPromoteLoading }] =
    usePromoteResourcesMutation();
  const [muteResourcesMutationTrigger, { isLoading: isMuteLoading }] =
    useMuteResourcesMutation();

  const anyActionIsLoading = isPromoteLoading || isMuteLoading;

  const handleConfirmClicked = async (urns: string[]) => {
    await promoteResourcesMutationTrigger({
      staged_resource_urns: urns,
    });
  };

  const handleIgnoreClicked = async (urns: string[]) => {
    await muteResourcesMutationTrigger({
      staged_resource_urns: urns,
    });
  };

  if (!selectedUrns.length) {
    return null;
  }

  return (
    <Flex
      direction="row"
      align="center"
      justify="center"
      data-testid="bulk-actions-menu"
    >
      <Text
        fontSize="xs"
        fontWeight="semibold"
        minW={16}
        mr={6}
      >{`${selectedUrns.length} selected`}</Text>
      <ButtonGroup>
        <ActionButton
          title="Confirm"
          icon={<CheckIcon />}
          onClick={() => handleConfirmClicked(selectedUrns)}
          isDisabled={anyActionIsLoading}
          isLoading={isPromoteLoading}
          variant="solid"
        />
        <ActionButton
          title="Ignore"
          icon={<ViewOffIcon />}
          isDisabled={anyActionIsLoading}
          isLoading={isMuteLoading}
          onClick={() => handleIgnoreClicked(selectedUrns)}
        />
      </ButtonGroup>
    </Flex>
  );
};

export default DiscoveryTableBulkActions;
