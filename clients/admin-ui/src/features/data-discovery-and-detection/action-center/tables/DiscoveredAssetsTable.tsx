import {
  AntButton as Button,
  AntDefaultOptionType as DefaultOptionType,
  AntDropdown as Dropdown,
  AntEmpty as Empty,
  AntFilterValue as FilterValue,
  AntFlex as Flex,
  AntSorterResult as SorterResult,
  AntSpace as Space,
  AntTable as Table,
  AntTablePaginationConfig as TablePaginationConfig,
  AntTabs as Tabs,
  AntTooltip as Tooltip,
  Icons,
  useToast,
} from "fidesui";
import { uniq } from "lodash";
import { useRouter } from "next/router";
import { useEffect, useState } from "react";

import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import {
  ACTION_CENTER_ROUTE,
  SYSTEM_ROUTE,
  UNCATEGORIZED_SEGMENT,
} from "~/features/common/nav/routes";
import { useTableState } from "~/features/common/table/hooks";
import { SelectedText } from "~/features/common/table/SelectedText";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import {
  ConsentStatus,
  DiffStatus,
  StagedResourceAPIResponse,
} from "~/types/api";

import { DebouncedSearchInput } from "../../../common/DebouncedSearchInput";
import {
  useAddMonitorResultAssetsMutation,
  useAddMonitorResultSystemsMutation,
  useGetDiscoveredAssetsQuery,
  useIgnoreMonitorResultAssetsMutation,
  useRestoreMonitorResultAssetsMutation,
  useUpdateAssetsMutation,
  useUpdateAssetsSystemMutation,
} from "../action-center.slice";
import AddDataUsesModal from "../AddDataUsesModal";
import { AssignSystemModal } from "../AssignSystemModal";
import { ConsentBreakdownModal } from "../ConsentBreakdownModal";
import { DiscoveredAssetsColumnKeys } from "../constants";
import useActionCenterTabs, {
  ActionCenterTabHash,
} from "../hooks/useActionCenterTabs";
import { useDiscoveredAssetsTable } from "../hooks/useDiscoveredAssetsTable";
import { SuccessToastContent } from "../SuccessToastContent";

interface DiscoveredAssetsTableProps {
  monitorId: string;
  systemId: string;
  onSystemName?: (name: string) => void;
}

export const DiscoveredAssetsTable = ({
  monitorId,
  systemId,
  onSystemName,
}: DiscoveredAssetsTableProps) => {
  const router = useRouter();
  const [firstItemConsentStatus, setFirstItemConsentStatus] = useState<
    ConsentStatus | null | undefined
  >();

  const [systemName, setSystemName] = useState(systemId);

  // Selection state
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const [selectedRowsMap, setSelectedRowsMap] = useState<
    Map<string, StagedResourceAPIResponse>
  >(new Map());

  const resetSelections = () => {
    setSelectedRowKeys([]);
    setSelectedRowsMap(new Map());
  };

  const [isAssignSystemModalOpen, setIsAssignSystemModalOpen] =
    useState<boolean>(false);
  const [isAddDataUseModalOpen, setIsAddDataUseModalOpen] =
    useState<boolean>(false);
  const [consentBreakdownModalData, setConsentBreakdownModalData] = useState<{
    stagedResource: StagedResourceAPIResponse;
    status: ConsentStatus;
  } | null>(null);

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
    isRestoringResults;

  const disableAddAll =
    anyBulkActionIsLoading || systemId === UNCATEGORIZED_SEGMENT;

  // Table state with URL synchronization for search, sorting, filtering, and pagination (complete implementation)
  const tableState = useTableState<DiscoveredAssetsColumnKeys>({
    urlSync: {
      pagination: true, // Now implementing pagination
      sorting: true, // Already implemented
      filtering: true, // Already implemented
      search: true, // Already implemented
    },
    pagination: {
      defaultPageSize: 10, // Start with 10 per page for testing
    },
  });

  // Use tableState values instead of local state
  const { columnFilters, pageIndex, pageSize } = tableState;

  // Use tableState sorting instead of local state - now properly typed!
  const { sortField, sortOrder } = tableState;

  // Use tableState.searchQuery instead of local state
  const searchQuery = tableState.searchQuery || "";

  const toast = useToast();

  const { filterTabs, activeTab, onTabChange, activeParams, actionsDisabled } =
    useActionCenterTabs(systemId);

  const { data, isLoading, isFetching } = useGetDiscoveredAssetsQuery({
    key: monitorId,
    page: pageIndex,
    size: pageSize,
    search: tableState.searchQuery,
    sort_by: sortField
      ? [sortField] // User selected a column to sort by
      : [DiscoveredAssetsColumnKeys.CONSENT_AGGREGATED, "urn"], // Default
    sort_asc: tableState.sortOrder !== "descend",
    ...activeParams,
    ...columnFilters,
  });

  const resetTableState = () => {
    resetSelections();
    tableState.updateFilters({}); // Clear filters using tableState
    tableState.updateSearch(""); // Clear search using tableState
    tableState.updateSorting(undefined, undefined); // Clear sorting using tableState
    tableState.updatePagination(1); // Reset to page 1
  };

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
      // this ensures that the column header remembers the consent status
      // even when the user navigates to a different paginated page
      const consentStatus = data.items.find(
        (item) => item.consent_aggregated === ConsentStatus.WITHOUT_CONSENT,
      )?.consent_aggregated;
      setFirstItemConsentStatus(consentStatus);
    }
  }, [data, firstItemConsentStatus]);

  const handleShowBreakdown = (
    stagedResource: StagedResourceAPIResponse,
    status: ConsentStatus,
  ) => {
    setConsentBreakdownModalData({ stagedResource, status });
  };

  const handleCloseBreakdown = () => {
    setConsentBreakdownModalData(null);
  };

  const { columns } = useDiscoveredAssetsTable({
    readonly: actionsDisabled ?? false,
    onTabChange,
    aggregatedConsent: firstItemConsentStatus,
    onShowBreakdown: handleShowBreakdown,
    monitorConfigId: monitorId,
    resolvedSystemId: systemId,
    diffStatus: activeParams?.diff_status,
    columnFilters,
    sortField,
    sortOrder,
    searchQuery: tableState.searchQuery,
  });

  // Get selected URNs from the map instead of selectedRows
  const selectedUrns = Array.from(selectedRowsMap.keys());
  const selectedRows = Array.from(selectedRowsMap.values());

  const handleBulkAdd = async () => {
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
  };

  const handleBulkAssignSystem = async (selectedSystem?: DefaultOptionType) => {
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
      }
    }
    setIsAssignSystemModalOpen(false);
  };

  const handleBulkAddDataUse = async (newDataUses: string[]) => {
    if (!selectedRows.length) {
      return;
    }
    const assets = selectedRows.map((asset) => {
      // eslint-disable-next-line @typescript-eslint/naming-convention
      const user_assigned_data_uses = uniq([
        ...(asset.user_assigned_data_uses || asset.data_uses || []),
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
    }
    setIsAddDataUseModalOpen(false);
  };

  const handleBulkIgnore = async () => {
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
  };

  const handleBulkRestore = async () => {
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
  };

  const handleAddAll = async () => {
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
          `Confirmed`,
        ),
      );
      resetSelections();
    }
  };

  const handleTabChange = async (tab: ActionCenterTabHash) => {
    await onTabChange(tab);
    resetTableState();
  };

  // Update selectedRowKeys to only show current page selections when data changes
  useEffect(() => {
    if (data?.items) {
      const currentPageSelectedKeys = data.items
        .filter((item) => selectedRowsMap.has(item.urn))
        .map((item) => item.urn);
      setSelectedRowKeys(currentPageSelectedKeys);
    }
  }, [data, selectedRowsMap]);

  const rowSelection = {
    selectedRowKeys,
    onChange: (
      newSelectedRowKeys: React.Key[],
      newSelectedRows: StagedResourceAPIResponse[],
    ) => {
      setSelectedRowKeys(newSelectedRowKeys);

      // Update the map with current page selections
      const newMap = new Map(selectedRowsMap);

      // Remove deselected items from current page
      if (data?.items) {
        data.items.forEach((item) => {
          if (!newSelectedRowKeys.includes(item.urn)) {
            newMap.delete(item.urn);
          }
        });
      }

      // Add newly selected items
      newSelectedRows.forEach((row) => {
        newMap.set(row.urn, row);
      });

      setSelectedRowsMap(newMap);
    },
  };

  const handleTableChange = (
    pagination: TablePaginationConfig,
    filters: Record<string, FilterValue | null>,
    sorter:
      | SorterResult<StagedResourceAPIResponse>
      | SorterResult<StagedResourceAPIResponse>[],
  ) => {
    // Check if this is just a pagination change (page or pageSize changed)
    const isPaginationChange =
      pagination.current !== pageIndex || pagination.pageSize !== pageSize;

    // Handle pagination with tableState
    if (isPaginationChange) {
      tableState.updatePagination(pagination.current || 1, pagination.pageSize);
    } else {
      tableState.updatePagination(1); // Reset to page 1 for sorting/filtering changes
      // Only update filters when it's not a pagination change
      tableState.updateFilters(filters || {});
    }

    // Handle sorting with tableState (only if sorting actually changed)
    const newSortField =
      sorter && !Array.isArray(sorter)
        ? (sorter.field as DiscoveredAssetsColumnKeys)
        : undefined;
    const newSortOrder =
      sorter && !Array.isArray(sorter) && sorter.order !== null
        ? sorter.order
        : undefined;

    // Only update sorting if this is not just a pagination change
    if (!isPaginationChange) {
      tableState.updateSorting(newSortField, newSortOrder);
    }
  };

  if (!monitorId || !systemId) {
    return null;
  }

  return (
    <>
      <Tabs
        items={filterTabs.map((tab) => ({
          key: tab.hash,
          label: tab.label,
        }))}
        activeKey={activeTab}
        onChange={(tab) => handleTabChange(tab as ActionCenterTabHash)}
      />
      <Flex justify="space-between" align="center" className="mb-4">
        <DebouncedSearchInput
          value={searchQuery}
          onChange={tableState.updateSearch}
          placeholder="Search by asset name..."
        />
        <Space size="large">
          {!!selectedUrns.length && (
            <SelectedText count={selectedUrns.length} />
          )}
          <Space size="small">
            <Button onClick={resetTableState} data-testid="clear-filters">
              Clear filters
            </Button>
            <Dropdown
              menu={{
                items: [
                  {
                    key: "add",
                    label: "Add",
                    onClick: handleBulkAdd,
                  },
                  {
                    key: "add-data-use",
                    label: "Add consent category",
                    onClick: () => setIsAddDataUseModalOpen(true),
                  },
                  {
                    key: "assign-system",
                    label: "Assign system",
                    onClick: () => setIsAssignSystemModalOpen(true),
                  },
                  ...(activeParams?.diff_status?.includes(DiffStatus.MUTED)
                    ? [
                        {
                          key: "restore",
                          label: "Restore",
                          onClick: handleBulkRestore,
                        },
                      ]
                    : [
                        {
                          type: "divider" as const,
                        },
                        {
                          key: "ignore",
                          label: "Ignore",
                          onClick: handleBulkIgnore,
                        },
                      ]),
                ],
              }}
              trigger={["click"]}
            >
              <Button
                icon={<Icons.ChevronDown />}
                iconPosition="end"
                loading={anyBulkActionIsLoading}
                data-testid="bulk-actions-menu"
                disabled={
                  !selectedUrns.length ||
                  anyBulkActionIsLoading ||
                  actionsDisabled
                }
                type="primary"
              >
                Actions
              </Button>
            </Dropdown>

            <Tooltip
              title={
                disableAddAll
                  ? `These assets require a system before you can add them to the inventory.`
                  : undefined
              }
            >
              <Button
                onClick={handleAddAll}
                disabled={disableAddAll}
                loading={isAddingAllResults}
                type="primary"
                icon={<Icons.Checkmark />}
                iconPosition="end"
                data-testid="add-all"
              >
                Add all
              </Button>
            </Tooltip>
          </Space>
        </Space>
      </Flex>
      <Table
        dataSource={data?.items || []}
        columns={columns}
        loading={isLoading || isFetching}
        rowKey={(record) => record.urn}
        rowSelection={
          activeTab === ActionCenterTabHash.RECENT_ACTIVITY
            ? undefined
            : rowSelection
        }
        pagination={{
          current: pageIndex,
          pageSize,
          total: data?.total || 0,
        }}
        onChange={handleTableChange}
        locale={{
          emptyText: (
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description="All caught up!"
            />
          ),
        }}
      />
      <AssignSystemModal
        isOpen={isAssignSystemModalOpen}
        onClose={() => {
          setIsAssignSystemModalOpen(false);
        }}
        onSave={handleBulkAssignSystem}
        isSaving={isBulkUpdatingSystem}
      />
      <AddDataUsesModal
        isOpen={isAddDataUseModalOpen}
        onClose={() => {
          setIsAddDataUseModalOpen(false);
        }}
        onSave={handleBulkAddDataUse}
        isSaving={isBulkAddingDataUses}
      />
      {consentBreakdownModalData && (
        <ConsentBreakdownModal
          isOpen={!!consentBreakdownModalData}
          stagedResource={consentBreakdownModalData.stagedResource}
          status={consentBreakdownModalData.status}
          onCancel={handleCloseBreakdown}
        />
      )}
    </>
  );
};

export default DiscoveredAssetsTable;
