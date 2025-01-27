import {
  getCoreRowModel,
  RowSelectionState,
  useReactTable,
} from "@tanstack/react-table";
import {
  AntButton as Button,
  AntEmpty as Empty,
  Flex,
  HStack,
  Icons,
  Menu,
  MenuButton,
  MenuDivider,
  MenuItem,
  MenuList,
  Text,
} from "fidesui";
import { useRouter } from "next/router";
// import { useRouter } from "next/router";
import { useEffect, useState } from "react";

import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { useAlert } from "~/features/common/hooks";
import {
  ACTION_CENTER_ROUTE,
  UNCATEGORIZED_SEGMENT,
} from "~/features/common/nav/v2/routes";
// import { ACTION_CENTER_ROUTE } from "~/features/common/nav/v2/routes";
import {
  FidesTableV2,
  PaginationBar,
  TableActionBar,
  TableSkeletonLoader,
  useServerSidePagination,
} from "~/features/common/table/v2";
import {
  useAddMonitorResultAssetsMutation,
  useAddMonitorResultSystemMutation,
  useGetDiscoveredAssetsQuery,
  useIgnoreMonitorResultAssetsMutation,
} from "~/features/data-discovery-and-detection/action-center/action-center.slice";

import { SearchInput } from "../../SearchInput";
import { useDiscoveredAssetsColumns } from "../hooks/useDiscoveredAssetsColumns";

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
  const [systemName, setSystemName] = useState(systemId);
  const [rowSelection, setRowSelection] = useState<RowSelectionState>({});
  const [addMonitorResultAssetsMutation, { isLoading: isAddingResults }] =
    useAddMonitorResultAssetsMutation();
  const [ignoreMonitorResultAssetsMutation, { isLoading: isIgnoringResults }] =
    useIgnoreMonitorResultAssetsMutation();
  const [addMonitorResultSystemMutation, { isLoading: isAddingAllResults }] =
    useAddMonitorResultSystemMutation();

  const anyBulkActionIsLoading =
    isAddingResults || isIgnoringResults || isAddingAllResults;

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
  const [searchQuery, setSearchQuery] = useState("");
  // const [isAddingAll, setIsAddingAll] = useState(false);
  const { successAlert, errorAlert } = useAlert();

  useEffect(() => {
    resetPageIndexToDefault();
  }, [monitorId, searchQuery, resetPageIndexToDefault]);

  const { data, isLoading, isFetching } = useGetDiscoveredAssetsQuery({
    key: monitorId,
    system: systemId,
    page: pageIndex,
    size: pageSize,
    search: searchQuery,
  });

  useEffect(() => {
    if (data) {
      const firstSystemName = data.items[0]?.system || systemId || "";
      setTotalPages(data.pages || 1);
      setSystemName(firstSystemName);
      onSystemName?.(firstSystemName);
    }
  }, [data, systemId, onSystemName, setTotalPages]);

  const { columns } = useDiscoveredAssetsColumns();

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
  });

  const selectedRows = tableInstance.getSelectedRowModel().rows;
  const selectedUrns = selectedRows.map((row) => row.original.urn);

  const handleBulkAdd = async () => {
    const result = await addMonitorResultAssetsMutation({
      urnList: selectedUrns,
    });
    if (isErrorResult(result)) {
      errorAlert(getErrorMessage(result.error));
    } else {
      successAlert(
        `${selectedUrns.length} assets from ${systemName} have been added to the system inventory.`,
        `Confirmed`,
      );
    }
  };

  const handleBulkIgnore = async () => {
    const result = await ignoreMonitorResultAssetsMutation({
      urnList: selectedUrns,
    });
    if (isErrorResult(result)) {
      errorAlert(getErrorMessage(result.error));
    } else {
      successAlert(
        `${selectedUrns.length} assets from ${systemName} have been ignored and will not appear in future scans.`,
        `Confirmed`,
      );
    }
  };

  const handleAddAll = async () => {
    const assetCount = data?.items.length || 0;
    const result = await addMonitorResultSystemMutation({
      monitor_config_key: monitorId,
      resolved_system_id: systemId,
    });

    if (isErrorResult(result)) {
      errorAlert(getErrorMessage(result.error));
    } else {
      router.push(`${ACTION_CENTER_ROUTE}/${monitorId}`);
      successAlert(
        `${assetCount} assets from ${systemName} have been added to the system inventory.`,
        `Confirmed`,
      );
    }
  };

  if (!monitorId || !systemId) {
    return null;
  }

  if (isLoading) {
    return <TableSkeletonLoader rowHeight={36} numRows={36} />;
  }

  return (
    <>
      <TableActionBar>
        <SearchInput value={searchQuery} onChange={setSearchQuery} />
        <Flex alignItems="center">
          {!!selectedUrns.length && (
            <Text
              fontSize="xs"
              fontWeight="semibold"
              minW={16}
              mr={6}
              data-testid="selected-count"
            >{`${selectedUrns.length} selected`}</Text>
          )}
          <HStack>
            <Menu>
              <MenuButton
                as={Button}
                icon={<Icons.ChevronDown />}
                iconPosition="end"
                loading={anyBulkActionIsLoading}
                data-testid="bulk-actions-menu"
                disabled={!selectedUrns.length || anyBulkActionIsLoading}
                // @ts-ignore - `type` prop is for Ant button, not Chakra MenuButton
                type="primary"
              >
                Actions
              </MenuButton>
              <MenuList>
                <MenuItem
                  fontSize="small"
                  onClick={handleBulkAdd}
                  data-testid="bulk-add"
                >
                  Add
                </MenuItem>
                <MenuDivider />
                <MenuItem
                  fontSize="small"
                  onClick={handleBulkIgnore}
                  data-testid="bulk-ignore"
                >
                  Ignore
                </MenuItem>
              </MenuList>
            </Menu>
            <Button
              onClick={handleAddAll}
              disabled={
                anyBulkActionIsLoading || systemId === UNCATEGORIZED_SEGMENT
              }
              loading={isAddingAllResults}
              type="primary"
              icon={<Icons.Checkmark />}
              iconPosition="end"
              data-testid="add-all"
            >
              Add all
            </Button>
          </HStack>
        </Flex>
      </TableActionBar>
      <FidesTableV2
        tableInstance={tableInstance}
        emptyTableNotice={
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="All caught up!"
          />
        }
      />
      <PaginationBar
        totalRows={data?.items.length || 0}
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
