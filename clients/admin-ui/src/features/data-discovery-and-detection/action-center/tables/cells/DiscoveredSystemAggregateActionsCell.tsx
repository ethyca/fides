import {
  AntButton as Button,
  AntSpace as Space,
  AntTooltip as Tooltip,
  useToast,
} from "fidesui";
import { useRouter } from "next/router";

import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import {
  SYSTEM_ROUTE,
  UNCATEGORIZED_SEGMENT,
} from "~/features/common/nav/routes";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import styles from "~/features/ToastLink.module.scss";

import {
  useAddMonitorResultSystemsMutation,
  useIgnoreMonitorResultSystemsMutation,
} from "../../action-center.slice";
import { MonitorSystemAggregate } from "../../types";

interface DiscoveredSystemActionsCellProps {
  monitorId: string;
  system: MonitorSystemAggregate;
  allowIgnore?: boolean;
}

export const DiscoveredSystemActionsCell = ({
  monitorId,
  system,
  allowIgnore,
}: DiscoveredSystemActionsCellProps) => {
  const [addMonitorResultSystemsMutation, { isLoading: isAddingResults }] =
    useAddMonitorResultSystemsMutation();
  const [ignoreMonitorResultSystemsMutation, { isLoading: isIgnoringResults }] =
    useIgnoreMonitorResultSystemsMutation();

  const router = useRouter();
  const toast = useToast();

  const anyActionIsLoading = isAddingResults || isIgnoringResults;

  const {
    id: resolvedSystemId,
    name: systemName,
    system_key: systemKey,
    total_updates: totalUpdates,
  } = system;

  // TODO: get system key to navigate
  const addSuccessToastContent = (systemName: string, systemKey?: string) => (
    <>
      {`${systemName} and ${totalUpdates} assets have been added to the system inventory. ${systemName} is now configured for consent.`}
      {systemKey && (
        <Button
          className={styles.toastLink}
          size="small"
          type="link"
          role="link"
          onClick={() => router.push(`${SYSTEM_ROUTE}/configure/${systemKey}`)}
        >
          View
        </Button>
      )}
    </>
  );

  const handleAdd = async () => {
    const result = await addMonitorResultSystemsMutation({
      monitor_config_key: monitorId,
      resolved_system_ids: [resolvedSystemId],
    });
    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
    } else {
      toast(
        successToastParams(
          !systemKey
            ? `${systemName} and ${totalUpdates} assets have been added to the system inventory. ${systemName} is now configured for consent.`
            : `${totalUpdates} assets from ${systemName} have been added to the system inventory.`,
          `Confirmed`,
        ),
      );
    }
  };

  const handleIgnore = async () => {
    const result = await ignoreMonitorResultSystemsMutation({
      monitor_config_key: monitorId,
      resolved_system_ids: [resolvedSystemId || UNCATEGORIZED_SEGMENT],
    });
    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
    } else {
      toast(
        successToastParams(
          systemName
            ? `${totalUpdates} assets from ${systemName} have been ignored and will not appear in future scans.`
            : `${totalUpdates} uncategorized assets have been ignored and will not appear in future scans.`,
          `Confirmed`,
        ),
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
      {allowIgnore && (
        <Button
          data-testid="ignore-btn"
          size="small"
          onClick={handleIgnore}
          disabled={anyActionIsLoading}
          loading={isIgnoringResults}
        >
          Ignore
        </Button>
      )}
    </Space>
  );
};
