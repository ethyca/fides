import {
  Button,
  Checkbox,
  Dropdown,
  Empty,
  Flex,
  Icons,
  List,
  Menu,
  Pagination,
  Text,
  Title,
  Tooltip,
} from "fidesui";
import { useCallback, useMemo } from "react";

import { DebouncedSearchInput } from "~/features/common/DebouncedSearchInput";

import { useGetMonitorConfigQuery } from "../action-center.slice";
import { InfrastructureSystemListItem } from "../components/InfrastructureSystemListItem";
import {
  INFRASTRUCTURE_SYSTEMS_TABS,
  InfrastructureSystemBulkActionType,
} from "../constants";
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
    handleTabChange,
    activeParams,
    rowClickUrl,
    getRecordKey,
    refetch,
  } = useDiscoveredInfrastructureSystemsTable({
    monitorId,
    statusFilters: infrastructureSystemsFilters.statusFilters,
    vendorFilters: infrastructureSystemsFilters.vendorFilters,
  });

  const { data: monitorConfigData } = useGetMonitorConfigQuery({
    monitor_config_id: monitorId,
  });

  const {
    selectedItems,
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
  });

  const { handleBulkAction, isBulkActionInProgress } =
    useInfrastructureSystemsBulkActions({
      monitorId,
      getRecordKey,
      onSuccess: () => {
        clearSelection();
        refetch();
      },
    });

  const isIgnoredTab = activeTab === ActionCenterTabHash.IGNORED;
  const allowIgnore = shouldAllowIgnore(activeParams);

  const handleBulkActionWithSelectedItems = useCallback(
    (action: InfrastructureSystemBulkActionType) => {
      handleBulkAction(action, selectedItems);
    },
    [handleBulkAction, selectedItems],
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
    <>
      <Menu
        aria-label="Asset state filter"
        mode="horizontal"
        items={INFRASTRUCTURE_SYSTEMS_TABS.map((tab) => ({
          key: tab.key,
          label: tab.label,
        }))}
        selectedKeys={[activeTab]}
        onClick={async (menuInfo) => {
          await handleTabChange(menuInfo.key as ActionCenterTabHash);
          clearSelection(); // Clear selections on tab change
        }}
        className="mb-4"
        data-testid="asset-state-filter"
      />
      <Flex vertical gap="middle" className="h-full">
        <Flex justify="space-between">
          <Title level={2}>Monitor results</Title>
          <Flex align="center">
            {monitorConfigData?.last_monitored && (
              <Text type="secondary">
                Last scan:{" "}
                {new Date(monitorConfigData.last_monitored).toLocaleString()}
              </Text>
            )}
          </Flex>
        </Flex>
        <Flex justify="space-between">
          <Flex gap="small">
            <DebouncedSearchInput
              value={searchQuery}
              onChange={updateSearch}
              placeholder="Search"
            />
          </Flex>
          <Flex gap="small">
            <InfrastructureSystemsFilters {...infrastructureSystemsFilters} />
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
          />
          <span className="ml-2">Select all</span>
          {selectedRowsCount > 0 && (
            <Text strong>{selectedRowsCount.toLocaleString()} selected</Text>
          )}
        </Flex>
        <List
          dataSource={data?.items}
          loading={isLoading}
          className="h-full overflow-y-scroll"
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
              onPromoteSuccess={refetch}
            />
          )}
        />
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
    </>
  );
};
