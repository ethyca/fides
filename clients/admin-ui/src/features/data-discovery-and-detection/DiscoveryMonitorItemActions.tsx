/* eslint-disable @typescript-eslint/no-use-before-define */
import {
  CheckIcon,
  CloseIcon,
  EditIcon,
  HStack,
  IconButton,
  Tooltip,
  ViewIcon,
  ViewOffIcon,
} from "@fidesui/react";
import { ReactElement } from "react";

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
          onClick={() =>
            monitorResourceMutation({
              monitor_config_id: monitorId,
              staged_resource_urn: resource.urn,
            })
          }
        />
      )}
      {showStopMonitoringAction && (
        <ActionIcon
          title="Stop Monitoring"
          icon={<StopIcon />}
          onClick={() =>
            muteResourceMutation({
              monitor_config_id: monitorId,
              staged_resource_urn: resource.urn,
            })
          }
        />
      )}
      {showMuteAction && (
        <ActionIcon
          title="Mute - Exclude from monitoring"
          icon={<ViewOffIcon />}
          onClick={() =>
            muteResourceMutation({
              monitor_config_id: monitorId,
              staged_resource_urn: resource.urn,
            })
          }
        />
      )}
      {showUnmuteAction && (
        <ActionIcon
          title="Unmute - Include in monitoring"
          icon={<ViewIcon />}
          onClick={() =>
            monitorResourceMutation({
              monitor_config_id: monitorId,
              staged_resource_urn: resource.urn,
            })
          }
        />
      )}
      {showRejectAction && (
        <ActionIcon title="Reject" icon={<CloseIcon />} onClick={() => {}} />
      )}
      {showAcceptAction && (
        <ActionIcon
          title="Accept"
          icon={<CheckIcon />}
          onClick={() =>
            acceptResourceMutation({
              monitor_config_id: monitorId,
              staged_resource_urn: resource.urn,
            })
          }
        />
      )}
      {showEditAction && (
        <ActionIcon title="Edit" icon={<EditIcon />} onClick={() => {}} />
      )}
    </HStack>
  );
};

const ActionIcon = ({
  title,
  icon,
  onClick,
}: {
  title: string;
  icon: ReactElement;
  onClick: () => void;
}) => (
  <Tooltip label={title}>
    <IconButton
      aria-label={title}
      variant="outline"
      size="xs"
      icon={icon}
      onClick={onClick}
    />
  </Tooltip>
);

export default DiscoveryMonitorItemActions;
