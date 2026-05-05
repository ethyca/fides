import { Button, Icons, Space, Tooltip } from "fidesui";
import React from "react";

import { DiffStatus } from "~/types/api";

import { InfrastructureSystemBulkActionType } from "../constants";
import { ActionCenterTabHash } from "../hooks/useActionCenterTabs";
import { useInfrastructureActions } from "../hooks/useInfrastructureActions";

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
  const actions = useInfrastructureActions({
    urn: system.urn,
    onSuccess: onPromoteSuccess,
    monitorId,
    diffStatus: system.diff_status ?? undefined,
  });
  const isActionInProgress = Object.values(actions).some(
    (action) => action.loading,
  );
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
            onClick={actions.ignore.callback}
            disabled={!system.urn || isActionInProgress}
            loading={actions.ignore.loading}
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
            onClick={actions.restore.callback}
            disabled={!system.urn || !isIgnored || isActionInProgress}
            loading={actions.restore.loading}
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
          onClick={actions.approve.callback}
          disabled={!system.urn || isIgnored || isActionInProgress}
          loading={actions.approve.loading}
          icon={approveIcon}
          aria-label="Approve"
        >
          {!approveIcon && "Approve"}
        </Button>
      </Tooltip>
    </Space>
  );
};
