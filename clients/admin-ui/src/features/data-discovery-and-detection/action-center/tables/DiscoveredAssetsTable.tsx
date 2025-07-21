import {
  AntButton as Button,
  AntDefaultOptionType as DefaultOptionType,
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
import { uniq } from "lodash";
import { useRouter } from "next/router";
import { useEffect, useState } from "react";

import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import {
  ACTION_CENTER_ROUTE,
  SYSTEM_ROUTE,
  UNCATEGORIZED_SEGMENT,
} from "~/features/common/nav/routes";
import { SelectedText } from "~/features/common/table/SelectedText";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import {
  ConsentStatus,
  DiffStatus,
  StagedResourceAPIResponse,
} from "~/types/api";

import { DebouncedSearchInput } from "../../../common/DebouncedSearchInput";
import {
  useAddMonitorResultAssetsMutation,
  useAddMonitorResultSystemsMutation,
  useGetDiscoveredAssetsQuery,
  useIgnoreMonitorResultAssetsMutation,
  useRestoreMonitorResultAssetsMutation,
  useUpdateAssetsMutation,
  useUpdateAssetsSystemMutation,
} from "../action-center.slice";
import AddDataUsesModal from "../AddDataUsesModal";
import { AssignSystemModal } from "../AssignSystemModal";
import { ConsentBreakdownModal } from "../ConsentBreakdownModal";
import useActionCenterTabs, {
  ActionCenterTabHash,
} from "../hooks/useActionCenterTabs";
import { useDiscoveredAssetsColumns } from "../hooks/useDiscoveredAssetsColumns";
import { SuccessToastContent } from "../SuccessToastContent";

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
  const [firstItemConsentStatus, setFirstItemConsentStatus] = useState<
    ConsentStatus | null | undefined
  >();

  const [systemName, setSystemName] = useState(systemId);

  // Pagination state
  const [pageIndex, setPageIndex] = useState(1);
  const [pageSize, setPageSize] = useState(25);

  // Selection state
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const [selectedRowsMap, setSelectedRowsMap] = useState<
    Map<string, StagedResourceAPIResponse>
  >(new Map());

  const resetSelections = () => {
    setSelectedRowKeys([]);
    setSelectedRowsMap(new Map());
  };

  const [isAssignSystemModalOpen, setIsAssignSystemModalOpen] =
    useState<boolean>(false);
  const [isAddDataUseModalOpen, setIsAddDataUseModalOpen] =
    useState<boolean>(false);
  const [consentBreakdownModalData, setConsentBreakdownModalData] = useState<{
    stagedResource: StagedResourceAPIResponse;
    status: ConsentStatus;
  } | null>(null);

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

  const [searchQuery, setSearchQuery] = useState("");

  const toast = useToast();

  // Reset pagination when filters change
  useEffect(() => {
    setPageIndex(1);
  }, [monitorId, searchQuery]);

  const { filterTabs, activeTab, onTabChange, activeParams, actionsDisabled } =
    useActionCenterTabs(systemId);

  useEffect(() => {
    setPageIndex(1);
  }, [monitorId, searchQuery, activeTab]);

  // Reset selections when filters change
  useEffect(() => {
    resetSelections();
  }, [monitorId, searchQuery, activeTab]);

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
      setSystemName(firstSystemName);
      onSystemName?.(firstSystemName);
    }
  }, [data, systemId, onSystemName, systemName]);

  useEffect(() => {
    if (data?.items && !firstItemConsentStatus) {
      // this ensures that the column header remembers the consent status
      // even when the user navigates to a different paginated page
      const consentStatus = data.items.find(
        (item) => item.consent_aggregated === ConsentStatus.WITHOUT_CONSENT,
      )?.consent_aggregated;
      setFirstItemConsentStatus(consentStatus);
    }
  }, [data, firstItemConsentStatus]);

  const handleShowBreakdown = (
    stagedResource: StagedResourceAPIResponse,
    status: ConsentStatus,
  ) => {
    setConsentBreakdownModalData({ stagedResource, status });
  };

  const handleCloseBreakdown = () => {
    setConsentBreakdownModalData(null);
  };

  const { columns } = useDiscoveredAssetsColumns({
    readonly: actionsDisabled ?? false,
    onTabChange,
    aggregatedConsent: firstItemConsentStatus,
    onShowBreakdown: handleShowBreakdown,
  });

  // Get selected URNs from the map instead of selectedRows
  const selectedUrns = Array.from(selectedRowsMap.keys());
  const selectedRows = Array.from(selectedRowsMap.values());

  const handleBulkAdd = async () => {
    const result = await addMonitorResultAssetsMutation({
      urnList: selectedUrns,
    });

    const systemKey =
      selectedRows[0]?.user_assigned_system_key || selectedRows[0]?.system_key;
    const allAssetsHaveSameSystemKey = selectedRows.every((a) => {
      const assetKey = a.user_assigned_system_key || a.system_key;
      return assetKey === systemKey;
    });

    const systemToLink = allAssetsHaveSameSystemKey ? systemKey : undefined;

    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
    } else {
      toast(
        successToastParams(
          SuccessToastContent(
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
      resetSelections();
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
    if (!selectedRows.length) {
      return;
    }
    const assets = selectedRows.map((asset) => {
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

  const handleBulkIgnore = async () => {
    const result = await ignoreMonitorResultAssetsMutation({
      urnList: selectedUrns,
    });
    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
    } else {
      toast(
        successToastParams(
          systemName === UNCATEGORIZED_SEGMENT
            ? `${selectedUrns.length} uncategorized assets have been ignored and will not appear in future scans.`
            : `${selectedUrns.length} assets from ${systemName} have been ignored and will not appear in future scans.`,
          `Confirmed`,
        ),
      );
      resetSelections();
    }
  };

  const handleBulkRestore = async () => {
    const result = await restoreMonitorResultAssetsMutation({
      urnList: selectedUrns,
    });
    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
    } else {
      toast(
        successToastParams(
          `${selectedUrns.length} assets have been restored and will appear in future scans.`,
          `Confirmed`,
        ),
      );
      resetSelections();
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
      resetSelections();
    }
  };

  const handleTabChange = (tab: ActionCenterTabHash) => {
    onTabChange(tab);
    resetSelections();
  };

  // Update selectedRowKeys to only show current page selections when data changes
  useEffect(() => {
    if (data?.items) {
      const currentPageSelectedKeys = data.items
        .filter((item) => selectedRowsMap.has(item.urn))
        .map((item) => item.urn);
      setSelectedRowKeys(currentPageSelectedKeys);
    }
  }, [data, selectedRowsMap]);

  const rowSelection = {
    selectedRowKeys,
    onChange: (
      newSelectedRowKeys: React.Key[],
      newSelectedRows: StagedResourceAPIResponse[],
    ) => {
      setSelectedRowKeys(newSelectedRowKeys);

      // Update the map with current page selections
      const newMap = new Map(selectedRowsMap);

      // Remove deselected items from current page
      if (data?.items) {
        data.items.forEach((item) => {
          if (!newSelectedRowKeys.includes(item.urn)) {
            newMap.delete(item.urn);
          }
        });
      }

      // Add newly selected items
      newSelectedRows.forEach((row) => {
        newMap.set(row.urn, row);
      });

      setSelectedRowsMap(newMap);
    },
  };

  const handleTableChange = (pagination: any) => {
    setPageIndex(pagination.current);
    setPageSize(pagination.pageSize);
  };

  if (!monitorId || !systemId) {
    return null;
  }

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
        <DebouncedSearchInput
          value={searchQuery}
          onChange={setSearchQuery}
          placeholder="Search by asset name..."
        />
        <Space size="large">
          {!!selectedUrns.length && (
            <SelectedText count={selectedUrns.length} />
          )}
          <Space size="small">
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
                  ...(activeParams?.diff_status?.includes(DiffStatus.MUTED)
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
          </Space>
        </Space>
      </Flex>
      <Table
        dataSource={data?.items || []}
        columns={columns}
        loading={isLoading || isFetching}
        rowKey={(record) => record.urn}
        rowSelection={
          activeTab === ActionCenterTabHash.RECENT_ACTIVITY
            ? undefined
            : rowSelection
        }
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
      {consentBreakdownModalData && (
        <ConsentBreakdownModal
          isOpen={!!consentBreakdownModalData}
          stagedResource={consentBreakdownModalData.stagedResource}
          status={consentBreakdownModalData.status}
          onCancel={handleCloseBreakdown}
        />
      )}
    </>
  );
};

export default DiscoveredAssetsTable;
