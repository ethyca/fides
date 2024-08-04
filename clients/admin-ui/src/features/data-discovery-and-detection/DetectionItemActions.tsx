import {
  ButtonSpinner,
  CheckIcon,
  HStack,
  ViewIcon,
  ViewOffIcon,
} from "fidesui";
import { useState } from "react";

import { useAlert } from "~/features/common/hooks";
import { DiffStatus, StagedResource } from "~/types/api";

import { MonitorOffIcon } from "../common/Icon/MonitorOffIcon";
import { MonitorOnIcon } from "../common/Icon/MonitorOnIcon";
import { TrashCanOutlineIcon } from "../common/Icon/TrashCanOutlineIcon";
import ActionButton from "./ActionButton";
import {
  useConfirmResourceMutation,
  useMuteResourceMutation,
  useUnmuteResourceMutation,
} from "./discovery-detection.slice";
import { StagedResourceType } from "./types/StagedResourceType";
import { findResourceType } from "./utils/findResourceType";

interface DetectionItemActionProps {
  resource: StagedResource;
}

const DetectionItemAction = ({ resource }: DetectionItemActionProps) => {
  const resourceType = findResourceType(resource);
  const [confirmResourceMutation] = useConfirmResourceMutation();
  const [muteResourceMutation] = useMuteResourceMutation();
  const [unmuteResourceMutation] = useUnmuteResourceMutation();
  const { successAlert } = useAlert();

  const [isProcessingAction, setIsProcessingAction] = useState(false);

  const { diff_status: diffStatus, child_diff_statuses: childDiffStatus } =
    resource;

  // No actions for database level
  if (resourceType === StagedResourceType.DATABASE) {
    return null;
  }

  // We enable monitor / stop monitoring at the schema level only
  // Tables and field levels can mute/unmute
  const isSchemaType = resourceType === StagedResourceType.SCHEMA;
  const isFieldType = resourceType === StagedResourceType.FIELD;

  const showStartMonitoringAction =
    (isSchemaType && diffStatus === undefined) ||
    (!isFieldType && diffStatus === DiffStatus.ADDITION);
  const showMuteAction = diffStatus !== DiffStatus.MUTED;
  const showUnmuteAction = diffStatus === DiffStatus.MUTED;
  const showConfirmAction =
    diffStatus === DiffStatus.MONITORED &&
    childDiffStatus &&
    (childDiffStatus[DiffStatus.ADDITION] ||
      childDiffStatus[DiffStatus.REMOVAL]);

  const showRemoveAction = false;

  return (
    <HStack onClick={(e) => e.stopPropagation()}>
      {showStartMonitoringAction && (
        <ActionButton
          title="Monitor"
          icon={<MonitorOnIcon />}
          onClick={async () => {
            setIsProcessingAction(true);
            await confirmResourceMutation({
              staged_resource_urn: resource.urn,
              monitor_config_id: resource.monitor_config_id!,
            });
            successAlert(
              "Data discovery has started. The results may take some time to appear in the “Data discovery“ tab.",
              `${resource.name || "The resource"} is now being monitored.`,
            );
            setIsProcessingAction(false);
          }}
          disabled={isProcessingAction}
        />
      )}
      {showUnmuteAction && (
        <ActionButton
          title="Monitor"
          icon={isSchemaType ? <MonitorOnIcon /> : <ViewIcon />}
          onClick={async () => {
            setIsProcessingAction(true);
            await unmuteResourceMutation({
              staged_resource_urn: resource.urn,
            });
            successAlert(
              "Data discovery has started. The results may take some time to appear in the “Data discovery“ tab.",
              `${resource.name || "The resource"} is now being monitored.`,
            );
            setIsProcessingAction(false);
          }}
          disabled={isProcessingAction}
        />
      )}
      {showConfirmAction && (
        <ActionButton
          title="Confirm"
          icon={<CheckIcon />}
          onClick={async () => {
            setIsProcessingAction(true);
            await confirmResourceMutation({
              staged_resource_urn: resource.urn,
              monitor_config_id: resource.monitor_config_id!,
            });
            setIsProcessingAction(false);
          }}
          disabled={isProcessingAction}
        />
      )}
      {showRemoveAction && (
        <ActionButton
          title="Drop"
          icon={<TrashCanOutlineIcon />}
          onClick={async () => {
            setIsProcessingAction(true);
            await confirmResourceMutation({
              staged_resource_urn: resource.urn,
              monitor_config_id: resource.monitor_config_id!,
            });
            setIsProcessingAction(false);
          }}
          disabled={isProcessingAction}
        />
      )}
      {/* Positive Actions (Monitor, Confirm) goes first. Negative actions such as ignore should be last */}
      {showMuteAction && (
        <ActionButton
          title="Ignore"
          icon={isSchemaType ? <MonitorOffIcon /> : <ViewOffIcon />}
          onClick={async () => {
            setIsProcessingAction(true);
            await muteResourceMutation({
              staged_resource_urn: resource.urn,
            });
            setIsProcessingAction(false);
          }}
          disabled={isProcessingAction}
        />
      )}

      {isProcessingAction ? <ButtonSpinner position="static" /> : null}
    </HStack>
  );
};

export default DetectionItemAction;
