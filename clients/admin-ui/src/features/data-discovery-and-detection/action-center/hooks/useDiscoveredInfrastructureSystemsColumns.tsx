import { AntButton as Button, Icons } from "fidesui";
import { useCallback, useMemo } from "react";

import { SystemStagedResourcesAggregateRecord } from "~/types/api";

import {
  useAddMonitorResultSystemsMutation,
  useIgnoreMonitorResultSystemsMutation,
} from "../action-center.slice";
import { ActionCenterTabHash } from "./useActionCenterTabs";

interface UseDiscoveredInfrastructureSystemsColumnsConfig {
  monitorId: string;
  onTabChange: (tab: ActionCenterTabHash) => Promise<void>;
  readonly: boolean;
  allowIgnore: boolean;
  rowClickUrl: (record: SystemStagedResourcesAggregateRecord) => string;
}

export const useDiscoveredInfrastructureSystemsColumns = ({
  monitorId,
  onTabChange,
  readonly,
  allowIgnore,
  rowClickUrl,
}: UseDiscoveredInfrastructureSystemsColumnsConfig) => {
  const [addMonitorResultSystemsMutation, { isLoading: isAddingResults }] =
    useAddMonitorResultSystemsMutation();
  const [ignoreMonitorResultSystemsMutation, { isLoading: isIgnoringResults }] =
    useIgnoreMonitorResultSystemsMutation();

  const handleAddSystem = useCallback(
    async (systemId: string) => {
      await addMonitorResultSystemsMutation({
        monitor_config_key: monitorId,
        resolved_system_ids: [systemId],
      });
    },
    [addMonitorResultSystemsMutation, monitorId],
  );

  const handleIgnoreSystem = useCallback(
    async (systemId: string) => {
      await ignoreMonitorResultSystemsMutation({
        monitor_config_key: monitorId,
        resolved_system_ids: [systemId],
      });
    },
    [ignoreMonitorResultSystemsMutation, monitorId],
  );

  const columns = useMemo(
    () => [
      {
        key: "name",
        dataIndex: "name",
        title: "System",
        sorter: true,
        onCell: (record: SystemStagedResourcesAggregateRecord) => ({
          onClick: () => {
            window.location.href = rowClickUrl(record);
          },
          style: { cursor: "pointer" },
        }),
      },
      {
        key: "actions",
        title: "Actions",
        width: 200,
        render: (_: unknown, record: SystemStagedResourcesAggregateRecord) => {
          if (readonly || !record.id) {
            return null;
          }

          return (
            <div className="flex gap-2">
              <Button
                size="small"
                icon={<Icons.Add />}
                onClick={(e) => {
                  e.stopPropagation();
                  handleAddSystem(record.id!);
                }}
                loading={isAddingResults}
                data-testid="add-system-button"
              >
                Add
              </Button>
              {allowIgnore && (
                <Button
                  size="small"
                  icon={<Icons.View />}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleIgnoreSystem(record.id!);
                  }}
                  loading={isIgnoringResults}
                  data-testid="ignore-system-button"
                >
                  Ignore
                </Button>
              )}
            </div>
          );
        },
      },
    ],
    [
      rowClickUrl,
      readonly,
      allowIgnore,
      handleAddSystem,
      handleIgnoreSystem,
      isAddingResults,
      isIgnoringResults,
    ],
  );

  return { columns };
};
