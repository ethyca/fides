import { CheckIcon, Flex, ViewOffIcon } from "fidesui";

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
      <div className="flex gap-2">
        <ActionButton
          title="Confirm all"
          icon={<CheckIcon />}
          onClick={() => handleConfirmClicked([resourceUrn])}
          disabled={anyActionIsLoading}
          loading={isPromoteLoading}
          type="primary"
        />
        <ActionButton
          title="Ignore all"
          icon={<ViewOffIcon />}
          onClick={() => handleIgnoreClicked([resourceUrn])}
          disabled={anyActionIsLoading}
          loading={isMuteLoading}
        />
      </div>
    </Flex>
  );
};

export default DiscoveryFieldBulkActions;
