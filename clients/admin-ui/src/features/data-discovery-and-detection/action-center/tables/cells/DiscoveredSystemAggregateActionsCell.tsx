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

  const { id, name, system_key: systemKey } = system;

  const handleAdd = async () => {
    const result = await addMonitorResultSystemMutation({
      monitor_config_key: monitorId,
      resolved_system_id: id,
    });
    if (isErrorResult(result)) {
      errorAlert(getErrorMessage(result.error));
    } else {
      // TODO: Add "view" button which will bring users to the system inventory with an asset tab open (not yet developed)
      successAlert(
        !systemKey
          ? `${name} has been added to the system inventory and all assets have been assigned to it.`
          : `All assets from ${name} have been assigned.`,
        `Confirmed`,
      );
    }
  };

  const handleIgnore = async () => {
    const result = await ignoreMonitorResultSystemMutation({
      monitor_config_key: monitorId,
      resolved_system_id: id || UNCATEGORIZED_SEGMENT,
    });
    if (isErrorResult(result)) {
      errorAlert(getErrorMessage(result.error));
    } else {
      successAlert(
        name
          ? `All assets from ${name} have been ignored.`
          : `All uncategorized assets have been ignored.`,
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
