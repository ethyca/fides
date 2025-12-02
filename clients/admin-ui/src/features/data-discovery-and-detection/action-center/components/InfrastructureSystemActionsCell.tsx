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

import { usePromoteIdentityProviderMonitorResultMutation } from "../../discovery-detection.slice";
import { ActionCenterTabHash } from "../hooks/useActionCenterTabs";

interface InfrastructureSystemActionsCellProps {
  monitorId: string;
  system: {
    urn?: string;
    name?: string | null;
  };
  allowIgnore?: boolean;
  onTabChange: (tab: ActionCenterTabHash) => Promise<void>;
  addIcon?: React.ReactNode;
  ignoreIcon?: React.ReactNode;
  onPromoteSuccess?: () => void;
}

export const InfrastructureSystemActionsCell = ({
  monitorId,
  system,
  allowIgnore,
  addIcon = <Icons.Checkmark />,
  ignoreIcon = <Icons.ViewOff />,
  onPromoteSuccess,
}: InfrastructureSystemActionsCellProps) => {
  const [
    promoteIdentityProviderMonitorResultMutation,
    { isLoading: isPromoting },
  ] = usePromoteIdentityProviderMonitorResultMutation();

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
    // TODO: Implement ignore functionality for infrastructure systems
    // This may require a new endpoint similar to the promote endpoint
    toast(
      errorToastParams(
        "Ignore functionality not yet implemented for infrastructure systems",
      ),
    );
  };

  return (
    <Space>
      {allowIgnore && (
        <Tooltip title="Ignore">
          <Button
            data-testid="ignore-btn"
            size="small"
            onClick={handleIgnore}
            disabled={isPromoting}
            loading={false}
            icon={ignoreIcon}
            aria-label="Ignore"
          >
            {!ignoreIcon && "Ignore"}
          </Button>
        </Tooltip>
      )}
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
          disabled={!system.urn || isPromoting}
          loading={isPromoting}
          icon={addIcon}
          aria-label="Add"
        >
          {!addIcon && "Add"}
        </Button>
      </Tooltip>
    </Space>
  );
};
