import {
  AntFlex as Flex,
  AntList as List,
  CheckIcon,
  ConfirmationModal,
  Text,
  ViewOffIcon,
} from "fidesui";
import { useState } from "react";

import { sentenceCase } from "~/features/common/utils";
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
  const [confirmationState, setConfirmationState] = useState<
    "confirm" | "ignore"
  >();
  const [promoteResourcesMutationTrigger, { isLoading: isPromoteLoading }] =
    usePromoteResourcesMutation();
  const [muteResourcesMutationTrigger, { isLoading: isMuteLoading }] =
    useMuteResourcesMutation();

  const anyActionIsLoading = isPromoteLoading || isMuteLoading;

  const handleConfirmMutation = async (urns: string[]) => {
    await promoteResourcesMutationTrigger({
      staged_resource_urns: urns,
    });
  };

  const handleIgnoreMutation = async (urns: string[]) => {
    await muteResourcesMutationTrigger({
      staged_resource_urns: urns,
    });
  };

  if (!selectedUrns.length) {
    return null;
  }

  return (
    <>
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
            onClick={() => setConfirmationState("confirm")}
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
            onClick={() => setConfirmationState("ignore")}
            size="middle"
          />
        </Flex>
      </Flex>
      <ConfirmationModal
        isOpen={!!confirmationState}
        onClose={() => setConfirmationState(undefined)}
        onConfirm={() => {
          switch (confirmationState) {
            case "ignore":
              handleIgnoreMutation(selectedUrns);
              break;
            case "confirm":
              handleConfirmMutation(selectedUrns);
              break;
            default:
              break;
          }
        }}
        title={sentenceCase(`${confirmationState} resources`)}
        message={
          <Text>
            {`You are about to ${confirmationState} `}
            <Text color="complimentary.500" as="span" fontWeight="bold">
              {selectedUrns.length}
            </Text>
            {` items. `}
            Are you sure you would like to continue?
          </Text>
        }
      />
    </>
  );
};

export default DiscoveryTableBulkActions;
