import {
  AntButton as Button,
  AntDropdown as Dropdown,
  AntEmpty as Empty,
  AntFlex as Flex,
  AntSpace as Space,
  AntTable as Table,
  AntTabs as Tabs,
  AntTooltip as Tooltip,
  Icons,
  useToast,
} from "fidesui";
import { useRouter } from "next/router";
import { useCallback, useEffect, useState } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import {
  ACTION_CENTER_ROUTE,
  SYSTEM_ROUTE,
  UNCATEGORIZED_SEGMENT,
} from "~/features/common/nav/routes";
import { SelectedText } from "~/features/common/table/SelectedText";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import {
  useAddMonitorResultSystemsMutation,
  useGetDiscoveredSystemAggregateQuery,
  useIgnoreMonitorResultSystemsMutation,
} from "~/features/data-discovery-and-detection/action-center/action-center.slice";
import useActionCenterTabs, {
  ActionCenterTabHash,
} from "~/features/data-discovery-and-detection/action-center/hooks/useActionCenterTabs";
import { SuccessToastContent } from "~/features/data-discovery-and-detection/action-center/SuccessToastContent";
import {
  AlertLevel,
  ConsentAlertInfo,
  DiffStatus,
  SystemStagedResourcesAggregateRecord,
} from "~/types/api";
import { isErrorResult } from "~/types/errors";

import { DebouncedSearchInput } from "../../../common/DebouncedSearchInput";
import { useDiscoveredSystemAggregateColumns } from "../hooks/useDiscoveredSystemAggregateColumns";

interface DiscoveredSystemAggregateTableProps {
  monitorId: string;
}

export const DiscoveredSystemAggregateTable = ({
  monitorId,
}: DiscoveredSystemAggregateTableProps) => {
  const router = useRouter();

  const [firstPageConsentStatus, setFirstPageConsentStatus] = useState<
    ConsentAlertInfo | undefined
  >();

  // Pagination state
  const [pageIndex, setPageIndex] = useState(1);
  const [pageSize, setPageSize] = useState(25);

  const [addMonitorResultSystemsMutation, { isLoading: isAddingResults }] =
    useAddMonitorResultSystemsMutation();
  const [ignoreMonitorResultSystemsMutation, { isLoading: isIgnoringResults }] =
    useIgnoreMonitorResultSystemsMutation();

  const anyBulkActionIsLoading = isAddingResults || isIgnoringResults;

  const toast = useToast();

  const [searchQuery, setSearchQuery] = useState("");

  // Selection state
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const [selectedRowsMap, setSelectedRowsMap] = useState<
    Map<string, SystemStagedResourcesAggregateRecord>
  >(new Map());

  const resetSelections = () => {
    setSelectedRowKeys([]);
    setSelectedRowsMap(new Map());
  };

  // Helper function to generate consistent row keys
  const getRecordKey = (record: SystemStagedResourcesAggregateRecord) =>
    record.id ?? record.vendor_id ?? record.name ?? UNCATEGORIZED_SEGMENT;

  const { filterTabs, activeTab, onTabChange, activeParams, actionsDisabled } =
    useActionCenterTabs();

  // Reset pagination when filters change
  useEffect(() => {
    setPageIndex(1);
  }, [monitorId, searchQuery]);

  // Reset selections when filters change
  useEffect(() => {
    resetSelections();
  }, [monitorId, searchQuery, activeTab]);

  const { data, isLoading, isFetching } = useGetDiscoveredSystemAggregateQuery({
    key: monitorId,
    page: pageIndex,
    size: pageSize,
    search: searchQuery,
    ...activeParams,
  });

  useEffect(() => {
    if (data?.items && !firstPageConsentStatus) {
      // this ensures that the column header remembers the consent status
      // even when the user navigates to a different paginated page
      const consentStatus = data.items.find(
        (item) => item.consent_status?.status === AlertLevel.ALERT,
      )?.consent_status;
      setFirstPageConsentStatus(consentStatus ?? undefined);
    }
  }, [data, firstPageConsentStatus]);

  // Update selectedRowKeys to only show current page selections when data changes
  useEffect(() => {
    if (data?.items) {
      const currentPageSelectedKeys = data.items
        .filter((item) => {
          const key = getRecordKey(item);
          return selectedRowsMap.has(String(key));
        })
        .map((item) => getRecordKey(item));
      setSelectedRowKeys(currentPageSelectedKeys);
    }
  }, [data, selectedRowsMap]);

  // Get selected rows from the map
  const selectedRows = Array.from(selectedRowsMap.values());

  const handleTabChange = (tab: ActionCenterTabHash) => {
    setFirstPageConsentStatus(undefined);
    onTabChange(tab);
    resetSelections();
  };

  const rowClickUrl = useCallback(
    (record: SystemStagedResourcesAggregateRecord) => {
      const newUrl = `${ACTION_CENTER_ROUTE}/${monitorId}/${record.id ?? UNCATEGORIZED_SEGMENT}${activeTab ? `#${activeTab}` : ""}`;
      return newUrl;
    },
    [monitorId, activeTab],
  );

  const { columns } = useDiscoveredSystemAggregateColumns({
    monitorId,
    onTabChange: handleTabChange,
    readonly: actionsDisabled,
    allowIgnore: !activeParams.diff_status.includes(DiffStatus.MUTED),
    consentStatus: firstPageConsentStatus,
    rowClickUrl,
  });

  const handleBulkAdd = async () => {
    const totalUpdates = selectedRows.reduce(
      (acc, row) => acc + row.total_updates!,
      0,
    );

    const result = await addMonitorResultSystemsMutation({
      monitor_config_key: monitorId,
      resolved_system_ids: selectedRows.map((row) => row.id!),
    });

    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
    } else {
      toast(
        successToastParams(
          SuccessToastContent(
            `${totalUpdates} assets have been added to the system inventory.`,
            () => router.push(SYSTEM_ROUTE),
          ),
        ),
      );
      resetSelections();
    }
  };

  const handleBulkIgnore = async () => {
    const totalUpdates = selectedRows.reduce(
      (acc, row) => acc + row.total_updates!,
      0,
    );

    const result = await ignoreMonitorResultSystemsMutation({
      monitor_config_key: monitorId,
      resolved_system_ids: selectedRows.map(
        (row) => row.id ?? UNCATEGORIZED_SEGMENT,
      ),
    });

    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
    } else {
      toast(
        successToastParams(
          SuccessToastContent(
            `${totalUpdates} assets have been ignored and will not appear in future scans.`,
            () => onTabChange(ActionCenterTabHash.IGNORED),
          ),
        ),
      );
      resetSelections();
    }
  };

  const uncategorizedIsSelected = selectedRows.some((row) => row.id === null);

  const rowSelection = {
    selectedRowKeys,
    onChange: (
      newSelectedRowKeys: React.Key[],
      newSelectedRows: SystemStagedResourcesAggregateRecord[],
    ) => {
      setSelectedRowKeys(newSelectedRowKeys);

      // Update the map with current page selections
      const newMap = new Map(selectedRowsMap);

      // Remove deselected items from current page
      if (data?.items) {
        data.items.forEach((item) => {
          const key = getRecordKey(item);
          if (!newSelectedRowKeys.includes(key)) {
            newMap.delete(String(key));
          }
        });
      }

      // Add newly selected items
      newSelectedRows.forEach((row) => {
        const key = getRecordKey(row);
        newMap.set(String(key), row);
      });

      setSelectedRowsMap(newMap);
    },
  };

  const handleTableChange = (pagination: any) => {
    setPageIndex(pagination.current);
    setPageSize(pagination.pageSize);
  };

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
        <DebouncedSearchInput value={searchQuery} onChange={setSearchQuery} />
        <Space size="large">
          {!!selectedRowKeys.length && (
            <SelectedText count={selectedRows.length} />
          )}
          <Dropdown
            menu={{
              items: [
                {
                  key: "add",
                  label: (
                    <Tooltip
                      title={
                        uncategorizedIsSelected
                          ? "Uncategorized assets can't be added to the inventory"
                          : null
                      }
                      placement="left"
                    >
                      Add
                    </Tooltip>
                  ),
                  onClick: handleBulkAdd,
                  disabled: uncategorizedIsSelected,
                },
                !activeParams.diff_status.includes(DiffStatus.MUTED)
                  ? {
                      key: "ignore",
                      label: "Ignore",
                      onClick: handleBulkIgnore,
                    }
                  : null,
              ],
            }}
            trigger={["click"]}
          >
            <Button
              type="primary"
              icon={<Icons.ChevronDown />}
              iconPosition="end"
              loading={anyBulkActionIsLoading}
              disabled={!selectedRowKeys.length}
              data-testid="bulk-actions-menu"
            >
              Actions
            </Button>
          </Dropdown>
        </Space>
      </Flex>
      <Table
        dataSource={data?.items || []}
        columns={columns}
        loading={isLoading || isFetching}
        rowKey={(record) =>
          record.id ?? record.vendor_id ?? record.name ?? UNCATEGORIZED_SEGMENT
        }
        rowSelection={rowSelection}
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
    </>
  );
};
