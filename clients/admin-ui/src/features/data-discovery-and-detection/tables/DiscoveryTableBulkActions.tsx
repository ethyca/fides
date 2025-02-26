import { AntFlex as Flex, CheckIcon, Text, ViewOffIcon } from "fidesui";

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
    <Flex className="items-center" data-testid="bulk-actions-menu">
      <Text
        fontSize="xs"
        fontWeight="semibold"
        minW={16}
        mr={4}
      >{`${selectedUrns.length} selected`}</Text>
      <Flex className="gap-2">
        <ActionButton
          title="Confirm"
          icon={<CheckIcon />}
          onClick={() => handleConfirmClicked(selectedUrns)}
          disabled={anyActionIsLoading}
          loading={isPromoteLoading}
          type="primary"
          size="middle"
        />
        <ActionButton
          title="Ignore"
          icon={<ViewOffIcon />}
          disabled={anyActionIsLoading}
          loading={isMuteLoading}
          onClick={() => handleIgnoreClicked(selectedUrns)}
          size="middle"
        />
      </Flex>
    </Flex>
  );
};

export default DiscoveryTableBulkActions;
