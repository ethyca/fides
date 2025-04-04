import {
  AntButton as Button,
  CheckIcon,
  HStack,
  Menu,
  MenuButton,
  MenuItem,
  MenuList,
  MoreIcon,
  RepeatIcon,
  Spacer,
  ViewOffIcon,
} from "fidesui";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";

import { useAlert } from "~/features/common/hooks";
import { DiscoveryMonitorItem } from "~/features/data-discovery-and-detection/types/DiscoveryMonitorItem";
import { findResourceType } from "~/features/data-discovery-and-detection/utils/findResourceType";
import getResourceName from "~/features/data-discovery-and-detection/utils/getResourceName";
import { DiffStatus, StagedResourceTypeValue } from "~/types/api";

import ActionButton from "../../ActionButton";
import {
  useConfirmResourceMutation,
  useMuteResourceMutation,
  usePromoteResourceMutation,
} from "../../discovery-detection.slice";

interface DiscoveryItemActionsProps {
  resource: DiscoveryMonitorItem;
}

const DiscoveryItemActionsCell = ({ resource }: DiscoveryItemActionsProps) => {
  const [confirmResourceMutation, { isLoading: confirmIsLoading }] =
    useConfirmResourceMutation();
  const [promoteResourceMutation, { isLoading: promoteIsLoading }] =
    usePromoteResourceMutation();
  const [muteResourceMutation, { isLoading: muteIsLoading }] =
    useMuteResourceMutation();

  const anyActionIsLoading =
    promoteIsLoading || muteIsLoading || confirmIsLoading;

  const {
    diff_status: diffStatus,
    child_diff_statuses: childDiffStatus,
    // eslint-disable-next-line @typescript-eslint/naming-convention
    top_level_field_name,
  } = resource;

  const { successAlert, errorAlert } = useAlert();

  const isSubField = !!top_level_field_name;

  const itemHasClassificationChanges =
    diffStatus === DiffStatus.CLASSIFICATION_ADDITION ||
    diffStatus === DiffStatus.CLASSIFICATION_UPDATE;

  const childItemsHaveClassificationChanges =
    childDiffStatus &&
    (childDiffStatus[DiffStatus.CLASSIFICATION_ADDITION] ||
      childDiffStatus[DiffStatus.CLASSIFICATION_UPDATE]);

  const showPromoteAction =
    (itemHasClassificationChanges || childItemsHaveClassificationChanges) &&
    !isSubField;

  const showMuteAction =
    itemHasClassificationChanges || childItemsHaveClassificationChanges;

  const showReclassifyAction =
    findResourceType(resource) !== StagedResourceTypeValue.FIELD;

  // if promote and mute are both shown, show "Reclassify" in an overflow menu
  // to avoid having too many buttons in the cell
  const showReclassifyInOverflow =
    showPromoteAction && showMuteAction && showReclassifyAction;

  const handlePromote = async () => {
    const result = await promoteResourceMutation({
      staged_resource_urn: resource.urn,
    });
    if (isErrorResult(result)) {
      errorAlert(getErrorMessage(result.error), "Failed to promote resource");
    } else {
      successAlert(
        `These changes have been added to a Fides dataset. To view, navigate to "Manage datasets".`,
        `Table changes confirmed`,
      );
    }
  };

  const handleMute = async () => {
    const result = await muteResourceMutation({
      staged_resource_urn: resource.urn,
    });
    if (isErrorResult(result)) {
      errorAlert(getErrorMessage(result.error), "Failed to mute resource");
    } else {
      successAlert(
        `Ignored changes will not be added to a Fides dataset.`,
        `${resource.name || "Changes"} ignored`,
      );
    }
  };

  const handleReclassify = async () => {
    const result = await confirmResourceMutation({
      staged_resource_urn: resource.urn,
      monitor_config_id: resource.monitor_config_id!,
      start_classification: true,
      classify_monitored_resources: true,
    });
    if (isErrorResult(result)) {
      errorAlert(
        getErrorMessage(result.error),
        "Failed to reclassify resource",
      );
    } else {
      successAlert(
        `Reclassification of ${getResourceName(resource) || "the resource"} has begun.  The results may take some time to appear in the “Data discovery“ tab.`,
        `Reclassification started`,
      );
    }
  };

  return (
    <HStack gap={2}>
      {showPromoteAction && (
        <ActionButton
          title="Confirm"
          icon={<CheckIcon />}
          onClick={handlePromote}
          disabled={anyActionIsLoading}
          loading={promoteIsLoading}
        />
      )}
      {showMuteAction && (
        <ActionButton
          title="Ignore"
          icon={<ViewOffIcon />}
          onClick={handleMute}
          disabled={anyActionIsLoading}
          loading={muteIsLoading}
        />
      )}
      {showReclassifyAction && !showReclassifyInOverflow && (
        <ActionButton
          title="Reclassify"
          icon={<RepeatIcon />}
          onClick={handleReclassify}
          disabled={anyActionIsLoading}
          loading={confirmIsLoading}
        />
      )}
      {showReclassifyInOverflow && (
        <>
          <Spacer />
          <Menu>
            <MenuButton
              as={Button}
              size="small"
              // TS expects Chakra's type prop (HTML type) but we want to assign the Ant type
              // @ts-ignore
              type="text"
              icon={<MoreIcon transform="rotate(90deg)" />}
              className="w-6 gap-0"
              data-testid="actions-overflow-btn"
            />
            <MenuList>
              <MenuItem
                onClick={handleReclassify}
                icon={<RepeatIcon />}
                data-testid="action-reclassify"
              >
                Reclassify
              </MenuItem>
            </MenuList>
          </Menu>
        </>
      )}
    </HStack>
  );
};

export default DiscoveryItemActionsCell;
