import {
  ButtonGroup,
  CheckIcon,
  Flex,
  Text,
  ViewOffIcon,
} from "@fidesui/react";

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

  const isLoading = isPromoteLoading || isMuteLoading;

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
      w="full"
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
          disabled={isLoading}
          variant="solid"
          colorScheme="primary"
        />
        <ActionButton
          title="Ignore"
          icon={<ViewOffIcon />}
          disabled={isLoading}
          onClick={() => handleIgnoreClicked(selectedUrns)}
        />
      </ButtonGroup>
    </Flex>
  );
};

export default DiscoveryTableBulkActions;
