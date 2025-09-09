import {
  AntFlex as Flex,
  CheckIcon,
  ConfirmationModal,
  Text,
  ViewOffIcon,
} from "fidesui";
import { useState } from "react";

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
    "Confirm" | "Ignore"
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
            onClick={() => setConfirmationState("Confirm")}
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
            onClick={() => setConfirmationState("Ignore")}
            size="middle"
          />
        </Flex>
      </Flex>
      <ConfirmationModal
        isOpen={!!confirmationState}
        onClose={() => setConfirmationState(undefined)}
        onConfirm={() => {
          switch (confirmationState) {
            case "Ignore":
              handleIgnoreMutation(selectedUrns);
              break;
            case "Confirm":
              handleConfirmMutation(selectedUrns);
              break;
            default:
              break;
          }
        }}
        title={`${confirmationState} Collection`}
        message={
          <Text>
            {`You are about to bulk ${confirmationState}}`}
            <Text color="complimentary.500" as="span" fontWeight="bold">
              {selectedUrns.join()}
            </Text>
            . Are you sure you would like to continue?
          </Text>
        }
      />
    </>
  );
};

export default DiscoveryTableBulkActions;
