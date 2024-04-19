/* eslint-disable @typescript-eslint/no-use-before-define */
import {
  ButtonSpinner,
  CheckIcon,
  CloseIcon,
  EditIcon,
  HStack,
  IconButton,
  Spinner,
  Tooltip,
  ViewIcon,
  ViewOffIcon,
} from "@fidesui/react";
import { ReactElement, useState } from "react";

import {
  ClassificationStatus,
  MonitorStatus,
  StagedResource,
} from "~/types/api";

import { PlayIcon } from "../common/Icon/Play";
import { StopIcon } from "../common/Icon/Stop";
import {
  useAcceptResourceMutation,
  useMonitorResourceMutation,
  useMuteResourceMutation,
  useUnmuteResourceMutation,
} from "./discovery-detection.slice";
import { StagedResourceType } from "./types/StagedResourceType";

interface DiscoveryMonitorItemActionsProps {
  resource: StagedResource;
  resourceType: StagedResourceType;
  monitorId: string;
}

const DiscoveryMonitorItemActions: React.FC<
  DiscoveryMonitorItemActionsProps
> = ({ resource, resourceType, monitorId }) => {
  const [monitorResourceMutation] = useMonitorResourceMutation();
  const [acceptResourceMutation] = useAcceptResourceMutation();
  const [muteResourceMutation] = useMuteResourceMutation();
  const [unmuteResourceMutation] = useUnmuteResourceMutation();

  const [isProcessingAction, setIsProcessingAction] = useState(false);

  const {
    monitor_status: monitorStatus,
    classification_status: classificationStatus,
    diff_status: diffStatus,
  } = resource;

  // No actions for database level
  if (resourceType === StagedResourceType.DATABASE) {
    return null;
  }

  // We enable monitor / stop monitoring at the schema level only
  // Tables and field levels can mute/unmute
  const isSchemaType = resourceType === StagedResourceType.SCHEMA;

  const showMuteAction = monitorStatus !== MonitorStatus.MUTED && !isSchemaType;
  const showUnmuteAction =
    monitorStatus === MonitorStatus.MUTED && !isSchemaType;
  const showAcceptAction =
    classificationStatus === ClassificationStatus.COMPLETE && diffStatus;
  const showRejectAction =
    classificationStatus === ClassificationStatus.COMPLETE && diffStatus;

  const showStartMonitoringAction =
    isSchemaType && monitorStatus !== MonitorStatus.MONITORED;
  const showStopMonitoringAction =
    isSchemaType && monitorStatus === MonitorStatus.MONITORED;

  const showEditAction =
    resourceType === StagedResourceType.FIELD &&
    classificationStatus === ClassificationStatus.COMPLETE;

  return (
    <HStack onClick={(e) => e.stopPropagation()}>
      {showStartMonitoringAction && (
        <ActionIcon
          title="Start Monitoring"
          icon={<PlayIcon />}
          onClick={async () => {
            setIsProcessingAction(true);
            await monitorResourceMutation({
              monitor_config_id: monitorId,
              staged_resource_urn: resource.urn,
            });
            setIsProcessingAction(false);
          }}
          disabled={isProcessingAction}
        />
      )}
      {showStopMonitoringAction && (
        <ActionIcon
          title="Stop Monitoring"
          icon={<StopIcon />}
          onClick={async () => {
            setIsProcessingAction(true);
            await muteResourceMutation({
              monitor_config_id: monitorId,
              staged_resource_urn: resource.urn,
            });
            setIsProcessingAction(false);
          }}
          disabled={isProcessingAction}
        />
      )}
      {showMuteAction && (
        <ActionIcon
          title="Mute - Exclude from monitoring"
          icon={<ViewOffIcon />}
          onClick={async () => {
            setIsProcessingAction(true);
            await muteResourceMutation({
              monitor_config_id: monitorId,
              staged_resource_urn: resource.urn,
            });
            setIsProcessingAction(false);
          }}
          disabled={isProcessingAction}
        />
      )}
      {showUnmuteAction && (
        <ActionIcon
          title="Unmute - Include in monitoring"
          icon={<ViewIcon />}
          onClick={async () => {
            setIsProcessingAction(true);
            await unmuteResourceMutation({
              monitor_config_id: monitorId,
              staged_resource_urn: resource.urn,
            });
            setIsProcessingAction(false);
          }}
          disabled={isProcessingAction}
        />
      )}
      {showRejectAction && (
        <ActionIcon
          title="Reject"
          icon={<CloseIcon />}
          onClick={() => {}}
          disabled={isProcessingAction}
        />
      )}
      {showAcceptAction && (
        <ActionIcon
          title="Accept"
          icon={<CheckIcon />}
          onClick={async () => {
            setIsProcessingAction(true);
            await acceptResourceMutation({
              monitor_config_id: monitorId,
              staged_resource_urn: resource.urn,
            });
            setIsProcessingAction(false);
          }}
          disabled={isProcessingAction}
        />
      )}
      {showEditAction && (
        <ActionIcon
          title="Edit"
          icon={<EditIcon />}
          onClick={() => {}}
          disabled={isProcessingAction}
        />
      )}
      {isProcessingAction ? <ButtonSpinner position="static" /> : null}
    </HStack>
  );
};

const ActionIcon = ({
  title,
  icon,
  onClick,
  disabled,
}: {
  title: string;
  icon: ReactElement;
  onClick: () => void;
  disabled?: boolean;
}) => (
  <Tooltip label={title}>
    <IconButton
      aria-label={title}
      variant="outline"
      size="xs"
      icon={icon}
      onClick={onClick}
      disabled={disabled}
    />
  </Tooltip>
);

export default DiscoveryMonitorItemActions;
