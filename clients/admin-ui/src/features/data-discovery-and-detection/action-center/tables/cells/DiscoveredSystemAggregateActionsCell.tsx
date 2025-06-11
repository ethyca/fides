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
import { getIndexFromHash } from "~/features/data-discovery-and-detection/action-center/tables/useActionCenterTabs";
import { successToastContent } from "~/features/data-discovery-and-detection/action-center/utils/successToastContent";
import { SystemStagedResourcesAggregateRecord } from "~/types/api";

import {
  useAddMonitorResultSystemsMutation,
  useIgnoreMonitorResultSystemsMutation,
} from "../../action-center.slice";

interface DiscoveredSystemActionsCellProps {
  monitorId: string;
  system: SystemStagedResourcesAggregateRecord;
  allowIgnore?: boolean;
  onTabChange: (index: number) => void;
}

export const DiscoveredSystemActionsCell = ({
  monitorId,
  system,
  allowIgnore,
  onTabChange,
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

  const handleAdd = async () => {
    const result = await addMonitorResultSystemsMutation({
      monitor_config_key: monitorId,
      resolved_system_ids: [resolvedSystemId!],
    });
    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
    } else {
      const promotedSystemKey = result.data?.items?.[0]?.promoted_system_key;
      const systemToLink = promotedSystemKey || systemKey;
      const href = `${SYSTEM_ROUTE}/configure/${systemToLink}#assets`;
      toast(
        successToastParams(
          successToastContent(
            systemKey
              ? `${totalUpdates} assets from ${systemName} have been added to the system inventory.`
              : `${systemName} and ${totalUpdates} assets have been added to the system inventory. ${systemName} is now configured for consent.`,
            systemToLink ? () => router.push(href) : undefined,
          ),
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
          successToastContent(
            systemName
              ? `${totalUpdates} assets from ${systemName} have been ignored and will not appear in future scans.`
              : `${totalUpdates} uncategorized assets have been ignored and will not appear in future scans.`,
            () => onTabChange(getIndexFromHash("#ignored")!),
          ),
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
