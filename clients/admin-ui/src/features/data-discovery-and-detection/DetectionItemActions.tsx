import {
  ButtonSpinner,
  CheckIcon,
  HStack,
  ViewIcon,
  ViewOffIcon,
} from "@fidesui/react";
import { useState } from "react";

import { DiffStatus, StagedResource } from "~/types/api";
import { MonitorOffIcon } from "../common/Icon/MonitorOffIcon";
import { MonitorOnIcon } from "../common/Icon/MonitorOnIcon";
import { TrashCanOutlineIcon } from "../common/Icon/TrashCanOutlineIcon";
import ActionButton from "./ActionButton";
import { findResourceType } from "./utils/findResourceType";

import {
  useConfirmResourceMutation,
  useMuteResourceMutation,
  useUnmuteResourceMutation,
} from "./discovery-detection.slice";
import { StagedResourceType } from "./types/StagedResourceType";

interface DetectionItemActionProps {
  resource: StagedResource;
}

const DetectionItemAction: React.FC<DetectionItemActionProps> = ({
  resource,
}) => {
  const resourceType = findResourceType(resource);
  const [confirmResourceMutation] = useConfirmResourceMutation();
  const [muteResourceMutation] = useMuteResourceMutation();
  const [unmuteResourceMutation] = useUnmuteResourceMutation();

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

  const showStartMonitoringAction = isSchemaType && diffStatus === undefined;
  const showMuteAction = diffStatus !== DiffStatus.MUTED;
  const showUnmuteAction = diffStatus === DiffStatus.MUTED;
  const showConfirmAction =
    diffStatus !== DiffStatus.MUTED &&
    childDiffStatus &&
    (childDiffStatus[DiffStatus.ADDITION] ||
      childDiffStatus[DiffStatus.REMOVAL]);

  const showRemoveAction = diffStatus === DiffStatus.REMOVAL;

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
              monitor_config_id: resource.monitor_config_id,
            });
            setIsProcessingAction(false);
          }}
          disabled={isProcessingAction}
        />
      )}
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
      {showUnmuteAction && (
        <ActionButton
          title="Monitor"
          icon={isSchemaType ? <MonitorOnIcon /> : <ViewIcon />}
          onClick={async () => {
            setIsProcessingAction(true);
            await unmuteResourceMutation({
              staged_resource_urn: resource.urn,
              monitor_config_id: resource.monitor_config_id,
            });
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
              monitor_config_id: resource.monitor_config_id,
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
