import {
  AntButton as Button,
  AntCheckbox as Checkbox,
  AntDropdown as Dropdown,
  AntEmpty as Empty,
  AntFlex as Flex,
  AntList as List,
  AntMenu as Menu,
  AntPagination as Pagination,
  AntText as Text,
  AntTitle as Title,
  AntTooltip as Tooltip,
  Icons,
} from "fidesui";
import { useCallback, useMemo, useState } from "react";

import { DebouncedSearchInput } from "~/features/common/DebouncedSearchInput";
import { DiffStatus } from "~/types/api";

import { useGetMonitorConfigQuery } from "../action-center.slice";
import { InfrastructureSystemListItem } from "../components/InfrastructureSystemListItem";
import { ActionCenterTabHash } from "../hooks/useActionCenterTabs";
import { useDiscoveredInfrastructureSystemsTable } from "../hooks/useDiscoveredInfrastructureSystemsTable";

interface DiscoveredInfrastructureSystemsTableProps {
  monitorId: string;
}

export const DiscoveredInfrastructureSystemsTable = ({
  monitorId,
}: DiscoveredInfrastructureSystemsTableProps) => {
  const [selectedKeys, setSelectedKeys] = useState<Set<string>>(new Set());

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
  } = useDiscoveredInfrastructureSystemsTable({ monitorId });

  const { data: monitorConfigData } = useGetMonitorConfigQuery({
    monitor_config_id: monitorId,
  });

  const hasSelectedRows = selectedKeys.size > 0;
  const selectedRowsCount = selectedKeys.size;

  // Create tabs with labels based on ActionCenterTabHash
  const tabsWithIcons = useMemo(
    () => [
      {
        key: ActionCenterTabHash.ATTENTION_REQUIRED,
        label: "Attention required",
      },
      {
        key: ActionCenterTabHash.ADDED,
        label: "Activity",
      },
      {
        key: ActionCenterTabHash.IGNORED,
        label: "Ignored",
      },
    ],
    [],
  );

  const handleSelectAll = useCallback(
    (checked: boolean) => {
      if (checked) {
        const allKeys = new Set(
          data?.items.map((item) => getRecordKey(item)) ?? [],
        );
        setSelectedKeys(allKeys);
      } else {
        setSelectedKeys(new Set());
      }
    },
    [data?.items, getRecordKey],
  );

  const handleSelectItem = useCallback((key: string, selected: boolean) => {
    setSelectedKeys((prev) => {
      const next = new Set(prev);
      if (selected) {
        next.add(key);
      } else {
        next.delete(key);
      }
      return next;
    });
  }, []);

  const isAllSelected = useMemo(() => {
    if (!data?.items || data.items.length === 0) {
      return false;
    }
    return (
      selectedKeys.size > 0 &&
      selectedKeys.size === data.items.length &&
      data.items.every((item) => selectedKeys.has(getRecordKey(item)))
    );
  }, [data?.items, selectedKeys, getRecordKey]);

  const isIndeterminate = useMemo(() => {
    if (!data?.items || data.items.length === 0) {
      return false;
    }
    return selectedKeys.size > 0 && selectedKeys.size < data.items.length;
  }, [data?.items, selectedKeys]);

  const allowIgnore =
    activeParams.diff_status &&
    !activeParams.diff_status.includes(DiffStatus.MUTED);

  const selectedItems = useMemo(() => {
    if (!data?.items) {
      return [];
    }
    return data.items.filter((item) => selectedKeys.has(getRecordKey(item)));
  }, [data?.items, selectedKeys, getRecordKey]);

  // TODO: Implement bulk actions
  const handleBulkAction = useCallback(
    (action: "add" | "ignore") => {
      console.log(`Bulk ${action} for`, selectedItems);
      // Implement bulk actions here
    },
    [selectedItems],
  );

  return (
    <>
      <Menu
        aria-label="Asset state filter"
        mode="horizontal"
        items={tabsWithIcons.map((tab) => ({
          key: tab.key,
          label: tab.label,
        }))}
        selectedKeys={[activeTab]}
        onClick={async (menuInfo) => {
          await handleTabChange(menuInfo.key as ActionCenterTabHash);
          setSelectedKeys(new Set()); // Clear selections on tab change
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
            <Tooltip title="Filter">
              <Button icon={<Icons.ChevronDown />} iconPosition="end">
                Filter
              </Button>
            </Tooltip>
            <Dropdown
              menu={{
                items: [
                  ...(allowIgnore
                    ? [
                      {
                        key: "ignore",
                        label: "Ignore",
                        onClick: () => handleBulkAction("ignore"),
                      },
                    ]
                    : []),
                  {
                    key: "add",
                    label: "Add",
                    onClick: () => handleBulkAction("add"),
                  },
                ],
              }}
              disabled={!hasSelectedRows}
            >
              <Button
                type="primary"
                icon={<Icons.ChevronDown />}
                iconPosition="end"
                disabled={!hasSelectedRows}
              >
                Actions
              </Button>
            </Dropdown>
            <Tooltip title="Refresh">
              <Button icon={<Icons.Renew />} aria-label="Refresh" />
            </Tooltip>
          </Flex>
        </Flex>
        <Flex gap="middle" align="center">
          <Checkbox
            checked={isAllSelected}
            indeterminate={isIndeterminate}
            onChange={(e) => handleSelectAll(e.target.checked)}
          />
          <label htmlFor="select-all">Select all</label>
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
              selected={selectedKeys.has(getRecordKey(item))}
              onSelect={handleSelectItem}
              rowClickUrl={rowClickUrl}
              monitorId={monitorId}
              onTabChange={handleTabChange}
              allowIgnore={allowIgnore}
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
