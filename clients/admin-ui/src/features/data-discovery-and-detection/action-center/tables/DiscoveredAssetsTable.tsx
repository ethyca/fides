import {
  getCoreRowModel,
  RowSelectionState,
  useReactTable,
} from "@tanstack/react-table";
import {
  AntButton as Button,
  AntDefaultOptionType as DefaultOptionType,
  AntDropdown as Dropdown,
  AntEmpty as Empty,
  AntTabs,
  AntTooltip as Tooltip,
  Flex,
  HStack,
  Icons,
  Text,
  useToast,
} from "fidesui";
import { uniq } from "lodash";
import { useRouter } from "next/router";
import { useEffect, useState } from "react";

import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
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
  useAddMonitorResultAssetsMutation,
  useAddMonitorResultSystemsMutation,
  useGetDiscoveredAssetsQuery,
  useIgnoreMonitorResultAssetsMutation,
  useRestoreMonitorResultAssetsMutation,
  useUpdateAssetsMutation,
  useUpdateAssetsSystemMutation,
} from "~/features/data-discovery-and-detection/action-center/action-center.slice";
import AddDataUsesModal from "~/features/data-discovery-and-detection/action-center/AddDataUsesModal";
import useActionCenterTabs, {
  ActionCenterTabHash,
} from "~/features/data-discovery-and-detection/action-center/tables/useActionCenterTabs";
import { successToastContent } from "~/features/data-discovery-and-detection/action-center/utils/successToastContent";
import { DiffStatus } from "~/types/api";

import { DebouncedSearchInput } from "../../../common/DebouncedSearchInput";
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
  const [
    restoreMonitorResultAssetsMutation,
    { isLoading: isRestoringResults },
  ] = useRestoreMonitorResultAssetsMutation();

  const anyBulkActionIsLoading =
    isAddingResults ||
    isIgnoringResults ||
    isAddingAllResults ||
    isBulkUpdatingSystem ||
    isRestoringResults;

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

  const toast = useToast();

  useEffect(() => {
    resetPageIndexToDefault();
  }, [monitorId, searchQuery, resetPageIndexToDefault]);

  const { filterTabs, activeTab, onTabChange, activeParams, actionsDisabled } =
    useActionCenterTabs(systemId);

  const { data, isLoading, isFetching } = useGetDiscoveredAssetsQuery({
    key: monitorId,
    page: pageIndex,
    size: pageSize,
    search: searchQuery,
    ...activeParams,
  });

  useEffect(() => {
    if (data) {
      const firstSystemName =
        data.items[0]?.system || systemName || systemId || "";
      setTotalPages(data.pages || 1);
      setSystemName(firstSystemName);
      onSystemName?.(firstSystemName);
    }
  }, [data, systemId, onSystemName, setTotalPages, systemName]);

  const { columns } = useDiscoveredAssetsColumns({
    readonly: actionsDisabled,
    onTabChange,
  });

  const tableInstance = useReactTable({
    getCoreRowModel: getCoreRowModel(),
    columns,
    manualPagination: true,
    data: data?.items || [],
    columnResizeMode: "onChange",
    onRowSelectionChange: setRowSelection,
    getRowId: (row) => row.urn,
    state: {
      rowSelection,
    },
  });

  const selectedUrns = tableInstance
    .getSelectedRowModel()
    .rows.map((row) => row.original.urn);

  const handleBulkAdd = async () => {
    const result = await addMonitorResultAssetsMutation({
      urnList: selectedUrns,
    });
    const selectedAssets =
      data?.items.filter((asset) => selectedUrns.includes(asset.urn)) ?? [];

    const systemKey =
      selectedAssets[0]?.user_assigned_system_key ||
      selectedAssets[0]?.system_key;
    const allAssetsHaveSameSystemKey = selectedAssets.every((a) => {
      const assetKey = a.user_assigned_system_key || a.system_key;
      return assetKey === systemKey;
    });

    const systemKeyFromResult = result.data?.[0]?.promoted_system_key;

    const systemToLink = allAssetsHaveSameSystemKey
      ? (systemKeyFromResult ?? systemKey)
      : undefined;

    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
    } else {
      tableInstance.resetRowSelection();
      toast(
        successToastParams(
          successToastContent(
            `${selectedUrns.length} assets from ${systemName} have been added to the system inventory.`,
            systemToLink
              ? () =>
                  router.push(
                    `${SYSTEM_ROUTE}/configure/${systemToLink}#assets`,
                  )
              : () => router.push(SYSTEM_ROUTE),
          ),
        ),
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
        toast(errorToastParams(getErrorMessage(result.error)));
      } else {
        toast(
          successToastParams(
            `${selectedUrns.length} assets have been assigned to ${selectedSystem.label}.`,
            `Confirmed`,
          ),
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
      const user_assigned_data_uses = uniq([
        ...(asset.user_assigned_data_uses || asset.data_uses || []),
        ...newDataUses,
      ]);
      return {
        urn: asset.urn,
        user_assigned_data_uses,
      };
    });
    const result = await updateAssetsMutation({
      monitorId,
      assets,
    });
    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
    } else {
      toast(
        successToastParams(
          `Consent categories added to ${selectedUrns.length} assets${
            systemName ? ` from ${systemName}` : ""
          }.`,
          `Confirmed`,
        ),
      );
    }
    setIsAddDataUseModalOpen(false);
  };

  // TODO: add toast link to ignored tab
  const handleBulkIgnore = async () => {
    const result = await ignoreMonitorResultAssetsMutation({
      urnList: selectedUrns,
    });
    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
    } else {
      tableInstance.resetRowSelection();
      toast(
        successToastParams(
          systemName === UNCATEGORIZED_SEGMENT
            ? `${selectedUrns.length} uncategorized assets have been ignored and will not appear in future scans.`
            : `${selectedUrns.length} assets from ${systemName} have been ignored and will not appear in future scans.`,
          `Confirmed`,
        ),
      );
    }
  };

  const handleBulkRestore = async () => {
    const result = await restoreMonitorResultAssetsMutation({
      urnList: selectedUrns,
    });
    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
    } else {
      tableInstance.resetRowSelection();
      toast(
        successToastParams(
          `${selectedUrns.length} assets have been restored and will appear in future scans.`,
          `Confirmed`,
        ),
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
      toast(errorToastParams(getErrorMessage(result.error)));
    } else {
      router.push(`${ACTION_CENTER_ROUTE}/${monitorId}`);
      toast(
        successToastParams(
          `${assetCount} assets from ${systemName} have been added to the system inventory.`,
          `Confirmed`,
        ),
      );
    }
  };

  const handleTabChange = (tab: ActionCenterTabHash) => {
    onTabChange(tab);
    setRowSelection({});
  };

  if (!monitorId || !systemId) {
    return null;
  }

  if (isLoading) {
    return <TableSkeletonLoader rowHeight={36} numRows={36} />;
  }

  return (
    <>
      <AntTabs
        items={filterTabs.map((tab) => ({
          key: tab.hash,
          label: tab.label,
        }))}
        activeKey={activeTab}
        onChange={(tab) => handleTabChange(tab as ActionCenterTabHash)}
      />
      <TableActionBar>
        <DebouncedSearchInput
          value={searchQuery}
          onChange={setSearchQuery}
          placeholder="Search by asset name..."
        />
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
            <Dropdown
              menu={{
                items: [
                  {
                    key: "add",
                    label: "Add",
                    onClick: handleBulkAdd,
                  },
                  {
                    key: "add-data-use",
                    label: "Add consent category",
                    onClick: () => setIsAddDataUseModalOpen(true),
                  },
                  {
                    key: "assign-system",
                    label: "Assign system",
                    onClick: () => setIsAssignSystemModalOpen(true),
                  },
                  ...(activeParams.diff_status.includes(DiffStatus.MUTED)
                    ? [
                        {
                          key: "restore",
                          label: "Restore",
                          onClick: handleBulkRestore,
                        },
                      ]
                    : [
                        {
                          type: "divider" as const,
                        },
                        {
                          key: "ignore",
                          label: "Ignore",
                          onClick: handleBulkIgnore,
                        },
                      ]),
                ],
              }}
              trigger={["click"]}
            >
              <Button
                icon={<Icons.ChevronDown />}
                iconPosition="end"
                loading={anyBulkActionIsLoading}
                data-testid="bulk-actions-menu"
                disabled={
                  !selectedUrns.length ||
                  anyBulkActionIsLoading ||
                  actionsDisabled
                }
                type="primary"
              >
                Actions
              </Button>
            </Dropdown>

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
