import { CheckIcon, HStack } from "fidesui";

import { useAlert } from "~/features/common/hooks";
import { DiscoveryMonitorItem } from "~/features/data-discovery-and-detection/types/DiscoveryMonitorItem";
import { DiffStatus } from "~/types/api";

import { MonitorOffIcon } from "../../../common/Icon/MonitorOffIcon";
import { MonitorOnIcon } from "../../../common/Icon/MonitorOnIcon";
import ActionButton from "../../ActionButton";
import {
  useConfirmResourceMutation,
  useMuteResourceMutation,
  useUnmuteResourceMutation,
} from "../../discovery-detection.slice";
import { StagedResourceType } from "../../types/StagedResourceType";
import { findResourceType } from "../../utils/findResourceType";

interface DetectionItemActionProps {
  resource: DiscoveryMonitorItem;
  ignoreChildActions?: boolean;
}

const DetectionItemActionsCell = ({
  resource,
  ignoreChildActions = false,
}: DetectionItemActionProps) => {
  const resourceType = findResourceType(resource);
  const [confirmResourceMutation, { isLoading: confirmIsLoading }] =
    useConfirmResourceMutation();
  const [muteResourceMutation, { isLoading: muteIsLoading }] =
    useMuteResourceMutation();
  const { successAlert } = useAlert();
  const [unmuteResourceMutation, { isLoading: unmuteIsLoading }] =
    useUnmuteResourceMutation();

  const anyActionIsLoading =
    confirmIsLoading || muteIsLoading || unmuteIsLoading;

  const { diff_status: diffStatus, child_diff_statuses: childDiffStatus } =
    resource;

  // We enable monitor / stop monitoring at the schema level only
  // Table levels can mute/monitor
  // Field levels can mute/un-mute
  const isSchemaType = resourceType === StagedResourceType.SCHEMA;
  const isFieldType = resourceType === StagedResourceType.FIELD;

  const showStartMonitoringAction =
    (isSchemaType && diffStatus === undefined) ||
    (!isFieldType && diffStatus === DiffStatus.ADDITION);
  const showMuteAction = diffStatus !== DiffStatus.MUTED;
  const showStartMonitoringActionOnMutedParent =
    diffStatus === DiffStatus.MUTED && !isFieldType;
  const showUnMuteAction = diffStatus === DiffStatus.MUTED && isFieldType;

  const childDiffHasChanges =
    childDiffStatus &&
    (childDiffStatus[DiffStatus.ADDITION] ||
      childDiffStatus[DiffStatus.REMOVAL]);
  const showConfirmAction =
    diffStatus === DiffStatus.MONITORED &&
    !ignoreChildActions &&
    childDiffHasChanges;

  return (
    <HStack onClick={(e) => e.stopPropagation()}>
      {showStartMonitoringAction && (
        <ActionButton
          title="Monitor"
          icon={<MonitorOnIcon />}
          onClick={async () => {
            await confirmResourceMutation({
              staged_resource_urn: resource.urn,
              monitor_config_id: resource.monitor_config_id!,
            });
            successAlert(
              "Data discovery has started. The results may take some time to appear in the “Data discovery“ tab.",
              `${resource.name || "The resource"} is now being monitored.`,
            );
          }}
          disabled={anyActionIsLoading}
          loading={confirmIsLoading}
        />
      )}
      {showUnMuteAction && (
        <ActionButton
          title="Un-Mute"
          icon={<MonitorOnIcon />}
          // Un-mute a field (marks field as monitored)
          onClick={async () => {
            await unmuteResourceMutation({
              staged_resource_urn: resource.urn,
            });
            successAlert(
              "The resource has been un-muted.",
              `${resource.name || "The resource"} is now un-muted.`,
            );
          }}
          disabled={anyActionIsLoading}
          loading={confirmIsLoading}
        />
      )}
      {showStartMonitoringActionOnMutedParent && (
        <ActionButton
          title="Monitor"
          icon={<MonitorOnIcon />}
          // This is a special case where we are monitoring a muted schema/table, we need to un-mute all children
          onClick={async () => {
            await confirmResourceMutation({
              staged_resource_urn: resource.urn,
              monitor_config_id: resource.monitor_config_id!,
              unmute_children: true,
              classify_monitored_resources: true,
            });
            successAlert(
              "Data discovery has started. The results may take some time to appear in the “Data discovery“ tab.",
              `${resource.name || "The resource"} is now being monitored.`,
            );
          }}
          disabled={anyActionIsLoading}
          loading={confirmIsLoading}
        />
      )}
      {showConfirmAction && (
        <ActionButton
          title="Confirm"
          icon={<CheckIcon />}
          onClick={async () => {
            await confirmResourceMutation({
              staged_resource_urn: resource.urn,
              monitor_config_id: resource.monitor_config_id!,
            });
            successAlert(
              `These changes have been added to a Fides dataset. To view, navigate to "Manage datasets".`,
              `Table changes confirmed`,
            );
          }}
          disabled={anyActionIsLoading}
          loading={confirmIsLoading}
        />
      )}
      {/* Positive Actions (Monitor, Confirm) goes first. Negative actions such as ignore should be last */}
      {showMuteAction && (
        <ActionButton
          title="Ignore"
          icon={<MonitorOffIcon />}
          onClick={async () => {
            await muteResourceMutation({
              staged_resource_urn: resource.urn,
            });
            successAlert(
              `Ignored data will not be monitored for changes or added to Fides datasets.`,
              `${resource.name || "Resource"} ignored`,
            );
          }}
          disabled={anyActionIsLoading}
          loading={muteIsLoading}
        />
      )}
    </HStack>
  );
};

export default DetectionItemActionsCell;
