import {
  getCoreRowModel,
  RowSelectionState,
  useReactTable,
} from "@tanstack/react-table";
import {
  AntButton as Button,
  AntDropdown as Dropdown,
  AntEmpty as Empty,
  AntTooltip as Tooltip,
  Box,
  Flex,
  Icons,
  Text,
  useToast,
} from "fidesui";
import { useRouter } from "next/router";
import { useEffect, useState } from "react";

import DataTabsHeader from "~/features/common/DataTabsHeader";
import { getErrorMessage } from "~/features/common/helpers";
import {
  ACTION_CENTER_ROUTE,
  SYSTEM_ROUTE,
  UNCATEGORIZED_SEGMENT,
} from "~/features/common/nav/routes";
import {
  FidesTableV2,
  PaginationBar,
  TableActionBar,
  TableSkeletonLoader,
  useServerSidePagination,
} from "~/features/common/table/v2";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import {
  useAddMonitorResultSystemsMutation,
  useGetDiscoveredSystemAggregateQuery,
  useIgnoreMonitorResultSystemsMutation,
} from "~/features/data-discovery-and-detection/action-center/action-center.slice";
import useActionCenterTabs, {
  getIndexFromHash,
} from "~/features/data-discovery-and-detection/action-center/tables/useActionCenterTabs";
import { successToastContent } from "~/features/data-discovery-and-detection/action-center/utils/successToastContent";
import { DiffStatus, SystemStagedResourcesAggregateRecord } from "~/types/api";
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
  const tabHash = router.asPath.split("#")[1];

  const {
    PAGE_SIZES,
    pageSize,
    setPageSize,
    onPreviousPageClick,
    isPreviousPageDisabled,
    onNextPageClick,
    isNextPageDisabled,
    startRange,
    endRange,
    pageIndex,
    setTotalPages,
    resetPageIndexToDefault,
  } = useServerSidePagination();

  const [addMonitorResultSystemsMutation, { isLoading: isAddingResults }] =
    useAddMonitorResultSystemsMutation();
  const [ignoreMonitorResultSystemsMutation, { isLoading: isIgnoringResults }] =
    useIgnoreMonitorResultSystemsMutation();

  const anyBulkActionIsLoading = isAddingResults || isIgnoringResults;

  const toast = useToast();

  const [searchQuery, setSearchQuery] = useState("");
  const [rowSelection, setRowSelection] = useState<RowSelectionState>({});

  useEffect(() => {
    resetPageIndexToDefault();
  }, [monitorId, searchQuery, resetPageIndexToDefault]);

  const {
    filterTabs,
    filterTabIndex,
    onTabChange,
    activeParams,
    actionsDisabled,
  } = useActionCenterTabs({ initialHash: tabHash });

  const { data, isLoading, isFetching } = useGetDiscoveredSystemAggregateQuery({
    key: monitorId,
    page: pageIndex,
    size: pageSize,
    search: searchQuery,
    ...activeParams,
  });

  useEffect(() => {
    if (data) {
      setTotalPages(data.pages || 1);
    }
  }, [data, setTotalPages]);

  const handleTabChange = (index: number) => {
    onTabChange(index);
    setRowSelection({});
  };

  const { columns } = useDiscoveredSystemAggregateColumns({
    monitorId,
    onTabChange: handleTabChange,
    readonly: actionsDisabled,
    allowIgnore: !activeParams.diff_status.includes(DiffStatus.MUTED),
  });

  const tableInstance = useReactTable({
    getCoreRowModel: getCoreRowModel(),
    columns,
    manualPagination: true,
    data: data?.items || [],
    columnResizeMode: "onChange",
    onRowSelectionChange: setRowSelection,
    state: {
      rowSelection,
    },
    getRowId: (row) =>
      row.id ?? row.vendor_id ?? row.name ?? UNCATEGORIZED_SEGMENT,
  });

  const selectedRows = tableInstance.getSelectedRowModel().rows;

  const uncategorizedIsSelected = selectedRows.some(
    (row) => row.original.id === null,
  );

  if (isLoading) {
    return <TableSkeletonLoader rowHeight={36} numRows={36} />;
  }

  const handleRowClick = (row: SystemStagedResourcesAggregateRecord) => {
    const newUrl = `${ACTION_CENTER_ROUTE}/${monitorId}/${row.id ?? UNCATEGORIZED_SEGMENT}${tabHash ? `#${tabHash}` : ""}`;
    router.push(newUrl);
  };

  const handleBulkAdd = async () => {
    const totalUpdates = selectedRows.reduce(
      (acc, row) => acc + row.original.total_updates!,
      0,
    );

    const result = await addMonitorResultSystemsMutation({
      monitor_config_key: monitorId,
      resolved_system_ids: selectedRows.map((row) => row.original.id!),
    });

    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
    } else {
      toast(
        successToastParams(
          successToastContent(
            `${totalUpdates} assets have been added to the system inventory.`,
            () => router.push(SYSTEM_ROUTE),
          ),
        ),
      );
      setRowSelection({});
    }
  };

  const handleBulkIgnore = async () => {
    const totalUpdates = selectedRows.reduce(
      (acc, row) => acc + row.original.total_updates!,
      0,
    );

    const result = await ignoreMonitorResultSystemsMutation({
      monitor_config_key: monitorId,
      resolved_system_ids: selectedRows.map(
        (row) => row.original.id ?? UNCATEGORIZED_SEGMENT,
      ),
    });

    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
    } else {
      toast(
        successToastParams(
          successToastContent(
            `${totalUpdates} assets have been ignored and will not appear in future scans.`,
            () => onTabChange(getIndexFromHash("#ignored")!),
          ),
        ),
      );
      setRowSelection({});
    }
  };

  return (
    <>
      <DataTabsHeader
        data={filterTabs}
        data-testid="filter-tabs"
        index={filterTabIndex}
        isLazy
        isManual
        onChange={handleTabChange}
      />
      <TableActionBar>
        <Flex
          direction="row"
          alignItems="center"
          justifyContent="space-between"
          width="full"
        >
          <Flex gap={6} align="center">
            <Box flexShrink={0}>
              <DebouncedSearchInput
                value={searchQuery}
                onChange={setSearchQuery}
              />
            </Box>
          </Flex>
          <Flex align="center">
            {!!selectedRows.length && (
              <Text
                fontSize="xs"
                fontWeight="semibold"
                minW={16}
                mr={6}
                data-testid="selected-count"
              >
                {`${selectedRows.length} selected`}
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
                disabled={!selectedRows.length}
                data-testid="bulk-actions-menu"
              >
                Actions
              </Button>
            </Dropdown>
          </Flex>
        </Flex>
      </TableActionBar>
      <FidesTableV2
        tableInstance={tableInstance}
        onRowClick={handleRowClick}
        emptyTableNotice={
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="All caught up!"
          />
        }
      />
      <PaginationBar
        totalRows={data?.total || 0}
        pageSizes={PAGE_SIZES}
        setPageSize={setPageSize}
        onPreviousPageClick={onPreviousPageClick}
        isPreviousPageDisabled={isPreviousPageDisabled || isFetching}
        onNextPageClick={onNextPageClick}
        isNextPageDisabled={isNextPageDisabled || isFetching}
        startRange={startRange}
        endRange={endRange}
      />
    </>
  );
};
