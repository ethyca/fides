import {
  AntColumnsType as ColumnsType,
  AntDefaultOptionType as DefaultOptionType,
  AntSpace as Space,
  AntText as Text,
  formatIsoLocation,
  isoStringToEntry,
  useToast,
} from "fidesui";
import { uniq } from "lodash";
import { useRouter } from "next/router";
import { useCallback, useEffect, useMemo, useState } from "react";

import { useFeatures } from "~/features/common/features/features.slice";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import {
  ACTION_CENTER_WEBSITE_MONITOR_ROUTE,
  SYSTEM_ROUTE,
  UNCATEGORIZED_SEGMENT,
} from "~/features/common/nav/routes";
import { PRIVACY_NOTICE_REGION_RECORD } from "~/features/common/privacy-notice-regions";
import {
  ListExpandableCell,
  TagExpandableCell,
} from "~/features/common/table/cells";
import { expandCollapseAllMenuItems } from "~/features/common/table/cells/constants";
import { useAntTable, useTableState } from "~/features/common/table/hooks";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import { convertToAntFilters } from "~/features/common/utils";
import {
  AlertLevel,
  ConsentAlertInfo,
  ConsentStatus,
  PrivacyNoticeRegion,
  StagedResourceAPIResponse,
} from "~/types/api";

import {
  useAddMonitorResultAssetsMutation,
  useAddMonitorResultSystemsMutation,
  useGetDiscoveredAssetsQuery,
  useGetWebsiteMonitorResourceFiltersQuery,
  useIgnoreMonitorResultAssetsMutation,
  useRestoreMonitorResultAssetsMutation,
  useUpdateAssetsMutation,
  useUpdateAssetsSystemMutation,
} from "../action-center.slice";
import {
  DiscoveredAssetsColumnKeys,
  DiscoveryStatusDisplayNames,
} from "../constants";
import { DiscoveryStatusIcon } from "../DiscoveryStatusIcon";
import { SuccessToastContent } from "../SuccessToastContent";
import { DiscoveredAssetActionsCell } from "../tables/cells/DiscoveredAssetActionsCell";
import DiscoveredAssetDataUseCell from "../tables/cells/DiscoveredAssetDataUseCell";
import { DiscoveryStatusBadgeCell } from "../tables/cells/DiscoveryStatusBadgeCell";
import { SystemCell } from "../tables/cells/SystemCell";
import isConsentCategory from "../utils/isConsentCategory";
import useActionCenterTabs, {
  ActionCenterTabHash,
} from "./useActionCenterTabs";

interface UseDiscoveredAssetsTableConfig {
  monitorId: string;
  systemId: string;
  consentStatus?: ConsentAlertInfo | null;
  onShowComplianceIssueDetails?: (
    stagedResource: StagedResourceAPIResponse,
  ) => void;
}

export const useDiscoveredAssetsTable = ({
  monitorId,
  systemId,
  consentStatus,
  onShowComplianceIssueDetails,
}: UseDiscoveredAssetsTableConfig) => {
  const router = useRouter();
  const toast = useToast();

  const [systemName, setSystemName] = useState(systemId);
  const [isLocationsExpanded, setIsLocationsExpanded] = useState(false);
  const [isPagesExpanded, setIsPagesExpanded] = useState(false);
  const [isDataUsesExpanded, setIsDataUsesExpanded] = useState(false);
  const [locationsVersion, setLocationsVersion] = useState(0);
  const [pagesVersion, setPagesVersion] = useState(0);
  const [dataUsesVersion, setDataUsesVersion] = useState(0);
  const { flags } = useFeatures();
  const { assetConsentStatusLabels } = flags;

  const { filterTabs, activeTab, onTabChange, activeParams, actionsDisabled } =
    useActionCenterTabs(systemId);

  const tableState = useTableState<DiscoveredAssetsColumnKeys>({
    sorting: {
      validColumns: Object.values(DiscoveredAssetsColumnKeys),
    },
  });

  const {
    columnFilters,
    pageIndex,
    pageSize,
    resetState,
    sortKey,
    sortOrder,
    searchQuery,
    updateSearch,
    updateFilters,
    updateSorting,
    updatePageIndex,
    updatePageSize,
  } = tableState;

  const { data, isLoading, isFetching } = useGetDiscoveredAssetsQuery({
    key: monitorId,
    page: pageIndex,
    size: pageSize,
    search: searchQuery,
    sort_by: sortKey
      ? [sortKey] // User selected a column to sort by
      : [DiscoveredAssetsColumnKeys.NAME], // Default,
    sort_asc: sortOrder !== "descend",
    ...activeParams,
    ...columnFilters,
  });

  const [addMonitorResultAssetsMutation, { isLoading: isAddingResults }] =
    useAddMonitorResultAssetsMutation();
  const [ignoreMonitorResultAssetsMutation, { isLoading: isIgnoringResults }] =
    useIgnoreMonitorResultAssetsMutation();
  const [addMonitorResultSystemsMutation, { isLoading: isAddingAllResults }] =
    useAddMonitorResultSystemsMutation();
  const [updateAssetsSystemMutation, { isLoading: isBulkUpdatingSystem }] =
    useUpdateAssetsSystemMutation();
  const [updateAssetsMutation, { isLoading: isBulkAddingDataUses }] =
    useUpdateAssetsMutation();
  const [
    restoreMonitorResultAssetsMutation,
    { isLoading: isRestoringResults },
  ] = useRestoreMonitorResultAssetsMutation();

  const anyBulkActionIsLoading =
    isAddingResults ||
    isIgnoringResults ||
    isAddingAllResults ||
    isBulkUpdatingSystem ||
    isRestoringResults ||
    isBulkAddingDataUses;

  const disableAddAll =
    anyBulkActionIsLoading || systemId === UNCATEGORIZED_SEGMENT;

  const { data: filterOptions } = useGetWebsiteMonitorResourceFiltersQuery({
    monitor_config_id: monitorId,
    resolved_system_id: systemId,
    diff_status: activeParams?.diff_status,
    search: searchQuery,
    ...columnFilters,
  });

  const antTableConfig = useMemo(
    () => ({
      enableSelection: activeTab !== ActionCenterTabHash.ADDED,
      getRowKey: (record: StagedResourceAPIResponse) => record.urn,
      isLoading,
      isFetching,
      dataSource: data?.items || [],
      totalRows: data?.total || 0,
      sortBy: [DiscoveredAssetsColumnKeys.NAME],
      sortAsc: true,
      customTableProps: {
        locale: {
          emptyText: (
            <div>
              <div>All caught up!</div>
            </div>
          ),
        },
        sticky: {
          offsetHeader: 40,
        },
      },
    }),
    [activeTab, isLoading, isFetching, data?.items, data?.total],
  );

  const antTable = useAntTable<
    StagedResourceAPIResponse,
    DiscoveredAssetsColumnKeys
  >(tableState, antTableConfig);

  const {
    selectedKeys: selectedUrns,
    selectedRows,
    resetSelections,
  } = antTable;

  const columns: ColumnsType<StagedResourceAPIResponse> = useMemo(() => {
    const baseColumns: ColumnsType<StagedResourceAPIResponse> = [
      {
        title: "Asset",
        dataIndex: DiscoveredAssetsColumnKeys.NAME,
        key: DiscoveredAssetsColumnKeys.NAME,
        sorter: true,
        sortOrder:
          sortKey === DiscoveredAssetsColumnKeys.NAME ? sortOrder : null,
        render: (name) => (
          <Text ellipsis={{ tooltip: true }} style={{ maxWidth: 300 }}>
            {name}
          </Text>
        ),
        fixed: "left",
      },
      {
        title: "Type",
        dataIndex: DiscoveredAssetsColumnKeys.RESOURCE_TYPE,
        key: DiscoveredAssetsColumnKeys.RESOURCE_TYPE,
        sorter: true,
        sortOrder:
          sortKey === DiscoveredAssetsColumnKeys.RESOURCE_TYPE
            ? sortOrder
            : null,
        filters: convertToAntFilters(filterOptions?.resource_type),
        filteredValue: columnFilters?.resource_type || null,
      },
      {
        title: "System",
        dataIndex: DiscoveredAssetsColumnKeys.SYSTEM,
        key: DiscoveredAssetsColumnKeys.SYSTEM,
        render: (_, record) =>
          !!record.monitor_config_id && (
            <SystemCell
              aggregateSystem={record}
              monitorConfigId={record.monitor_config_id}
              readonly={
                actionsDisabled || activeTab === ActionCenterTabHash.IGNORED
              }
              onChange={() => {
                resetSelections();
              }}
            />
          ),
      },
      {
        title: "Categories of consent",
        key: DiscoveredAssetsColumnKeys.DATA_USES,
        menu: {
          items: expandCollapseAllMenuItems,
          onClick: (e) => {
            e.domEvent.stopPropagation();
            if (e.key === "expand-all") {
              setIsDataUsesExpanded(true);
              setDataUsesVersion((prev) => prev + 1);
            } else if (e.key === "collapse-all") {
              setIsDataUsesExpanded(false);
              setDataUsesVersion((prev) => prev + 1);
            }
          },
        },
        filters: convertToAntFilters(
          filterOptions?.data_uses?.filter((use) => isConsentCategory(use)),
        ),
        filteredValue: columnFilters?.data_uses || null,
        render: (_, record) => (
          <DiscoveredAssetDataUseCell
            asset={record}
            readonly={
              actionsDisabled || activeTab === ActionCenterTabHash.IGNORED
            }
            columnState={{
              isExpanded: isDataUsesExpanded,
              version: dataUsesVersion,
            }}
            onChange={() => {
              resetSelections();
            }}
          />
        ),
      },
      {
        title: "Locations",
        dataIndex: DiscoveredAssetsColumnKeys.LOCATIONS,
        key: DiscoveredAssetsColumnKeys.LOCATIONS,
        menu: {
          items: expandCollapseAllMenuItems,
          onClick: (e) => {
            e.domEvent.stopPropagation();
            if (e.key === "expand-all") {
              setIsLocationsExpanded(true);
              setLocationsVersion((prev) => prev + 1);
            } else if (e.key === "collapse-all") {
              setIsLocationsExpanded(false);
              setLocationsVersion((prev) => prev + 1);
            }
          },
        },
        filters: convertToAntFilters(filterOptions?.locations, (location) => {
          const isoEntry = isoStringToEntry(location);

          return isoEntry
            ? formatIsoLocation({ isoEntry })
            : (PRIVACY_NOTICE_REGION_RECORD[location as PrivacyNoticeRegion] ??
                location);
        }),
        filteredValue: columnFilters?.locations || null,
        render: (locations: PrivacyNoticeRegion[]) => {
          return (
            <TagExpandableCell
              values={
                locations?.map((location) => {
                  const isoEntry = isoStringToEntry(location);
                  return {
                    label: isoEntry
                      ? formatIsoLocation({ isoEntry })
                      : (PRIVACY_NOTICE_REGION_RECORD[location] ??
                        location) /* fallback on internal list for now */,
                    key: location,
                  };
                }) ?? []
              }
              columnState={{
                isExpanded: isLocationsExpanded,
                version: locationsVersion,
              }}
            />
          );
        },
      },
      {
        title: "Domain",
        dataIndex: DiscoveredAssetsColumnKeys.DOMAIN,
        key: DiscoveredAssetsColumnKeys.DOMAIN,
        // Domain filtering will be handled via search instead of column filters
      },
      {
        title: "Detected on",
        dataIndex: DiscoveredAssetsColumnKeys.PAGE,
        menu: {
          items: expandCollapseAllMenuItems,
          onClick: (e) => {
            e.domEvent.stopPropagation();
            if (e.key === "expand-all") {
              setIsPagesExpanded(true);
              setPagesVersion((prev) => prev + 1);
            } else if (e.key === "collapse-all") {
              setIsPagesExpanded(false);
              setPagesVersion((prev) => prev + 1);
            }
          },
        },
        key: DiscoveredAssetsColumnKeys.PAGE,
        render: (pages: string[]) => (
          <ListExpandableCell
            values={pages}
            valueSuffix="pages"
            columnState={{
              isExpanded: isPagesExpanded,
              version: pagesVersion,
            }}
          />
        ),
      },
    ];

    // Add compliance column if flag is enabled
    if (assetConsentStatusLabels) {
      baseColumns.push({
        title: () => (
          <Space>
            <div>Compliance</div>
            {consentStatus?.status === AlertLevel.ALERT && (
              <DiscoveryStatusIcon consentStatus={consentStatus} />
            )}
          </Space>
        ),
        dataIndex: DiscoveredAssetsColumnKeys.CONSENT_AGGREGATED,
        key: DiscoveredAssetsColumnKeys.CONSENT_AGGREGATED,
        sorter: true,
        sortOrder:
          sortKey === DiscoveredAssetsColumnKeys.CONSENT_AGGREGATED
            ? sortOrder
            : null,
        filters: convertToAntFilters(
          filterOptions?.[DiscoveredAssetsColumnKeys.CONSENT_AGGREGATED],
          (status) =>
            DiscoveryStatusDisplayNames[status as ConsentStatus] ?? status,
        ),
        filteredValue:
          columnFilters?.[DiscoveredAssetsColumnKeys.CONSENT_AGGREGATED] ||
          null,
        render: (consentAggregated: ConsentStatus, record) => (
          <DiscoveryStatusBadgeCell
            consentAggregated={consentAggregated ?? ConsentStatus.UNKNOWN}
            stagedResource={record}
          />
        ),
      });
    }

    // Add actions column if not readonly
    if (!actionsDisabled) {
      baseColumns.push({
        title: "Actions",
        key: DiscoveredAssetsColumnKeys.ACTIONS,
        fixed: "right",
        render: (_, record) => (
          <DiscoveredAssetActionsCell
            asset={record}
            onTabChange={onTabChange}
            showComplianceIssueDetails={onShowComplianceIssueDetails}
          />
        ),
      });
    }

    return baseColumns;
  }, [
    sortKey,
    sortOrder,
    filterOptions,
    columnFilters,
    assetConsentStatusLabels,
    actionsDisabled,
    activeTab,
    isDataUsesExpanded,
    dataUsesVersion,
    resetSelections,
    isLocationsExpanded,
    locationsVersion,
    isPagesExpanded,
    pagesVersion,
    consentStatus,
    onTabChange,
    onShowComplianceIssueDetails,
  ]);

  // Business logic effects
  useEffect(() => {
    if (data) {
      const firstSystemName =
        data.items[0]?.system || systemName || systemId || "";
      setSystemName(firstSystemName);
    }
  }, [data, systemId, systemName]);

  const handleBulkAdd = useCallback(async () => {
    const result = await addMonitorResultAssetsMutation({
      urnList: selectedUrns,
    });

    const systemKey =
      selectedRows[0]?.user_assigned_system_key || selectedRows[0]?.system_key;
    const allAssetsHaveSameSystemKey = selectedRows.every((a) => {
      const assetKey = a.user_assigned_system_key || a.system_key;
      return assetKey === systemKey;
    });

    const systemToLink = allAssetsHaveSameSystemKey ? systemKey : undefined;

    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
    } else {
      toast(
        successToastParams(
          SuccessToastContent(
            `${selectedUrns.length} assets from ${systemName} have been added to the system inventory.`,
            systemToLink
              ? () =>
                  router.push(
                    `${SYSTEM_ROUTE}/configure/${systemToLink}#assets`,
                  )
              : () => router.push(SYSTEM_ROUTE),
          ),
        ),
      );
      resetSelections();
    }
  }, [
    addMonitorResultAssetsMutation,
    selectedUrns,
    selectedRows,
    systemName,
    toast,
    router,
    resetSelections,
  ]);

  const handleBulkAssignSystem = useCallback(
    async (selectedSystem?: DefaultOptionType) => {
      if (typeof selectedSystem?.value === "string") {
        const result = await updateAssetsSystemMutation({
          monitorId,
          urnList: selectedUrns,
          systemKey: selectedSystem.value,
        });
        if (isErrorResult(result)) {
          toast(errorToastParams(getErrorMessage(result.error)));
        } else {
          toast(
            successToastParams(
              `${selectedUrns.length} assets have been assigned to ${selectedSystem.label}.`,
              `Confirmed`,
            ),
          );
          resetSelections();
        }
      }
    },
    [
      updateAssetsSystemMutation,
      monitorId,
      selectedUrns,
      toast,
      resetSelections,
    ],
  );

  const handleBulkAddDataUse = useCallback(
    async (newDataUses: string[]) => {
      if (!selectedRows.length) {
        return;
      }
      const assets = selectedRows.map((asset) => {
        // eslint-disable-next-line @typescript-eslint/naming-convention
        const user_assigned_data_uses = uniq([
          ...(asset.preferred_data_uses || []),
          ...newDataUses,
        ]);
        return {
          urn: asset.urn,
          user_assigned_data_uses,
        };
      });
      const result = await updateAssetsMutation({
        monitorId,
        assets,
      });
      if (isErrorResult(result)) {
        toast(errorToastParams(getErrorMessage(result.error)));
      } else {
        toast(
          successToastParams(
            `Consent categories added to ${selectedUrns.length} assets${
              systemName ? ` from ${systemName}` : ""
            }.`,
            `Confirmed`,
          ),
        );
        resetSelections();
      }
    },
    [
      selectedRows,
      updateAssetsMutation,
      monitorId,
      selectedUrns,
      systemName,
      toast,
      resetSelections,
    ],
  );

  const handleBulkIgnore = useCallback(async () => {
    const result = await ignoreMonitorResultAssetsMutation({
      urnList: selectedUrns,
    });
    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
    } else {
      toast(
        successToastParams(
          systemName === UNCATEGORIZED_SEGMENT
            ? `${selectedUrns.length} uncategorized assets have been ignored and will not appear in future scans.`
            : `${selectedUrns.length} assets from ${systemName} have been ignored and will not appear in future scans.`,
          `Confirmed`,
        ),
      );
      resetSelections();
    }
  }, [
    ignoreMonitorResultAssetsMutation,
    selectedUrns,
    systemName,
    toast,
    resetSelections,
  ]);

  const handleBulkRestore = useCallback(async () => {
    const result = await restoreMonitorResultAssetsMutation({
      urnList: selectedUrns,
    });
    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
    } else {
      toast(
        successToastParams(
          `${selectedUrns.length} assets have been restored and will appear in future scans.`,
          `Confirmed`,
        ),
      );
      resetSelections();
    }
  }, [
    restoreMonitorResultAssetsMutation,
    selectedUrns,
    toast,
    resetSelections,
  ]);

  const handleAddAll = useCallback(async () => {
    const assetCount = data?.items.length || 0;
    const result = await addMonitorResultSystemsMutation({
      monitor_config_key: monitorId,
      resolved_system_ids: [systemId],
    });

    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
    } else {
      router.push({
        pathname: ACTION_CENTER_WEBSITE_MONITOR_ROUTE,
        query: {
          monitorId: encodeURIComponent(monitorId),
        },
      });
      toast(
        successToastParams(
          `${assetCount} assets from ${systemName} have been added to the system inventory.`,
          `Confirmed`,
        ),
      );
      resetSelections();
    }
  }, [
    data?.items.length,
    addMonitorResultSystemsMutation,
    monitorId,
    systemId,
    router,
    toast,
    systemName,
    resetSelections,
  ]);

  const handleTabChange = useCallback(
    async (tab: ActionCenterTabHash) => {
      await onTabChange(tab);
      resetState();
      resetSelections();
    },
    [onTabChange, resetState, resetSelections],
  );

  return {
    // Table state and data
    columns,
    data,
    isLoading,
    isFetching,
    tableState,
    searchQuery,
    updateSearch,
    updateFilters,
    updateSorting,
    updatePageIndex,
    updatePageSize,
    resetState,

    // Ant Design table integration
    tableProps: antTable.tableProps,
    selectionProps: antTable.selectionProps,

    // Tab management
    filterTabs,
    activeTab,
    handleTabChange,
    activeParams,
    actionsDisabled,

    // Selection (from antTable)
    selectedRows,
    selectedUrns,
    hasSelectedRows: antTable.hasSelectedRows,
    resetSelections,

    // Business state
    systemName,
    consentStatus,

    // Business actions
    handleBulkAdd,
    handleBulkAssignSystem,
    handleBulkAddDataUse,
    handleBulkIgnore,
    handleBulkRestore,
    handleAddAll,

    // Loading states
    anyBulkActionIsLoading,
    isAddingResults,
    isIgnoringResults,
    isAddingAllResults,
    isBulkUpdatingSystem,
    isBulkAddingDataUses,
    isRestoringResults,
    disableAddAll,
  };
};
