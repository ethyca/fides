import { useToast } from "fidesui";
import { uniq } from "lodash";
import { useRouter } from "next/router";
import { useCallback, useEffect, useMemo, useState } from "react";

import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import {
  ACTION_CENTER_ROUTE,
  SYSTEM_ROUTE,
  UNCATEGORIZED_SEGMENT,
} from "~/features/common/nav/routes";
import {
  BulkActionsConfig,
  useAntTable,
  useTableState,
} from "~/features/common/table/hooks/index";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import {
  ConsentStatus,
  DiffStatus,
  StagedResourceAPIResponse,
} from "~/types/api";

import {
  useAddMonitorResultAssetsMutation,
  useAddMonitorResultSystemsMutation,
  useGetDiscoveredAssetsQuery,
  useIgnoreMonitorResultAssetsMutation,
  useRestoreMonitorResultAssetsMutation,
  useUpdateAssetsMutation,
  useUpdateAssetsSystemMutation,
} from "../../../../data-discovery-and-detection/action-center/action-center.slice";
import { DiscoveredAssetsColumnKeys } from "../../../../data-discovery-and-detection/action-center/constants";
import useActionCenterTabs from "../../../../data-discovery-and-detection/action-center/hooks/useActionCenterTabs";
import { SuccessToastContent } from "../../../../data-discovery-and-detection/action-center/SuccessToastContent";

interface UseDiscoveredAssetsTableConfig {
  monitorId: string;
  systemId: string;
  onSystemName?: (name: string) => void;
}

/**
 * Specialized hook for DiscoveredAssetsTable that combines all table functionality
 * with specific business logic for asset management.
 */
export const useDiscoveredAssetsTable = ({
  monitorId,
  systemId,
  onSystemName,
}: UseDiscoveredAssetsTableConfig) => {
  const router = useRouter();
  const toast = useToast();

  // Local state
  const [systemName, setSystemName] = useState(systemId);
  const [firstItemConsentStatus, setFirstItemConsentStatus] = useState<
    ConsentStatus | null | undefined
  >();

  // Tab management
  const { filterTabs, activeTab, onTabChange, activeParams, actionsDisabled } =
    useActionCenterTabs(systemId);

  // Table state with URL synchronization
  const tableState = useTableState<DiscoveredAssetsColumnKeys>({
    urlSync: {
      pagination: true,
      sorting: true,
      filtering: true,
      search: true,
    },
    sorting: {
      defaultSortField: DiscoveredAssetsColumnKeys.CONSENT_AGGREGATED,
      defaultSortOrder: "ascend",
    },
  });

  // API query with table state
  const queryParams = useMemo(
    () => ({
      key: monitorId,
      page: tableState.pageIndex,
      size: tableState.pageSize,
      search: tableState.searchQuery,
      sort_by: tableState.sortField
        ? ([tableState.sortField] as (DiscoveredAssetsColumnKeys | "urn")[])
        : ([DiscoveredAssetsColumnKeys.CONSENT_AGGREGATED, "urn"] as (
            | DiscoveredAssetsColumnKeys
            | "urn"
          )[]),
      sort_asc: tableState.sortOrder !== "descend",
      ...activeParams,
      ...tableState.columnFilters,
    }),
    [
      monitorId,
      tableState.pageIndex,
      tableState.pageSize,
      tableState.searchQuery,
      tableState.sortField,
      tableState.sortOrder,
      activeParams,
      tableState.columnFilters,
    ],
  );

  const { data, isLoading, isFetching } =
    useGetDiscoveredAssetsQuery(queryParams);

  // Mutations
  const [addMonitorResultAssetsMutation, { isLoading: isAddingResults }] =
    useAddMonitorResultAssetsMutation();
  const [ignoreMonitorResultAssetsMutation, { isLoading: isIgnoringResults }] =
    useIgnoreMonitorResultAssetsMutation();
  const [addMonitorResultSystemsMutation, { isLoading: isAddingAllResults }] =
    useAddMonitorResultSystemsMutation();
  const [, { isLoading: isBulkUpdatingSystem }] =
    useUpdateAssetsSystemMutation();
  const [updateAssetsMutation] = useUpdateAssetsMutation();
  const [
    restoreMonitorResultAssetsMutation,
    { isLoading: isRestoringResults },
  ] = useRestoreMonitorResultAssetsMutation();

  // Bulk actions configuration
  const bulkActionsConfig: BulkActionsConfig<StagedResourceAPIResponse> =
    useMemo(
      () => ({
        getRowKey: (row) => row.urn,
        actions: [
          {
            key: "add",
            label: "Add",
            onClick: async (selectedRows) => {
              const urns = selectedRows.map((row) => row.urn);
              const result = await addMonitorResultAssetsMutation({
                urnList: urns,
              });

              const systemKey =
                selectedRows[0]?.user_assigned_system_key ||
                selectedRows[0]?.system_key;
              const allAssetsHaveSameSystemKey = selectedRows.every((a) => {
                const assetKey = a.user_assigned_system_key || a.system_key;
                return assetKey === systemKey;
              });
              const systemToLink = allAssetsHaveSameSystemKey
                ? systemKey
                : undefined;

              if (isErrorResult(result)) {
                toast(errorToastParams(getErrorMessage(result.error)));
              } else {
                toast(
                  successToastParams(
                    SuccessToastContent(
                      `${urns.length} assets from ${systemName} have been added to the system inventory.`,
                      systemToLink
                        ? () =>
                            router.push(
                              `${SYSTEM_ROUTE}/configure/${systemToLink}#assets`,
                            )
                        : () => router.push(SYSTEM_ROUTE),
                    ),
                  ),
                );
              }
            },
            loading: isAddingResults,
          },
          {
            key: "ignore",
            label: "Ignore",
            onClick: async (selectedRows) => {
              const urns = selectedRows.map((row) => row.urn);
              const result = await ignoreMonitorResultAssetsMutation({
                urnList: urns,
              });

              if (isErrorResult(result)) {
                toast(errorToastParams(getErrorMessage(result.error)));
              } else {
                toast(
                  successToastParams(
                    systemName === UNCATEGORIZED_SEGMENT
                      ? `${urns.length} uncategorized assets have been ignored and will not appear in future scans.`
                      : `${urns.length} assets from ${systemName} have been ignored and will not appear in future scans.`,
                    "Confirmed",
                  ),
                );
              }
            },
            loading: isIgnoringResults,
            disabled: () =>
              !!activeParams?.diff_status?.includes(DiffStatus.MUTED),
          },
          {
            key: "restore",
            label: "Restore",
            onClick: async (selectedRows) => {
              const urns = selectedRows.map((row) => row.urn);
              const result = await restoreMonitorResultAssetsMutation({
                urnList: urns,
              });

              if (isErrorResult(result)) {
                toast(errorToastParams(getErrorMessage(result.error)));
              } else {
                toast(
                  successToastParams(
                    `${urns.length} assets have been restored and will appear in future scans.`,
                    "Confirmed",
                  ),
                );
              }
            },
            loading: isRestoringResults,
            disabled: () =>
              !activeParams?.diff_status?.includes(DiffStatus.MUTED),
          },
        ],
      }),
      [
        addMonitorResultAssetsMutation,
        ignoreMonitorResultAssetsMutation,
        restoreMonitorResultAssetsMutation,
        isAddingResults,
        isIgnoringResults,
        isRestoringResults,
        systemName,
        activeParams?.diff_status,
        toast,
        router,
      ],
    );

  // Ant Design table integration
  const antTable = useAntTable<
    StagedResourceAPIResponse,
    DiscoveredAssetsColumnKeys
  >(
    {
      ...tableState,
      paginationConfig: tableState.paginationConfig,
    },
    {
      enableSelection: activeTab !== "recent-activity", // Assuming this is the tab hash
      getRowKey: (record) => record.urn,
      bulkActions: bulkActionsConfig,
      dataSource: data?.items,
      totalRows: data?.total ?? 0,
      isLoading,
      isFetching,
    },
  );

  // Business logic effects
  useEffect(() => {
    if (data) {
      const firstSystemName =
        data.items[0]?.system || systemName || systemId || "";
      setSystemName(firstSystemName);
      onSystemName?.(firstSystemName);
    }
  }, [data, systemId, onSystemName, systemName]);

  useEffect(() => {
    if (data?.items && !firstItemConsentStatus) {
      const consentStatus = data.items.find(
        (item) => item.consent_aggregated === ConsentStatus.WITHOUT_CONSENT,
      )?.consent_aggregated;
      setFirstItemConsentStatus(consentStatus);
    }
  }, [data, firstItemConsentStatus]);

  // Additional business logic functions
  const handleAddAll = useCallback(async () => {
    const assetCount = data?.items.length || 0;
    const result = await addMonitorResultSystemsMutation({
      monitor_config_key: monitorId,
      resolved_system_ids: [systemId],
    });

    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
    } else {
      router.push(`${ACTION_CENTER_ROUTE}/${monitorId}`);
      toast(
        successToastParams(
          `${assetCount} assets from ${systemName} have been added to the system inventory.`,
          "Confirmed",
        ),
      );
    }
  }, [
    data?.items.length,
    addMonitorResultSystemsMutation,
    monitorId,
    systemId,
    router,
    toast,
    systemName,
  ]);

  const handleBulkAddDataUse = useCallback(
    async (newDataUses: string[]) => {
      const selectedRows = Array.from(
        antTable.selectionState.selectedRowsMap.values(),
      );
      if (!selectedRows.length) {
        return;
      }

      const assets = selectedRows.map((asset) => {
        const userAssignedDataUses = uniq([
          ...(asset.user_assigned_data_uses || asset.data_uses || []),
          ...newDataUses,
        ]);
        return {
          urn: asset.urn,
          user_assigned_data_uses: userAssignedDataUses,
        };
      });

      const result = await updateAssetsMutation({ monitorId, assets });

      if (isErrorResult(result)) {
        toast(errorToastParams(getErrorMessage(result.error)));
      } else {
        toast(
          successToastParams(
            `Consent categories added to ${selectedRows.length} assets${
              systemName ? ` from ${systemName}` : ""
            }.`,
            "Confirmed",
          ),
        );
      }
    },
    [
      antTable.selectionState.selectedRowsMap,
      updateAssetsMutation,
      monitorId,
      toast,
      systemName,
    ],
  );

  return {
    // Table state and props
    ...tableState,
    ...antTable,

    // Data
    data,
    isLoading,
    isFetching,

    // Tab management
    filterTabs,
    activeTab,
    onTabChange,
    actionsDisabled,

    // Business state
    systemName,
    firstItemConsentStatus,

    // Business actions
    handleAddAll,
    handleBulkAddDataUse,

    // Loading states
    anyBulkActionIsLoading:
      isAddingResults ||
      isIgnoringResults ||
      isAddingAllResults ||
      isBulkUpdatingSystem ||
      isRestoringResults,
    isAddingAllResults,

    // Additional helpers
    disableAddAll: systemId === UNCATEGORIZED_SEGMENT,

    // Query parameters for column hook
    queryParamsForColumns: {
      monitorConfigId: monitorId,
      resolvedSystemId: systemId,
      diffStatus: activeParams?.diff_status,
      columnFilters: tableState.columnFilters,
      sortField: tableState.sortField,
      sortOrder: tableState.sortOrder,
      searchQuery: tableState.searchQuery,
    },
  };
};
