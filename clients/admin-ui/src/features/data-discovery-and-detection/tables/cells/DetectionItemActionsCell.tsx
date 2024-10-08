import { CheckIcon, HStack } from "fidesui";

import { useAlert } from "~/features/common/hooks";
import { DiffStatus, StagedResource } from "~/types/api";

import { MonitorOffIcon } from "../../../common/Icon/MonitorOffIcon";
import { MonitorOnIcon } from "../../../common/Icon/MonitorOnIcon";
import ActionButton from "../../ActionButton";
import {
  useConfirmResourceMutation,
  useMuteResourceMutation,
} from "../../discovery-detection.slice";
import { StagedResourceType } from "../../types/StagedResourceType";
import { findResourceType } from "../../utils/findResourceType";

interface DetectionItemActionProps {
  resource: StagedResource;
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

  const anyActionIsLoading = confirmIsLoading || muteIsLoading;

  const { diff_status: diffStatus, child_diff_statuses: childDiffStatus } =
    resource;

  // We enable monitor / stop monitoring at the schema level only
  // Tables and field levels can mute/monitor
  const isSchemaType = resourceType === StagedResourceType.SCHEMA;
  const isFieldType = resourceType === StagedResourceType.FIELD;

  const showStartMonitoringAction =
    (isSchemaType && diffStatus === undefined) ||
    (!isFieldType && diffStatus === DiffStatus.ADDITION);
  const showMuteAction = diffStatus !== DiffStatus.MUTED;
  const showStartMonitoringActionOnMutedField =
    isFieldType && diffStatus === DiffStatus.MUTED;

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
          isDisabled={anyActionIsLoading}
          isLoading={confirmIsLoading}
        />
      )}
      {showStartMonitoringActionOnMutedField && (
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
          isDisabled={anyActionIsLoading}
          isLoading={confirmIsLoading}
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
          isDisabled={anyActionIsLoading}
          isLoading={confirmIsLoading}
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
          isDisabled={anyActionIsLoading}
          isLoading={muteIsLoading}
        />
      )}
    </HStack>
  );
};

export default DetectionItemActionsCell;
