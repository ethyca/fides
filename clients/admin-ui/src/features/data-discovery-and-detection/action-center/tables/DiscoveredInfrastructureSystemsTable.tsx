import {
  Alert,
  Button,
  Checkbox,
  Dropdown,
  Empty,
  Flex,
  Icons,
  List,
  Pagination,
  Text,
} from "fidesui";
import { useCallback, useMemo } from "react";

import { DebouncedSearchInput } from "~/features/common/DebouncedSearchInput";
import { DiffStatus } from "~/types/api";

import { InfrastructureSystemListItem } from "../components/InfrastructureSystemListItem";
import { InfrastructureSystemsFilters } from "../components/InfrastructureSystemsFilters";
import { InfrastructureSystemBulkActionType } from "../constants";
import { useInfrastructureSystemsFilters } from "../fields/useInfrastructureSystemsFilters";
import { ActionCenterTabHash } from "../hooks/useActionCenterTabs";
import { useDiscoveredInfrastructureSystemsTable } from "../hooks/useDiscoveredInfrastructureSystemsTable";
import { useInfrastructureSystemsBulkActions } from "../hooks/useInfrastructureSystemsBulkActions";
import { useInfrastructureSystemsSelection } from "../hooks/useInfrastructureSystemsSelection";
import {
  getBulkActionsMenuItems,
  shouldAllowIgnore,
  shouldAllowRestore,
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
    diffStatusFilters,
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

  const allowIgnore = shouldAllowIgnore(diffStatusFilters);
  const allowRestore = shouldAllowRestore(diffStatusFilters);

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
        isIgnoredTab: diffStatusFilters?.includes(DiffStatus.MUTED),
        allowIgnore,
        isBulkActionInProgress,
        onBulkAction: handleBulkActionWithSelectedItems,
      }),
    [
      diffStatusFilters,
      allowIgnore,
      isBulkActionInProgress,
      handleBulkActionWithSelectedItems,
    ],
  );

  return (
    <Flex vertical gap="medium" className="h-full overflow-hidden">
      <Alert
        showIcon
        title="Fides detected the following systems"
        description="Some may not yet be in your inventory. Review each system's detected data use — approve to add it to your inventory, or ignore if it's not relevant."
        closable
      />
      <Flex justify="space-between" gap="medium">
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
              iconPlacement="end"
              disabled={!hasSelectedRows || isBulkActionInProgress}
              loading={isBulkActionInProgress}
            >
              Actions
            </Button>
          </Dropdown>
        </Flex>
      </Flex>
      <Flex gap="medium" align="center">
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
              onSelect={handleSelectItem}
              rowClickUrl={rowClickUrl}
              monitorId={monitorId}
              activeTab={activeTab as ActionCenterTabHash | null}
              allowIgnore={allowIgnore}
              allowRestore={allowRestore}
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
