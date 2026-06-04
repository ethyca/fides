import {
  Button,
  Checkbox,
  DefaultOptionType,
  Dropdown,
  Empty,
  Flex,
  Icons,
  List,
  Pagination,
  Splitter,
  Text,
  Title,
  Tooltip,
  useMessage,
  useModal,
  useNotification,
} from "fidesui";
import { uniq } from "lodash";
import { useRouter } from "next/router";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { useAppDispatch } from "~/app/hooks";
import { DebouncedSearchInput } from "~/features/common/DebouncedSearchInput";
import { useFeatures } from "~/features/common/features/features.slice";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { SYSTEM_ROUTE } from "~/features/common/nav/routes";
import { useAntPagination } from "~/features/common/pagination/useAntPagination";
import ToastLink from "~/features/common/ToastLink";
import { DiffStatus, StagedResourceAPIResponse } from "~/types/api";

import {
  actionCenterUtil,
  useAddMonitorResultAssetsMutation,
  useGetDiscoveredAssetsQuery,
  useGetMonitorConfigQuery,
  useIgnoreMonitorResultAssetsMutation,
  useUpdateAssetsMutation,
  useUpdateAssetsSystemMutation,
  useUpdateAssetsSystemOptimisticMutation,
} from "../action-center.slice";
import AddDataUsesModal from "../AddDataUsesModal";
import { AssignSystemModal } from "../AssignSystemModal";
import { ConsentBreakdownModal } from "../ConsentBreakdownModal";
import { DiscoveredAssetsColumnKeys } from "../constants";
import { useConfirmPromotion } from "../hooks/useConfirmPromotion";
import hasConsentComplianceIssue from "../utils/hasConsentComplianceIssue";
import { AssetDetailsDrawer } from "./AssetDetailsDrawer";
import WebsiteAssetExplorerTree, {
  WebsiteAssetExplorerTreeRef,
} from "./WebsiteAssetExplorerTree";
import WebsiteAssetFilters from "./WebsiteAssetFilters";
import { WebsiteAssetListItem } from "./WebsiteAssetListItem";

const WEBSITE_ASSET_PAGE_SIZE = 25;

interface WebsiteMonitorResultsProps {
  monitorId: string;
  /** Visibility toggles from the page header (top-right settings dropdown). */
  showApproved?: boolean;
  showIgnored?: boolean;
}

interface DiscoveredAssetsFilterValues {
  resource_type?: string[];
  data_uses?: string[];
  locations?: string[];
  consent_aggregated?: string[];
}

// The shared per-row actions cell expects an onTabChange callback (used by its
// "View" toast link). There are no tabs here, so it's a no-op.
const noTabChange = async () => {};

const WebsiteMonitorResults = ({
  monitorId,
  showApproved,
  showIgnored,
}: WebsiteMonitorResultsProps) => {
  const router = useRouter();
  const dispatch = useAppDispatch();
  const message = useMessage();
  const notification = useNotification();
  const { flags } = useFeatures();
  const { assetConsentStatusLabels } = flags;

  const treeRef = useRef<WebsiteAssetExplorerTreeRef>(null);
  const modalApi = useModal();

  const [selectedSystemId, setSelectedSystemId] = useState<string>();
  // Assets reassigned in the drawer stay put until the user confirms a move on
  // tree-navigate. Keyed by urn → its pending target system name.
  const [pendingReassignments, setPendingReassignments] = useState<
    Map<string, { assetName: string; toSystemName: string }>
  >(new Map());
  const [detailsAsset, setDetailsAsset] = useState<StagedResourceAPIResponse>();
  const [selectedUrns, setSelectedUrns] = useState<Set<string>>(new Set());
  const [searchQuery, setSearchQuery] = useState("");
  const [columnFilters, setColumnFilters] =
    useState<DiscoveredAssetsFilterValues>({});

  const [isAssignSystemModalOpen, setIsAssignSystemModalOpen] = useState(false);
  const [isAddDataUseModalOpen, setIsAddDataUseModalOpen] = useState(false);
  const [complianceModalAsset, setComplianceModalAsset] =
    useState<StagedResourceAPIResponse | null>(null);

  const { paginationProps, pageIndex, pageSize, resetPagination } =
    useAntPagination({ defaultPageSize: WEBSITE_ASSET_PAGE_SIZE });

  // Attention-required (additions) by default; the header settings dropdown
  // adds approved (monitored) and/or ignored (muted) resources.
  const diffStatus = useMemo(
    () => [
      DiffStatus.ADDITION,
      ...(showApproved ? [DiffStatus.MONITORED] : []),
      ...(showIgnored ? [DiffStatus.MUTED] : []),
    ],
    [showApproved, showIgnored],
  );

  const { data: monitorConfigData } = useGetMonitorConfigQuery({
    monitor_config_id: monitorId,
  });

  const assetsQueryArgs = useMemo(
    () => ({
      key: monitorId,
      page: pageIndex,
      size: pageSize,
      search: searchQuery,
      sort_by: [DiscoveredAssetsColumnKeys.NAME],
      sort_asc: true,
      diff_status: diffStatus,
      system: selectedSystemId,
      ...columnFilters,
    }),
    [
      monitorId,
      pageIndex,
      pageSize,
      searchQuery,
      diffStatus,
      selectedSystemId,
      columnFilters,
    ],
  );

  // No `skip`: when no system is selected (undefined), the query omits
  // resolved_system_id and returns assets across all systems.
  const { data, isFetching } = useGetDiscoveredAssetsQuery(assetsQueryArgs);

  const assets = useMemo(() => {
    // Surface assets with compliance issues at the top of the list.
    const items = data?.items ?? [];
    return [...items].sort((a, b) => {
      const aIssue = hasConsentComplianceIssue(a.consent_aggregated) ? 1 : 0;
      const bIssue = hasConsentComplianceIssue(b.consent_aggregated) ? 1 : 0;
      return bIssue - aIssue;
    });
  }, [data?.items]);
  const itemsByUrn = useMemo(
    () => new Map(assets.map((asset) => [asset.urn, asset])),
    [assets],
  );
  const selectedRows = useMemo(
    () =>
      [...selectedUrns]
        .map((urn) => itemsByUrn.get(urn))
        .filter((a): a is StagedResourceAPIResponse => !!a),
    [selectedUrns, itemsByUrn],
  );

  const [addMonitorResultAssetsMutation] = useAddMonitorResultAssetsMutation();
  const [ignoreMonitorResultAssetsMutation] =
    useIgnoreMonitorResultAssetsMutation();
  const [updateAssetsSystemMutation, { isLoading: isBulkUpdatingSystem }] =
    useUpdateAssetsSystemMutation();
  const [updateAssetsMutation, { isLoading: isBulkAddingDataUses }] =
    useUpdateAssetsMutation();
  const [updateAssetsSystemOptimisticMutation] =
    useUpdateAssetsSystemOptimisticMutation();
  const { confirmPromotion } = useConfirmPromotion();

  const resetSelections = useCallback(() => setSelectedUrns(new Set()), []);

  // Reset pagination + selection whenever the selected system changes.
  useEffect(() => {
    resetPagination();
    resetSelections();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedSystemId]);

  const handleSelectSystem = useCallback(
    async (systemId: string | undefined) => {
      // If reassignments are pending and we're navigating to a different
      // system, ask whether to relocate them now or leave them in place.
      if (pendingReassignments.size > 0 && systemId !== selectedSystemId) {
        const pending = [...pendingReassignments.entries()];
        const isSingle = pending.length === 1;
        const move = await modalApi.confirm({
          title: "Move assets to their new systems?",
          centered: true,
          okText: "Move now",
          cancelText: "Keep here for now",
          content: (
            <>
              <Text>
                {isSingle
                  ? "You changed the system for this asset:"
                  : `You changed the system for ${pending.length} assets:`}
              </Text>
              <ul className="my-2 ml-5 list-disc">
                {pending.map(([urn, p]) => (
                  <li key={urn}>
                    <Text>{`${p.assetName} → ${p.toSystemName}`}</Text>
                  </li>
                ))}
              </ul>
              <Text type="secondary">
                {isSingle
                  ? "“Move now” updates the list so it appears under its new system. “Keep here for now” leaves it in the current view until you refresh."
                  : "“Move now” updates the list so each appears under its new system. “Keep here for now” leaves them in the current view until you refresh."}
              </Text>
            </>
          ),
        });
        if (move) {
          // Backend already persisted each reassignment; refetching the list +
          // tree aggregate relocates the assets and recomputes counts.
          dispatch(
            actionCenterUtil.invalidateTags(["Discovery Monitor Results"]),
          );
          setPendingReassignments(new Map());
        }
        // Either way, complete the navigation.
      }
      setSelectedSystemId(systemId);
    },
    [pendingReassignments, selectedSystemId, modalApi, dispatch],
  );

  const handleFiltersChange = useCallback(
    (next: DiscoveredAssetsFilterValues) => {
      setColumnFilters(next);
      resetPagination();
      resetSelections();
    },
    [resetPagination, resetSelections],
  );

  const handleSearch = useCallback(
    (value: string) => {
      setSearchQuery(value);
      resetPagination();
    },
    [resetPagination],
  );

  const handleToggleAsset = useCallback((urn: string, selected: boolean) => {
    setSelectedUrns((prev) => {
      const next = new Set(prev);
      if (selected) {
        next.add(urn);
      } else {
        next.delete(urn);
      }
      return next;
    });
  }, []);

  const pageUrns = useMemo(() => assets.map((a) => a.urn), [assets]);
  const allPageSelected =
    pageUrns.length > 0 && pageUrns.every((urn) => selectedUrns.has(urn));
  const somePageSelected = pageUrns.some((urn) => selectedUrns.has(urn));

  const handleToggleSelectAll = useCallback(() => {
    setSelectedUrns((prev) => {
      const next = new Set(prev);
      if (pageUrns.every((urn) => next.has(urn))) {
        pageUrns.forEach((urn) => next.delete(urn));
      } else {
        pageUrns.forEach((urn) => next.add(urn));
      }
      return next;
    });
  }, [pageUrns]);

  /**
   * Rich-feedback inline system assignment: assign without invalidating (so the
   * row stays put), then optimistically patch the cached row and record a
   * pending reassignment. The actual relocation + count change is deferred
   * until the user confirms a move when navigating away in the tree.
   */
  const handleSystemAssign = useCallback(
    async (
      asset: StagedResourceAPIResponse,
      fidesKey: string,
      systemName: string,
    ): Promise<boolean> => {
      const result = await updateAssetsSystemOptimisticMutation({
        monitorId,
        urnList: [asset.urn],
        systemKey: fidesKey,
      });
      if (isErrorResult(result)) {
        message.error(getErrorMessage(result.error));
        return false;
      }

      dispatch(
        actionCenterUtil.updateQueryData(
          "getDiscoveredAssets",
          assetsQueryArgs,
          (draft) => {
            const cached = draft.items.find((item) => item.urn === asset.urn);
            if (cached) {
              cached.user_assigned_system_key = fidesKey;
              // Show the reassigned system on the row (the asset still stays put
              // until the user confirms a move on tree-navigate).
              cached.system = systemName;
            }
          },
        ),
      );

      setPendingReassignments((prev) => {
        const next = new Map(prev);
        next.set(asset.urn, {
          assetName: asset.name ?? asset.urn,
          toSystemName: systemName,
        });
        return next;
      });

      notification.success({
        message: "System reassigned",
        description: `"${asset.name}" reassigned to ${systemName} (pending). You'll be asked to move it when you switch systems.`,
      });
      return true;
    },
    [
      updateAssetsSystemOptimisticMutation,
      monitorId,
      dispatch,
      assetsQueryArgs,
      message,
      notification,
    ],
  );

  /**
   * Remove an asset's system assignment from the drawer. Clears optimistically
   * (so it reads as Unassigned and stays put) and records a pending change so
   * the move dialog can relocate it to Uncategorized on tree-navigate.
   */
  const handleSystemRemove = useCallback(
    async (asset: StagedResourceAPIResponse): Promise<void> => {
      // An empty systemKey clears the assignment server-side.
      const result = await updateAssetsSystemOptimisticMutation({
        monitorId,
        urnList: [asset.urn],
        systemKey: "",
      });
      if (isErrorResult(result)) {
        message.error(getErrorMessage(result.error));
        return;
      }

      dispatch(
        actionCenterUtil.updateQueryData(
          "getDiscoveredAssets",
          assetsQueryArgs,
          (draft) => {
            const cached = draft.items.find((item) => item.urn === asset.urn);
            if (cached) {
              cached.user_assigned_system_key = null;
              cached.system = null;
            }
          },
        ),
      );

      setPendingReassignments((prev) => {
        const next = new Map(prev);
        next.set(asset.urn, {
          assetName: asset.name ?? asset.urn,
          toSystemName: "Unassigned",
        });
        return next;
      });

      notification.success({
        message: "System removed",
        description: `"${asset.name}" is now unassigned (pending). You'll be asked to move it when you switch systems.`,
      });
    },
    [
      updateAssetsSystemOptimisticMutation,
      monitorId,
      dispatch,
      assetsQueryArgs,
      message,
      notification,
    ],
  );

  const hasUncategorizedSelected = selectedRows.some((a) => !a.system);

  const handleBulkApprove = useCallback(async () => {
    const urnList = [...selectedUrns];
    const confirmed = await confirmPromotion(urnList);
    if (!confirmed) {
      return;
    }
    const result = await addMonitorResultAssetsMutation({ urnList });
    if (isErrorResult(result)) {
      message.error(getErrorMessage(result.error));
    } else {
      notification.success({
        message: "Approved",
        description: `${urnList.length} assets have been added to the system inventory.`,
        actions: (
          <ToastLink onClick={() => router.push(SYSTEM_ROUTE)}>View</ToastLink>
        ),
      });
      resetSelections();
    }
  }, [
    selectedUrns,
    confirmPromotion,
    addMonitorResultAssetsMutation,
    message,
    notification,
    router,
    resetSelections,
  ]);

  const handleBulkIgnore = useCallback(async () => {
    const result = await ignoreMonitorResultAssetsMutation({
      urnList: [...selectedUrns],
    });
    if (isErrorResult(result)) {
      message.error(getErrorMessage(result.error));
    } else {
      message.success(
        `${selectedUrns.size} assets have been ignored and will not appear in future scans.`,
      );
      resetSelections();
    }
  }, [
    selectedUrns,
    ignoreMonitorResultAssetsMutation,
    message,
    resetSelections,
  ]);

  const handleBulkAssignSystem = useCallback(
    async (selectedSystem?: DefaultOptionType) => {
      if (typeof selectedSystem?.value !== "string") {
        return;
      }
      const result = await updateAssetsSystemMutation({
        monitorId,
        urnList: [...selectedUrns],
        systemKey: selectedSystem.value,
      });
      if (isErrorResult(result)) {
        message.error(getErrorMessage(result.error));
      } else {
        message.success(
          `${selectedUrns.size} assets have been assigned to ${selectedSystem.label}.`,
        );
        resetSelections();
      }
      setIsAssignSystemModalOpen(false);
    },
    [
      updateAssetsSystemMutation,
      monitorId,
      selectedUrns,
      message,
      resetSelections,
    ],
  );

  const handleBulkAddDataUse = useCallback(
    async (newDataUses: string[]) => {
      if (!selectedRows.length) {
        return;
      }
      const updatedAssets = selectedRows.map((asset) => ({
        urn: asset.urn,
        // eslint-disable-next-line @typescript-eslint/naming-convention
        user_assigned_data_uses: uniq([
          ...(asset.preferred_data_uses || []),
          ...newDataUses,
        ]),
      }));
      const result = await updateAssetsMutation({
        monitorId,
        assets: updatedAssets as StagedResourceAPIResponse[],
      });
      if (isErrorResult(result)) {
        message.error(getErrorMessage(result.error));
      } else {
        message.success(
          `Consent categories added to ${selectedRows.length} assets.`,
        );
        resetSelections();
      }
      setIsAddDataUseModalOpen(false);
    },
    [selectedRows, updateAssetsMutation, monitorId, message, resetSelections],
  );

  const hasSelection = selectedUrns.size > 0;

  const bulkMenuItems = [
    {
      key: "approve",
      label: (
        <Tooltip
          title={
            hasUncategorizedSelected
              ? "The selected assets must be assigned to a system before you can approve them."
              : undefined
          }
        >
          Approve
        </Tooltip>
      ),
      onClick: handleBulkApprove,
      disabled: hasUncategorizedSelected,
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
    { type: "divider" as const },
    { key: "ignore", label: "Ignore", onClick: handleBulkIgnore },
  ];

  return (
    <>
      <Splitter className="h-[calc(100%-48px)] overflow-hidden">
        <Splitter.Panel
          defaultSize={260}
          style={{ paddingRight: "var(--fidesui-padding-md)" }}
        >
          <WebsiteAssetExplorerTree
            ref={treeRef}
            monitorId={monitorId}
            diffStatus={diffStatus}
            search={searchQuery}
            onSelectSystem={handleSelectSystem}
          />
        </Splitter.Panel>
        <Splitter.Panel
          style={{
            paddingLeft: "var(--fidesui-padding-md)",
            overflow: "hidden",
          }}
        >
          <Flex vertical gap="medium" className="h-full">
            <Flex justify="space-between" align="center">
              <Title level={2} ellipsis>
                Monitor results
              </Title>
              {monitorConfigData?.last_monitored && (
                <Text type="secondary">
                  Last scan:{" "}
                  {new Date(monitorConfigData.last_monitored).toLocaleString()}
                </Text>
              )}
            </Flex>

            <Flex gap="small" wrap="wrap" align="center">
              <DebouncedSearchInput
                value={searchQuery}
                onChange={handleSearch}
                placeholder="Search by asset name..."
              />
              {/* Filters + Actions are right-aligned */}
              <Flex gap="small" wrap="wrap" align="center" className="ml-auto">
                <WebsiteAssetFilters
                  monitorId={monitorId}
                  resolvedSystemId={selectedSystemId ?? ""}
                  diffStatus={diffStatus}
                  search={searchQuery}
                  value={columnFilters}
                  onChange={handleFiltersChange}
                  showComplianceFilter={assetConsentStatusLabels}
                />
                <Dropdown
                  menu={{ items: bulkMenuItems }}
                  trigger={["click"]}
                  disabled={!hasSelection}
                >
                  <Button
                    type="primary"
                    icon={<Icons.ChevronDown />}
                    iconPlacement="end"
                    data-testid="bulk-actions-menu"
                  >
                    Actions
                  </Button>
                </Dropdown>
              </Flex>
            </Flex>

            <Flex gap="medium" align="center">
              <Checkbox
                id="select-all"
                checked={allPageSelected}
                indeterminate={!allPageSelected && somePageSelected}
                onChange={handleToggleSelectAll}
              />
              <label htmlFor="select-all">Select all</label>
              {hasSelection && (
                <Text strong>
                  {selectedUrns.size.toLocaleString()} selected
                </Text>
              )}
            </Flex>

            <List
              // -ml-3 / pl-1 aligns the row checkboxes under the select-all
              // checkbox (matches the datastore schema explorer list).
              className="-ml-3 h-full overflow-y-scroll pl-1"
              loading={isFetching}
              dataSource={assets}
              locale={{
                emptyText: (
                  <Empty
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                    description="All caught up!"
                  />
                ),
              }}
              renderItem={(asset) => (
                <WebsiteAssetListItem
                  key={asset.urn}
                  asset={asset}
                  selected={selectedUrns.has(asset.urn)}
                  onSelect={handleToggleAsset}
                  onNavigate={setDetailsAsset}
                  readonly={false}
                  showActions
                  showComplianceStatus={assetConsentStatusLabels}
                  onTabChange={noTabChange}
                  showComplianceIssueDetails={setComplianceModalAsset}
                />
              )}
            />

            <Pagination
              {...paginationProps}
              showSizeChanger={{ suffixIcon: <Icons.ChevronDown /> }}
              total={data?.total || 0}
              hideOnSinglePage={
                paginationProps.pageSize?.toString() ===
                paginationProps.pageSizeOptions?.[0]
              }
            />
          </Flex>
        </Splitter.Panel>
      </Splitter>

      <AssetDetailsDrawer
        asset={detailsAsset}
        open={!!detailsAsset}
        onClose={() => setDetailsAsset(undefined)}
        readonly={false}
        onTabChange={noTabChange}
        onSystemAssign={handleSystemAssign}
        onSystemRemove={handleSystemRemove}
      />

      <AssignSystemModal
        isOpen={isAssignSystemModalOpen}
        onClose={() => setIsAssignSystemModalOpen(false)}
        onSave={handleBulkAssignSystem}
        isSaving={isBulkUpdatingSystem}
      />
      <AddDataUsesModal
        isOpen={isAddDataUseModalOpen}
        onClose={() => setIsAddDataUseModalOpen(false)}
        onSave={handleBulkAddDataUse}
        isSaving={isBulkAddingDataUses}
      />
      {complianceModalAsset && (
        <ConsentBreakdownModal
          isOpen={!!complianceModalAsset}
          stagedResource={complianceModalAsset}
          onCancel={() => setComplianceModalAsset(null)}
        />
      )}
    </>
  );
};

export default WebsiteMonitorResults;
