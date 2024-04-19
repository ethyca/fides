/* eslint-disable @typescript-eslint/no-use-before-define */
import {
  CheckIcon,
  CloseIcon,
  EditIcon,
  HStack,
  Tooltip,
  ViewIcon,
  ViewOffIcon,
  IconButton,
} from "@fidesui/react";
import { ReactElement } from "react";
import { StagedResource } from "~/types/api";
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

enum mockMonitorStatusEnum {
  MONITORED = "monitored",
  MUTED = "muted",
}

enum mockDiffStatusEnum {
  ADDITION = "addition",
  REMOVAL = "removal",
  MODIFICATION = "modification",
}

enum mockClassificationStatusEnum {
  PROCESSING = "processing",
  COMPLETE = "complete",
}

const DiscoveryMonitorItemActions: React.FC<
  DiscoveryMonitorItemActionsProps
> = ({ resource, resourceType, monitorId }) => {
  const [monitorResourceMutation] = useMonitorResourceMutation();
  const [acceptResourceMutation] = useAcceptResourceMutation();
  const [muteResourceMutation] = useMuteResourceMutation();

  const monitorStatus = undefined;
  const diffStatus = mockDiffStatusEnum.ADDITION;
  const classificationStatus = undefined;

  if (resourceType === StagedResourceType.DATABASE) {
    // No actions for database level
    return null;
  }

  console.log("monitorId", monitorId);

  // We enable monitor / stop monitoring at the schema level only
  // Tables and field levels can mute/unmute
  const isSchemaType = resourceType === StagedResourceType.SCHEMA;

  const showMuteAction =
    monitorStatus !== mockMonitorStatusEnum.MUTED && !isSchemaType;
  const showUnmuteAction =
    monitorStatus === mockMonitorStatusEnum.MUTED && !isSchemaType;
  const showAcceptAction =
    classificationStatus === mockClassificationStatusEnum.COMPLETE &&
    diffStatus;
  const showRejectAction =
    classificationStatus === mockClassificationStatusEnum.COMPLETE &&
    diffStatus;

  const showStartMonitoringAction =
    isSchemaType && monitorStatus !== mockMonitorStatusEnum.MONITORED;
  const showStopMonitoringAction =
    isSchemaType && monitorStatus === mockMonitorStatusEnum.MONITORED;

  const showEditAction =
    resourceType === StagedResourceType.FIELD &&
    classificationStatus === mockClassificationStatusEnum.COMPLETE;

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
