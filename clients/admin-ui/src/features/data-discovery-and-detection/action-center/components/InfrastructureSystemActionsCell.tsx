import {
  AntButton as Button,
  AntSpace as Space,
  AntTooltip as Tooltip,
  Icons,
  useToast,
} from "fidesui";
import React from "react";

import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { errorToastParams, successToastParams } from "~/features/common/toast";

import {
  useMuteIdentityProviderMonitorResultMutation,
  usePromoteIdentityProviderMonitorResultMutation,
  useUnmuteIdentityProviderMonitorResultMutation,
} from "../../discovery-detection.slice";
import { ActionCenterTabHash } from "../hooks/useActionCenterTabs";

interface InfrastructureSystemActionsCellProps {
  monitorId: string;
  system: {
    urn?: string;
    name?: string | null;
  };
  allowIgnore?: boolean;
  activeTab?: ActionCenterTabHash | null;
  addIcon?: React.ReactNode;
  ignoreIcon?: React.ReactNode;
  onPromoteSuccess?: () => void;
}

export const InfrastructureSystemActionsCell = ({
  monitorId,
  system,
  allowIgnore,
  activeTab,
  addIcon = <Icons.Checkmark />,
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

  const toast = useToast();

  const handleAdd = async () => {
    if (!system.urn) {
      toast(errorToastParams("Cannot promote: system URN is missing"));
      return;
    }

    const result = await promoteIdentityProviderMonitorResultMutation({
      monitor_config_key: monitorId,
      urn: system.urn,
    });

    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
    } else {
      toast(
        successToastParams(
          `${system.name || "System"} has been promoted to the system inventory.`,
        ),
      );
      if (onPromoteSuccess) {
        onPromoteSuccess();
      }
    }
  };

  const handleIgnore = async () => {
    if (!system.urn) {
      toast(errorToastParams("Cannot ignore: system URN is missing"));
      return;
    }

    const result = await muteIdentityProviderMonitorResultMutation({
      monitor_config_key: monitorId,
      urn: system.urn,
    });

    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
    } else {
      toast(successToastParams(`${system.name || "System"} has been ignored.`));
      if (onPromoteSuccess) {
        onPromoteSuccess();
      }
    }
  };

  const handleRestore = async () => {
    if (!system.urn) {
      toast(errorToastParams("Cannot restore: system URN is missing"));
      return;
    }

    const result = await unmuteIdentityProviderMonitorResultMutation({
      monitor_config_key: monitorId,
      urn: system.urn,
    });

    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
    } else {
      toast(
        successToastParams(`${system.name || "System"} has been restored.`),
      );
      if (onPromoteSuccess) {
        onPromoteSuccess();
      }
    }
  };

  const isActionInProgress = isPromoting || isMuting || isUnmuting;
  const isIgnoredTab = activeTab === ActionCenterTabHash.IGNORED;

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
      {isIgnoredTab ? (
        <Tooltip
          title={
            !system.urn
              ? `This system cannot be restored: URN is missing.`
              : "Restore"
          }
        >
          <Button
            data-testid="restore-btn"
            size="small"
            onClick={handleRestore}
            disabled={!system.urn || isActionInProgress}
            loading={isUnmuting}
            icon={<Icons.Renew />}
            aria-label="Restore"
          >
            Restore
          </Button>
        </Tooltip>
      ) : (
        <Tooltip
          title={
            !system.urn
              ? `This system cannot be promoted: URN is missing.`
              : "Add"
          }
        >
          <Button
            data-testid="add-btn"
            size="small"
            onClick={handleAdd}
            disabled={!system.urn || isActionInProgress}
            loading={isPromoting}
            icon={addIcon}
            aria-label="Add"
          >
            {!addIcon && "Add"}
          </Button>
        </Tooltip>
      )}
    </Space>
  );
};
