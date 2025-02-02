import {
  AntButton as Button,
  AntSpace as Space,
  AntTooltip as Tooltip,
} from "fidesui";

import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { useAlert } from "~/features/common/hooks";
import { UNCATEGORIZED_SEGMENT } from "~/features/common/nav/v2/routes";

import {
  useAddMonitorResultSystemMutation,
  useIgnoreMonitorResultSystemMutation,
} from "../../action-center.slice";
import { MonitorSystemAggregate } from "../../types";

interface DiscoveredSystemActionsCellProps {
  monitorId: string;
  system: MonitorSystemAggregate;
}

export const DiscoveredSystemActionsCell = ({
  monitorId,
  system,
}: DiscoveredSystemActionsCellProps) => {
  const [addMonitorResultSystemMutation, { isLoading: isAddingResults }] =
    useAddMonitorResultSystemMutation();
  const [ignoreMonitorResultSystemMutation, { isLoading: isIgnoringResults }] =
    useIgnoreMonitorResultSystemMutation();

  const { successAlert, errorAlert } = useAlert();

  const anyActionIsLoading = isAddingResults || isIgnoringResults;

  const {
    id: resolvedSystemId,
    name: systemName,
    system_key: systemKey,
    total_updates: totalUpdates,
  } = system;

  const handleAdd = async () => {
    const result = await addMonitorResultSystemMutation({
      monitor_config_key: monitorId,
      resolved_system_id: resolvedSystemId,
    });
    if (isErrorResult(result)) {
      errorAlert(getErrorMessage(result.error));
    } else {
      successAlert(
        !systemKey
          ? `${systemName} and ${totalUpdates}assets have been added to the system inventory. ${systemName} is now configured for consent.`
          : `${totalUpdates} assets from ${systemName} have been added to the system inventory.`,
        `Confirmed`,
      );
    }
  };

  const handleIgnore = async () => {
    const result = await ignoreMonitorResultSystemMutation({
      monitor_config_key: monitorId,
      resolved_system_id: resolvedSystemId || UNCATEGORIZED_SEGMENT,
    });
    if (isErrorResult(result)) {
      errorAlert(getErrorMessage(result.error));
    } else {
      successAlert(
        systemName
          ? `${totalUpdates} assets from ${systemName} have been ignored and will not appear in future scans.`
          : `${totalUpdates} uncategorized assets have been ignored and will not appear in future scans.`,
        `Confirmed`,
      );
    }
  };

  return (
    <Space>
      <Tooltip
        title={
          !system.id
            ? `These assets must be categorized before you can add them to the inventory.`
            : undefined
        }
      >
        <Button
          data-testid="add-btn"
          size="small"
          onClick={handleAdd}
          disabled={!system.id || anyActionIsLoading}
          loading={isAddingResults}
        >
          Add
        </Button>
      </Tooltip>
      <Button
        data-testid="ignore-btn"
        size="small"
        onClick={handleIgnore}
        disabled={anyActionIsLoading}
        loading={isIgnoringResults}
      >
        Ignore
      </Button>
    </Space>
  );
};
