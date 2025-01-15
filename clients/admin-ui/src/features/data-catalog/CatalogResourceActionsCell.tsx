import {
  AntButton,
  AntButton as Button,
  Flex,
  Menu,
  MenuButton,
  MenuItem,
  MenuList,
  MoreIcon,
} from "fidesui";

import { useAlert } from "~/features/common/hooks";
import {
  CatalogResourceStatus,
  getCatalogResourceStatus,
} from "~/features/data-catalog/utils";
import {
  useConfirmResourceMutation,
  useMuteResourceMutation,
  usePromoteResourceMutation,
} from "~/features/data-discovery-and-detection/discovery-detection.slice";
import { StagedResourceAPIResponse } from "~/types/api";

const CatalogResourceActionsCell = ({
  resource,
}: {
  resource: StagedResourceAPIResponse;
}) => {
  const { successAlert } = useAlert();
  const status = getCatalogResourceStatus(resource);
  const [confirmResource, { isLoading: classifyIsLoading }] =
    useConfirmResourceMutation();
  const [promoteResource, { isLoading: approveIsLoading }] =
    usePromoteResourceMutation();
  const [muteResource, { isLoading: muteIsLoading }] =
    useMuteResourceMutation();

  const classifyResource = async () => {
    await confirmResource({
      staged_resource_urn: resource.urn,
      monitor_config_id: resource.monitor_config_id!,
      unmute_children: true,
      classify_monitored_resources: true,
    });
    successAlert(
      `Started classification on ${resource.name ?? "this resource"}`,
    );
  };

  const approveResource = async () => {
    await promoteResource({
      staged_resource_urn: resource.urn,
    });
    successAlert(`Approved ${resource.name ?? " resource"}`);
  };

  const hideResource = async () => {
    await muteResource({
      staged_resource_urn: resource.urn,
    });
    successAlert(`Hid ${resource.name ?? " resource"}`);
  };

  const anyActionIsLoading =
    classifyIsLoading || approveIsLoading || muteIsLoading;

  return (
    <Flex gap={2} justify="space-between">
      {status === CatalogResourceStatus.ATTENTION_REQUIRED && (
        <Button
          size="small"
          onClick={classifyResource}
          loading={classifyIsLoading}
          disabled={anyActionIsLoading}
          data-testid="classify-btn"
        >
          Classify
        </Button>
      )}
      {status === CatalogResourceStatus.IN_REVIEW && (
        <Button
          size="small"
          onClick={approveResource}
          loading={approveIsLoading}
          disabled={anyActionIsLoading}
          data-testid="approve-btn"
        >
          Approve
        </Button>
      )}
      <Menu>
        <MenuButton
          as={AntButton}
          size="small"
          // Chakra is expecting the Chakra "type" prop, i.e. HTML type,
          // but Ant buttons use "type" for styling
          // @ts-ignore
          type="text"
          className="max-w-4"
          icon={<MoreIcon transform="rotate(90deg)" ml={2} />}
          data-testid="resource-actions-menu"
        />
        <MenuList>
          <MenuItem onClick={hideResource} data-testid="hide-action">
            Hide
          </MenuItem>
        </MenuList>
      </Menu>
    </Flex>
  );
};

export default CatalogResourceActionsCell;
