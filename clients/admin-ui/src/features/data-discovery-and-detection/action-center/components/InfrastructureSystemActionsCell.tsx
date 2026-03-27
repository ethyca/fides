import { Button, Icons, Space, Tooltip, useMessage } from "fidesui";
import React from "react";

import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { DiffStatus } from "~/types/api";

import {
  useMuteIdentityProviderMonitorResultMutation,
  usePromoteIdentityProviderMonitorResultMutation,
  useUnmuteIdentityProviderMonitorResultMutation,
} from "../../discovery-detection.slice";
import { InfrastructureSystemBulkActionType } from "../constants";
import { ActionCenterTabHash } from "../hooks/useActionCenterTabs";

interface InfrastructureSystemActionsCellProps {
  monitorId: string;
  system: {
    urn?: string;
    name?: string | null;
    diff_status?: DiffStatus | null;
  };
  allowIgnore?: boolean;
  allowRestore?: boolean;
  activeTab?: ActionCenterTabHash | null;
  approveIcon?: React.ReactNode;
  ignoreIcon?: React.ReactNode;
  onPromoteSuccess?: () => void;
}

export const InfrastructureSystemActionsCell = ({
  monitorId,
  system,
  allowIgnore,
  allowRestore,
  activeTab,
  approveIcon = <Icons.Checkmark />,
  ignoreIcon = <Icons.ViewOff />,
  onPromoteSuccess,
}: InfrastructureSystemActionsCellProps) => {
  const [
    promoteIdentityProviderMonitorResultMutation,
    { isLoading: isPromoting },
  ] = usePromoteIdentityProviderMonitorResultMutation();

  const [muteIdentityProviderMonitorResultMutation, { isLoading: isMuting }] =
    useMuteIdentityProviderMonitorResultMutation();

  const [
    unmuteIdentityProviderMonitorResultMutation,
    { isLoading: isUnmuting },
  ] = useUnmuteIdentityProviderMonitorResultMutation();

  const messageApi = useMessage();

  const handleApprove = async () => {
    if (!system.urn) {
      messageApi.error("Cannot promote: system URN is missing");
      return;
    }

    const result = await promoteIdentityProviderMonitorResultMutation({
      monitor_config_key: monitorId,
      urn: system.urn,
    });

    if (isErrorResult(result)) {
      messageApi.error(getErrorMessage(result.error));
    } else {
      messageApi.success(
        `${system.name || "System"} has been promoted to the system inventory.`,
      );
      if (onPromoteSuccess) {
        onPromoteSuccess();
      }
    }
  };

  const handleIgnore = async () => {
    if (!system.urn) {
      messageApi.error("Cannot ignore: system URN is missing");
      return;
    }

    const result = await muteIdentityProviderMonitorResultMutation({
      monitor_config_key: monitorId,
      urn: system.urn,
    });

    if (isErrorResult(result)) {
      messageApi.error(getErrorMessage(result.error));
    } else {
      messageApi.success(`${system.name || "System"} has been ignored.`);
      if (onPromoteSuccess) {
        onPromoteSuccess();
      }
    }
  };

  const handleRestore = async () => {
    if (!system.urn) {
      messageApi.error("Cannot restore: system URN is missing");
      return;
    }

    const result = await unmuteIdentityProviderMonitorResultMutation({
      monitor_config_key: monitorId,
      urn: system.urn,
    });

    if (isErrorResult(result)) {
      messageApi.error(getErrorMessage(result.error));
    } else {
      messageApi.success(`${system.name || "System"} has been restored.`);
      if (onPromoteSuccess) {
        onPromoteSuccess();
      }
    }
  };

  const isActionInProgress = isPromoting || isMuting || isUnmuting;
  const isIgnoredTab = activeTab === ActionCenterTabHash.IGNORED;
  const isIgnored = system.diff_status
    ? system.diff_status === DiffStatus.MUTED
    : isIgnoredTab;

  const getActionTooltip = (
    action:
      | InfrastructureSystemBulkActionType.APPROVE
      | InfrastructureSystemBulkActionType.RESTORE,
  ) => {
    const isApprove = action === InfrastructureSystemBulkActionType.APPROVE;
    if (!system.urn) {
      return `This system cannot be ${isApprove ? "promoted" : "restored"}: URN is missing.`;
    }
    if (isApprove && isIgnored) {
      return "Restore systems before adding to the inventory";
    }
    if (!isApprove && !isIgnored) {
      return "You can only restore ignored systems";
    }
    return isApprove ? "Approve" : "Restore";
  };

  return (
    <Space>
      {allowIgnore && !isIgnoredTab && (
        <Tooltip title="Ignore">
          <Button
            data-testid="ignore-btn"
            size="small"
            onClick={handleIgnore}
            disabled={!system.urn || isActionInProgress}
            loading={isMuting}
            icon={ignoreIcon}
            aria-label="Ignore"
          >
            {!ignoreIcon && "Ignore"}
          </Button>
        </Tooltip>
      )}
      {(isIgnoredTab || allowRestore) && (
        <Tooltip
          title={getActionTooltip(InfrastructureSystemBulkActionType.RESTORE)}
        >
          <Button
            data-testid="restore-btn"
            size="small"
            onClick={handleRestore}
            disabled={!system.urn || !isIgnored || isActionInProgress}
            loading={isUnmuting}
            icon={<Icons.View />}
            aria-label="Restore"
          />
        </Tooltip>
      )}

      <Tooltip
        title={getActionTooltip(InfrastructureSystemBulkActionType.APPROVE)}
      >
        <Button
          data-testid="approve-btn"
          size="small"
          onClick={handleApprove}
          disabled={!system.urn || isIgnored || isActionInProgress}
          loading={isPromoting}
          icon={approveIcon}
          aria-label="Approve"
        >
          {!approveIcon && "Approve"}
        </Button>
      </Tooltip>
    </Space>
  );
};
