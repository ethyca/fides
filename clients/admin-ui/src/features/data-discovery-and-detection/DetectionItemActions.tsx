import {
  ButtonSpinner,
  CheckIcon,
  CloseIcon,
  EditIcon,
  HStack,
  ViewIcon,
  ViewOffIcon,
} from "@fidesui/react";
import { useState } from "react";

import {
  ClassificationStatus,
  DiffStatus,
  MonitorStatus,
  StagedResource,
} from "~/types/api";
import { MonitorOffIcon } from "../common/Icon/MonitorOffIcon";
import { MonitorOnIcon } from "../common/Icon/MonitorOnIcon";
import { TrashCanOutlineIcon } from "../common/Icon/TrashCanOutlineIcon";
import ActionButton from "./ActionButton";

import {
  useAcceptResourceMutation,
  useMonitorResourceMutation,
  useMuteResourceMutation,
  useUnmuteResourceMutation,
} from "./discovery-detection.slice";
import { StagedResourceType } from "./types/StagedResourceType";

interface DetectionItemActionProps {
  resource: StagedResource;
  resourceType: StagedResourceType;
}

const DetectionItemAction: React.FC<DetectionItemActionProps> = ({
  resource,
  resourceType,
}) => {
  const [monitorResourceMutation] = useMonitorResourceMutation();
  const [muteResourceMutation] = useMuteResourceMutation();
  const [acceptResourceMutation] = useAcceptResourceMutation();

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

  const showStartMonitoringAction =
    isSchemaType &&
    (diffStatus === undefined || diffStatus === DiffStatus.MUTED);
  const showStopMonitoringAction =
    isSchemaType && diffStatus !== DiffStatus.MUTED;
  const showRemoveAction = isSchemaType && diffStatus === DiffStatus.REMOVAL;

  return (
    <HStack onClick={(e) => e.stopPropagation()}>
      {showStartMonitoringAction && (
        <ActionButton
          title="Monitor"
          icon={<MonitorOnIcon />}
          onClick={async () => {
            setIsProcessingAction(true);
            await monitorResourceMutation({
              staged_resource_urn: resource.urn,
              monitor_config_id: resource.monitor_config_id,
            });
            setIsProcessingAction(false);
          }}
          disabled={isProcessingAction}
        />
      )}
      {showStopMonitoringAction && (
        <ActionButton
          title="Ignore"
          icon={<MonitorOffIcon />}
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
      {showRemoveAction && (
        <ActionButton
          title="Drop"
          icon={<TrashCanOutlineIcon />}
          onClick={async () => {
            setIsProcessingAction(true);
            await acceptResourceMutation({
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
