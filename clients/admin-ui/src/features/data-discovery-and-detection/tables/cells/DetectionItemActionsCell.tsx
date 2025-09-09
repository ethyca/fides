import { ConfirmationModal, HStack, Text } from "fidesui";
import { useState } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import { useAlert } from "~/features/common/hooks";
import { sentenceCase } from "~/features/common/utils";
import { DiscoveryMonitorItem } from "~/features/data-discovery-and-detection/types/DiscoveryMonitorItem";
import { DiffStatus, StagedResourceTypeValue } from "~/types/api";
import { isErrorResult } from "~/types/errors";

import { MonitorOffIcon } from "../../../common/Icon/MonitorOffIcon";
import { MonitorOnIcon } from "../../../common/Icon/MonitorOnIcon";
import ActionButton from "../../ActionButton";
import {
  useConfirmResourceMutation,
  useMuteResourceMutation,
  useUnmuteResourceMutation,
} from "../../discovery-detection.slice";
import { findResourceType } from "../../utils/findResourceType";

interface DetectionItemActionProps {
  resource: DiscoveryMonitorItem;
  ignoreChildActions?: boolean;
}

const DetectionItemActionsCell = ({
  resource,
  ignoreChildActions = false,
}: DetectionItemActionProps) => {
  const [confirmationState, setConfirmationState] = useState<
    "confirm" | "mute"
  >();
  const resourceType = findResourceType(resource);
  const [confirmResourceMutation, { isLoading: confirmIsLoading }] =
    useConfirmResourceMutation();
  const [muteResourceMutation, { isLoading: muteIsLoading }] =
    useMuteResourceMutation();
  const [unmuteResourceMutation, { isLoading: unmuteIsLoading }] =
    useUnmuteResourceMutation();

  const { successAlert, errorAlert } = useAlert();

  const handleMonitor = async () => {
    const result = await confirmResourceMutation({
      staged_resource_urn: resource.urn,
      monitor_config_id: resource.monitor_config_id!,
    });
    if (isErrorResult(result)) {
      errorAlert(getErrorMessage(result.error, "Failed to confirm resource"));
    } else {
      successAlert(
        "Data discovery has started. The results may take some time to appear in the “Data discovery“ tab.",
        `${resource.name || "The resource"} is now being monitored.`,
      );
    }
  };

  const handleUnMute = async () => {
    const result = await unmuteResourceMutation({
      staged_resource_urn: resource.urn,
    });
    if (isErrorResult(result)) {
      errorAlert(getErrorMessage(result.error), "Failed to un-mute resource");
    } else {
      successAlert(
        `${resource.name || "The resource"} has been un-muted and is now being monitored.`,
      );
    }
  };

  const handleStartMonitoringOnMutedParent = async () => {
    const result = await confirmResourceMutation({
      staged_resource_urn: resource.urn,
      monitor_config_id: resource.monitor_config_id!,
      unmute_children: true,
      classify_monitored_resources: true,
    });
    if (isErrorResult(result)) {
      errorAlert(getErrorMessage(result.error), "Failed to un-mute resource");
    } else {
      successAlert(
        "Data discovery has started. The results may take some time to appear in the “Data discovery“ tab.",
        `${resource.name || "The resource"} is now being monitored.`,
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
        `Ignored data will not be monitored for changes or added to Fides datasets.`,
        `${resource.name || "Resource"} ignored`,
      );
    }
  };

  const anyActionIsLoading =
    confirmIsLoading || muteIsLoading || unmuteIsLoading;

  const { diff_status: diffStatus, child_diff_statuses: childDiffStatus } =
    resource;

  // We enable monitor / stop monitoring at the schema level only
  // Table levels can mute/monitor
  // Field levels can mute/un-mute
  const isSchemaType = resourceType === StagedResourceTypeValue.SCHEMA;
  const isFieldType = resourceType === StagedResourceTypeValue.FIELD;
  const hasClassificationChanges =
    childDiffStatus &&
    (childDiffStatus[DiffStatus.CLASSIFICATION_ADDITION] ||
      childDiffStatus[DiffStatus.CLASSIFICATION_UPDATE]);

  const showStartMonitoringAction =
    (isSchemaType && diffStatus === undefined) ||
    (!isFieldType && diffStatus === DiffStatus.ADDITION) ||
    hasClassificationChanges;
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
    childDiffHasChanges &&
    !hasClassificationChanges;

  return (
    <>
      <HStack>
        {(showStartMonitoringAction || showConfirmAction) && (
          <ActionButton
            title="Monitor"
            icon={<MonitorOnIcon />}
            onClick={() =>
              isFieldType ? handleMonitor : setConfirmationState("confirm")
            }
            disabled={anyActionIsLoading}
            loading={confirmIsLoading}
          />
        )}
        {showUnMuteAction && (
          <ActionButton
            title="Un-Mute"
            icon={<MonitorOnIcon />}
            // Un-mute a field (marks field as monitored)
            onClick={handleUnMute}
            disabled={anyActionIsLoading}
            loading={confirmIsLoading}
          />
        )}
        {showStartMonitoringActionOnMutedParent && (
          <ActionButton
            title="Monitor"
            icon={<MonitorOnIcon />}
            // This is a special case where we are monitoring a muted schema/table, we need to un-mute all children
            onClick={() => setConfirmationState("confirm")}
            disabled={anyActionIsLoading}
            loading={confirmIsLoading}
          />
        )}
        {/* Positive Actions (Monitor, Confirm) goes first. Negative actions such as ignore should be last */}
        {showMuteAction && (
          <ActionButton
            title="Ignore"
            icon={<MonitorOffIcon />}
            onClick={() =>
              isFieldType ? handleMute : setConfirmationState("mute")
            }
            disabled={anyActionIsLoading}
            loading={muteIsLoading}
          />
        )}
      </HStack>
      <ConfirmationModal
        isOpen={!!confirmationState}
        onClose={() => setConfirmationState(undefined)}
        onConfirm={() => {
          switch (confirmationState) {
            case "mute":
              handleMute;
              break;
            case "confirm":
              handleStartMonitoringOnMutedParent;
              break;
            default:
              break;
          }
        }}
        title={sentenceCase(`${confirmationState} resources`)}
        message={
          <Text>
            {`You are about to ${confirmationState} ${resource.data_type}`}
            <Text color="complimentary.500" as="span" fontWeight="bold">
              {resource.data_type}
            </Text>
            {` items. `}
            Are you sure you would like to continue?
          </Text>
        }
      />
    </>
  );
};

export default DetectionItemActionsCell;
