import {
  AntButton as Button,
  AntDropdown as Dropdown,
  AntEmpty as Empty,
  AntTable as Table,
  AntTabs as Tabs,
  AntTooltip as Tooltip,
  Flex,
  Icons,
  Text,
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
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const [selectedRows, setSelectedRows] = useState<
    SystemStagedResourcesAggregateRecord[]
  >([]);

  const { filterTabs, activeTab, onTabChange, activeParams, actionsDisabled } =
    useActionCenterTabs();

  // Reset pagination when filters change
  useEffect(() => {
    setPageIndex(1);
  }, [monitorId, searchQuery]);

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

  const handleTabChange = (tab: ActionCenterTabHash) => {
    setFirstPageConsentStatus(undefined);
    onTabChange(tab);
    setSelectedRowKeys([]);
    setSelectedRows([]);
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

  const handleRowClick = (record: SystemStagedResourcesAggregateRecord) => {
    router.push(rowClickUrl(record));
  };

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
      setSelectedRowKeys([]);
      setSelectedRows([]);
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
      setSelectedRowKeys([]);
      setSelectedRows([]);
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
      setSelectedRows(newSelectedRows);
    },
  };

  const handleTableChange = (pagination: any) => {
    setPageIndex(pagination.current);
    setPageSize(pagination.pageSize);
  };

  return (
    <Tabs
      items={filterTabs.map((tab) => ({
        key: tab.hash,
        label: tab.label,
        children: (
          <>
            <Flex justify="space-between" align="center" className="mb-4">
              <DebouncedSearchInput
                value={searchQuery}
                onChange={setSearchQuery}
              />
              <Flex align="center">
                {!!selectedRowKeys.length && (
                  <Text
                    fontSize="xs"
                    fontWeight="semibold"
                    minW={16}
                    mr={6}
                    data-testid="selected-count"
                  >
                    {`${selectedRowKeys.length} selected`}
                  </Text>
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
              </Flex>
            </Flex>
            <Table
              dataSource={data?.items || []}
              columns={columns}
              loading={isLoading || isFetching}
              rowKey={(record) =>
                record.id ??
                record.vendor_id ??
                record.name ??
                UNCATEGORIZED_SEGMENT
              }
              rowSelection={rowSelection}
              pagination={{
                current: pageIndex,
                pageSize,
                total: data?.total || 0,
              }}
              onChange={handleTableChange}
              onRow={(record) => ({
                onClick: (e) => {
                  e.stopPropagation();
                  handleRowClick(record);
                },
                style: { cursor: "pointer" },
              })}
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
        ),
      }))}
      activeKey={activeTab}
      onChange={(tab) => handleTabChange(tab as ActionCenterTabHash)}
    />
  );
};
