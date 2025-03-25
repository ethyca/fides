import {
  getCoreRowModel,
  RowSelectionState,
  useReactTable,
} from "@tanstack/react-table";
import {
  AntButton as Button,
  AntDefaultOptionType as DefaultOptionType,
  AntEmpty as Empty,
  AntTooltip as Tooltip,
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
import { uniq } from "lodash";
import { useRouter } from "next/router";
import { useEffect, useState } from "react";

import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { useAlert } from "~/features/common/hooks";
import {
  ACTION_CENTER_ROUTE,
  UNCATEGORIZED_SEGMENT,
} from "~/features/common/nav/routes";
import {
  FidesTableV2,
  PaginationBar,
  TableActionBar,
  TableSkeletonLoader,
  useServerSidePagination,
} from "~/features/common/table/v2";
import {
  useAddMonitorResultAssetsMutation,
  useAddMonitorResultSystemsMutation,
  useGetDiscoveredAssetsQuery,
  useIgnoreMonitorResultAssetsMutation,
  useUpdateAssetsMutation,
  useUpdateAssetsSystemMutation,
} from "~/features/data-discovery-and-detection/action-center/action-center.slice";
import AddDataUsesModal from "~/features/data-discovery-and-detection/action-center/AddDataUsesModal";

import { SearchInput } from "../../SearchInput";
import { AssignSystemModal } from "../AssignSystemModal";
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
  const [isAssignSystemModalOpen, setIsAssignSystemModalOpen] =
    useState<boolean>(false);
  const [isAddDataUseModalOpen, setIsAddDataUseModalOpen] =
    useState<boolean>(false);
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

  const anyBulkActionIsLoading =
    isAddingResults ||
    isIgnoringResults ||
    isAddingAllResults ||
    isBulkUpdatingSystem;

  const disableAddAll =
    anyBulkActionIsLoading || systemId === UNCATEGORIZED_SEGMENT;

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
      tableInstance.resetRowSelection();
      successAlert(
        `${selectedUrns.length} assets from ${systemName} have been added to the system inventory.`,
        `Confirmed`,
      );
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
        errorAlert(getErrorMessage(result.error));
      } else {
        tableInstance.resetRowSelection();
        successAlert(
          `${selectedUrns.length} assets have been assigned to ${selectedSystem.label}.`,
          `Confirmed`,
        );
      }
    }
    setIsAssignSystemModalOpen(false);
  };

  const handleBulkAddDataUse = async (newDataUses: string[]) => {
    const selectedAssets = data?.items.filter((asset) =>
      selectedUrns.includes(asset.urn),
    );
    if (!selectedAssets) {
      return;
    }
    const assets = selectedAssets.map((asset) => {
      // eslint-disable-next-line @typescript-eslint/naming-convention
      const data_uses = uniq([...(asset.data_uses || []), ...newDataUses]);
      return {
        urn: asset.urn,
        data_uses,
      };
    });
    const result = await updateAssetsMutation({
      monitorId,
      assets,
    });
    if (isErrorResult(result)) {
      errorAlert(getErrorMessage(result.error));
    } else {
      tableInstance.resetRowSelection();
      successAlert(
        `Consent categories added to ${selectedUrns.length} assets from ${systemName}.`,
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
      tableInstance.resetRowSelection();
      successAlert(
        `${selectedUrns.length} assets from ${systemName} have been ignored and will not appear in future scans.`,
        `Confirmed`,
      );
    }
  };

  const handleAddAll = async () => {
    const assetCount = data?.items.length || 0;
    const result = await addMonitorResultSystemsMutation({
      monitor_config_key: monitorId,
      resolved_system_ids: [systemId],
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
                <MenuItem
                  fontSize="small"
                  onClick={() => setIsAddDataUseModalOpen(true)}
                  data-testid="bulk-add-data-use"
                >
                  Add consent category
                </MenuItem>
                <MenuItem
                  fontSize="small"
                  onClick={() => {
                    setIsAssignSystemModalOpen(true);
                  }}
                  data-testid="bulk-assign-system"
                >
                  Assign system
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
    </>
  );
};
