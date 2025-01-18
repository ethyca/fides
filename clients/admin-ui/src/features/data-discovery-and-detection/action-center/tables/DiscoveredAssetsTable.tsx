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
// import { useRouter } from "next/router";
import { useEffect, useState } from "react";

import { useAlert } from "~/features/common/hooks";
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
  useGetDiscoveredAssetsQuery,
  useIgnoreMonitorResultAssetsMutation,
} from "~/features/data-discovery-and-detection/action-center/action-center.slice";

import { SearchInput } from "../../SearchInput";
import { useDiscoveredAssetsColumns } from "../hooks/useDiscoveredAssetsColumns";

interface DiscoveredAssetsTableProps {
  monitorId: string;
  systemId: string;
}

export const DiscoveredAssetsTable = ({
  monitorId,
  systemId,
}: DiscoveredAssetsTableProps) => {
  // const router = useRouter();
  const [rowSelection, setRowSelection] = useState<RowSelectionState>({});
  const [addMonitorResultAssetsMutation, { isLoading: isAddingResults }] =
    useAddMonitorResultAssetsMutation();
  const [ignoreMonitorResultAssetsMutation, { isLoading: isIgnoringResults }] =
    useIgnoreMonitorResultAssetsMutation();

  const anyBulkActionIsLoading = isAddingResults || isIgnoringResults;

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
  const { successAlert } = useAlert();

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
      setTotalPages(data.pages || 1);
    }
  }, [data, setTotalPages]);

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

  const selectedUrns = Object.keys(rowSelection).filter((k) => rowSelection[k]);

  const handleBulkAdd = async () => {
    await addMonitorResultAssetsMutation({
      urnList: selectedUrns,
    });
    // TODO: Add "view" button which will bring users to the system inventory with an asset tab open (not yet developed)
    successAlert(
      `${selectedUrns.length} assets from ${systemId} have been added to the system inventory.`,
      `Confirmed`,
    );
  };

  const handleBulkIgnore = async () => {
    await ignoreMonitorResultAssetsMutation({
      urnList: selectedUrns,
    });
    successAlert(
      `${selectedUrns.length} assets from ${systemId} have been ignored and will not be added to the system inventory.`,
      `Confirmed`,
    );
  };

  // TODO: [HJ-343] Uncommend when system actions are implemented
  /* const handleAddAll = async () => {
    setIsAddingAll(true);
    await addMonitorResultSystemMutation({
      monitor_config_key: monitorId,
      resolved_system_id: systemId,
    });
    setIsAddingAll(false);
    router.push(`${ACTION_CENTER_ROUTE}/${monitorId}`);
    // TODO: Add "view" button which will bring users to the system inventory with an asset tab open (not yet developed)
    successAlert(
      `All assets from ${systemId} have been added to the system inventory.`,
      `Confirmed`,
    );
  }; */

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
            {/*
            // TODO: [HJ-343] Uncommend when system actions are implemented
            <Button
              onClick={handleAddAll}
              disabled={anyBulkActionIsLoading}
              loading={isAddingAll}
              type="primary"
              icon={<Icons.Checkmark />}
              iconPosition="end"
              data-testid="add-all"
            >
              Add all
            </Button> */}
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
