/* eslint-disable @typescript-eslint/no-use-before-define */
import {
  Button,
  ButtonSpinner,
  CheckIcon,
  CloseIcon,
  EditIcon,
  HStack,
  Text,
  ViewIcon,
  ViewOffIcon,
} from "@fidesui/react";
import { ReactElement, useState } from "react";

import {
  ClassificationStatus,
  MonitorStatus,
  StagedResource,
} from "~/types/api";
import { MonitorOffIcon } from "../common/Icon/MonitorOffIcon";
import { MonitorOnIcon } from "../common/Icon/MonitorOnIcon";

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
}

const DiscoveryMonitorItemActions: React.FC<
  DiscoveryMonitorItemActionsProps
> = ({ resource, resourceType }) => {
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
    isSchemaType && monitorStatus !== MonitorStatus.MUTED;

  const showEditAction =
    resourceType === StagedResourceType.FIELD &&
    classificationStatus === ClassificationStatus.COMPLETE;

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
      {showMuteAction && (
        <ActionButton
          title="Ignore"
          icon={<ViewOffIcon />}
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
          title="Unmute - Include in monitoring"
          icon={<ViewIcon />}
          onClick={async () => {
            setIsProcessingAction(true);
            await unmuteResourceMutation({
              staged_resource_urn: resource.urn,
            });
            setIsProcessingAction(false);
          }}
          disabled={isProcessingAction}
        />
      )}
      {showRejectAction && (
        <ActionButton
          title="Reject"
          icon={<CloseIcon />}
          onClick={() => {}}
          disabled={isProcessingAction}
        />
      )}
      {showAcceptAction && (
        <ActionButton
          title="Accept"
          icon={<CheckIcon />}
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
      {showEditAction && (
        <ActionButton
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

const ActionButton = ({
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
  <Button size="xs" variant="outline" onClick={onClick} disabled={disabled}>
    {icon}
    <Text marginLeft={1} fontWeight="semibold" fontSize={12}>
      {title}
    </Text>
  </Button>
);

export default DiscoveryMonitorItemActions;
