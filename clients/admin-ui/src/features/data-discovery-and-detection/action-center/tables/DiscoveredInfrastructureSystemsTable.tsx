import {
  Button,
  Checkbox,
  Dropdown,
  Empty,
  Flex,
  Icons,
  List,
  Pagination,
  Text,
  Tooltip,
} from "fidesui";
import { useCallback, useMemo } from "react";

import { DebouncedSearchInput } from "~/features/common/DebouncedSearchInput";

import { InfrastructureSystemListItem } from "../components/InfrastructureSystemListItem";
import { InfrastructureSystemBulkActionType } from "../constants";
import { InfrastructureSystemsFilters } from "../fields/InfrastructureSystemsFilters";
import { useInfrastructureSystemsFilters } from "../fields/useInfrastructureSystemsFilters";
import { ActionCenterTabHash } from "../hooks/useActionCenterTabs";
import { useDiscoveredInfrastructureSystemsTable } from "../hooks/useDiscoveredInfrastructureSystemsTable";
import { useInfrastructureSystemsBulkActions } from "../hooks/useInfrastructureSystemsBulkActions";
import { useInfrastructureSystemsSelection } from "../hooks/useInfrastructureSystemsSelection";
import {
  getBulkActionsMenuItems,
  shouldAllowIgnore,
} from "../utils/infrastructureSystemsBulkActionsMenu";

interface DiscoveredInfrastructureSystemsTableProps {
  monitorId: string;
}

export const DiscoveredInfrastructureSystemsTable = ({
  monitorId,
}: DiscoveredInfrastructureSystemsTableProps) => {
  const infrastructureSystemsFilters = useInfrastructureSystemsFilters();

  const {
    data,
    isLoading,
    searchQuery,
    updateSearch,
    paginationProps,
    activeTab,
    activeParams,
    rowClickUrl,
    getRecordKey,
    refetch,
  } = useDiscoveredInfrastructureSystemsTable({
    monitorId,
    statusFilters: infrastructureSystemsFilters.statusFilters,
    vendorFilters: infrastructureSystemsFilters.vendorFilters,
    dataUsesFilters: infrastructureSystemsFilters.dataUsesFilters,
  });

  // Build filters object for selection hook
  const filters = useMemo(
    () => ({
      search: searchQuery || undefined,
      diff_status: infrastructureSystemsFilters.statusFilters?.length
        ? (infrastructureSystemsFilters.statusFilters as any)
        : undefined,
      vendor_id: infrastructureSystemsFilters.vendorFilters?.length
        ? infrastructureSystemsFilters.vendorFilters
        : undefined,
      data_uses: infrastructureSystemsFilters.dataUsesFilters?.length
        ? infrastructureSystemsFilters.dataUsesFilters
        : undefined,
    }),
    [
      searchQuery,
      infrastructureSystemsFilters.statusFilters,
      infrastructureSystemsFilters.vendorFilters,
      infrastructureSystemsFilters.dataUsesFilters,
    ],
  );

  const {
    selectedItems,
    excludedUrns,
    selectionMode,
    hasSelectedRows,
    selectedRowsCount,
    isAllSelected,
    isIndeterminate,
    handleSelectAll,
    handleSelectItem,
    clearSelection,
    isItemSelected,
  } = useInfrastructureSystemsSelection({
    items: data?.items,
    getRecordKey,
    totalCount: data?.total,
    filters,
  });

  const { handleBulkAction, isBulkActionInProgress } =
    useInfrastructureSystemsBulkActions({
      monitorId,
      onSuccess: () => {
        clearSelection();
        refetch();
      },
    });

  const isIgnoredTab = activeTab === ActionCenterTabHash.IGNORED;
  const allowIgnore = shouldAllowIgnore(activeParams);

  const handleBulkActionWithSelectedItems = useCallback(
    (action: InfrastructureSystemBulkActionType) => {
      if (selectionMode === "all") {
        // excludedUrns already contains all URNs that should be excluded
        handleBulkAction(action, {
          mode: "all",
          filters,
          excludeUrns: excludedUrns,
        });
      } else {
        handleBulkAction(action, {
          mode: "explicit",
          selectedItems,
        });
      }
    },
    [handleBulkAction, selectedItems, selectionMode, excludedUrns, filters],
  );

  const bulkActionsMenuItems = useMemo(
    () =>
      getBulkActionsMenuItems({
        isIgnoredTab,
        allowIgnore,
        isBulkActionInProgress,
        onBulkAction: handleBulkActionWithSelectedItems,
      }),
    [
      isIgnoredTab,
      allowIgnore,
      isBulkActionInProgress,
      handleBulkActionWithSelectedItems,
    ],
  );

  return (
    <Flex vertical gap="middle" className="h-full overflow-hidden">
      <Flex justify="space-between">
        <Flex gap="small">
          <DebouncedSearchInput
            value={searchQuery}
            onChange={updateSearch}
            placeholder="Search"
          />
        </Flex>
        <Flex gap="small">
          <InfrastructureSystemsFilters
            monitorId={monitorId}
            {...infrastructureSystemsFilters}
          />
          <Dropdown
            menu={{ items: bulkActionsMenuItems }}
            disabled={!hasSelectedRows || isBulkActionInProgress}
          >
            <Button
              type="primary"
              icon={<Icons.ChevronDown />}
              iconPosition="end"
              disabled={!hasSelectedRows || isBulkActionInProgress}
              loading={isBulkActionInProgress}
            >
              Actions
            </Button>
          </Dropdown>
          <Tooltip title="Refresh">
            <Button
              icon={<Icons.Renew />}
              aria-label="Refresh"
              onClick={refetch}
              loading={isLoading}
            />
          </Tooltip>
        </Flex>
      </Flex>
      <Flex gap="middle" align="center">
        <Checkbox
          checked={isAllSelected}
          indeterminate={isIndeterminate}
          onChange={(e) => handleSelectAll(e.target.checked)}
          title="Select all"
        >
          Select all
        </Checkbox>
        {selectedRowsCount > 0 && (
          <Text strong>
            {selectedRowsCount.toLocaleString()}
            {selectionMode === "all" &&
            data?.total &&
            selectedRowsCount < data.total
              ? ` of ${data.total.toLocaleString()}`
              : ""}{" "}
            selected
          </Text>
        )}
      </Flex>
      <Flex flex={1} style={{ minHeight: 0, overflow: "hidden" }}>
        <List
          dataSource={data?.items}
          loading={isLoading}
          className="size-full overflow-y-auto overflow-x-clip"
          locale={{
            emptyText: (
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description="All caught up!"
              />
            ),
          }}
          renderItem={(item) => (
            <InfrastructureSystemListItem
              item={item}
              selected={isItemSelected(item)}
              onSelect={(key, selected) => {
                // Use getRecordKey to ensure consistent key matching
                const recordKey = getRecordKey(item);
                handleSelectItem(recordKey, selected);
              }}
              rowClickUrl={rowClickUrl}
              monitorId={monitorId}
              activeTab={activeTab as ActionCenterTabHash | null}
              allowIgnore={allowIgnore}
              onPromoteSuccess={refetch}
            />
          )}
        />
      </Flex>
      <Pagination
        {...paginationProps}
        total={data?.total || 0}
        showSizeChanger={{
          suffixIcon: <Icons.ChevronDown />,
        }}
        hideOnSinglePage={
          paginationProps.pageSize?.toString() ===
          paginationProps.pageSizeOptions?.[0]
        }
      />
    </Flex>
  );
};
