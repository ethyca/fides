import {
  Alert,
  Button,
  Checkbox,
  DefaultOptionType,
  DisplayValueType,
  Dropdown,
  Empty,
  Flex,
  Icons,
  List,
  Pagination,
  Select,
  Space,
  Splitter,
  Tooltip,
  Typography,
  useMessage,
} from "fidesui";
import { useEffect, useMemo, useState } from "react";

import { DebouncedSearchInput } from "~/features/common/DebouncedSearchInput";
import { useSearch } from "~/features/common/hooks";
import { UNCATEGORIZED_SEGMENT } from "~/features/common/nav/routes";
import { DiffStatus, SystemStagedResourcesAggregateRecord } from "~/types/api";
import { CloudInfraStagedResource } from "~/types/api/models/CloudInfraStagedResource";

import { MockAssignSystemModal } from "../components/MockAssignSystemModal";
import { MockCloudInfraResourceDetailsDrawer } from "../components/MockCloudInfraResourceDetailsDrawer";
import { MockCloudInfraResourceListItem } from "../components/MockCloudInfraResourceListItem";
import { useCloudInfraFilters } from "../fields/useCloudInfraFilters";
import RegexToggle from "../forms/RegexToggle";
import { useMockCloudInfraResources } from "../hooks/useMockCloudInfraResources";
import { MOCK_AWS_RESOURCES } from "../mock/awsCloudInfraMock";
import { getServiceLabel } from "../utils/cloudInfraServiceInfo";
import WebsiteAssetExplorerTree from "../website/WebsiteAssetExplorerTree";
import { WebsiteSystemTreeNodeData } from "../website/websiteTreeUtils";

const { Text } = Typography;

const DEFAULT_STATUS_FILTERS = [DiffStatus.ADDITION, DiffStatus.REMOVAL];
const PAGE_SIZE_OPTIONS = [25, 50, 100];

const STATUS_FILTER_OPTIONS = [
  { label: "New", value: DiffStatus.ADDITION },
  { label: "Removed", value: DiffStatus.REMOVAL },
];

const renderTagPlaceholder = (omittedValues: DisplayValueType[]) => (
  <Tooltip
    title={
      <Flex vertical>
        {omittedValues.map(({ label, value }, index) => (
          <span key={value ?? index}>{label}</span>
        ))}
      </Flex>
    }
  >
    <span>+ {omittedValues.length}</span>
  </Tooltip>
);

interface MockCloudInfraResourcesTableProps {
  showIgnored?: boolean;
  showApproved?: boolean;
}

export const MockCloudInfraResourcesTable = ({
  showIgnored = false,
  showApproved = false,
}: MockCloudInfraResourcesTableProps) => {
  const messageApi = useMessage();
  const filters = useCloudInfraFilters();
  const search = useSearch();
  const [searchRegex, setSearchRegex] = useState(false);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  // Tree container selection — supports modifier-key multi-select for bulk
  // actions; also drives the list filter (union of selected systems).
  const [selectedSystemKeys, setSelectedSystemKeys] = useState<string[]>([]);
  // Recently-changed urns that should "stay put" in the current filtered view
  // until you navigate to another tree node (avoids the jarring vanish when a
  // resource is assigned/unassigned while filtered).
  const [stickyUrns, setStickyUrns] = useState<Set<string>>(new Set());
  const [page, setPage] = useState(1);
  const [detailsResource, setDetailsResource] =
    useState<CloudInfraStagedResource | null>(null);
  const [bulkAssignOpen, setBulkAssignOpen] = useState(false);
  const [pageSize, setPageSize] = useState(PAGE_SIZE_OPTIONS[0]);

  const effectiveStatusFilters = useMemo(() => {
    const statuses = new Set<string>(
      filters.statusFilters && filters.statusFilters.length > 0
        ? filters.statusFilters
        : DEFAULT_STATUS_FILTERS,
    );
    if (showIgnored) {
      statuses.add(DiffStatus.MUTED);
    }
    if (showApproved) {
      statuses.add(DiffStatus.MONITORED);
    }
    return Array.from(statuses);
  }, [filters.statusFilters, showIgnored, showApproved]);

  const {
    data,
    isLoading,
    getAssignedSystems,
    addSystem,
    removeSystem,
    clearSystems,
    approve,
    ignore,
    restore,
  } = useMockCloudInfraResources({
    statusFilters: effectiveStatusFilters,
    locationFilters: filters.locationFilters,
    serviceFilters: filters.serviceFilters,
    search: search.searchQuery ?? "",
    searchRegex,
  });

  const markSticky = (urns: string[]) =>
    setStickyUrns((prev) => new Set([...prev, ...urns]));

  // Navigating to another tree node clears the sticky set so the list
  // re-filters cleanly (assigned resources correctly leave "Unassigned").
  const selectionKey = selectedSystemKeys.join("|");
  useEffect(() => {
    setStickyUrns(new Set());
  }, [selectionKey]);

  // Build the explorer tree: a single "Resources" grouping for unassigned
  // resources, plus a node per assigned system (with resource counts). Systems
  // appear here as they get assigned.
  const treeNodes = useMemo<WebsiteSystemTreeNodeData[]>(() => {
    const systemMap = new Map<string, { label: string; count: number }>();
    let unassigned = 0;
    data.items.forEach((item) => {
      const systems = getAssignedSystems(item.urn);
      if (!systems.length) {
        unassigned += 1;
        return;
      }
      systems.forEach((s) => {
        const key = String(s.value);
        const prev = systemMap.get(key);
        systemMap.set(key, {
          label: String(s.label ?? s.value),
          count: (prev?.count ?? 0) + 1,
        });
      });
    });
    const makeNode = (
      key: string,
      title: string,
      count: number,
    ): WebsiteSystemTreeNodeData => ({
      key,
      title,
      isLeaf: true,
      selectable: true,
      record: {
        id: key === UNCATEGORIZED_SEGMENT ? null : key,
        name: title,
        total_updates: count,
      } as SystemStagedResourcesAggregateRecord,
      count,
    });
    return [
      makeNode(UNCATEGORIZED_SEGMENT, "Unassigned resources", unassigned),
      ...Array.from(systemMap.entries()).map(([key, v]) =>
        makeNode(key, v.label, v.count),
      ),
    ];
  }, [data.items, getAssignedSystems]);

  // Filter the list by the selected tree node(s): a system, the unassigned
  // "Resources" group, or nothing = show all. With multiple selected we show
  // the union of their resources.
  const visibleItems = useMemo(() => {
    const matchesNode = (i: CloudInfraStagedResource) => {
      if (!selectedSystemKeys.length) {
        return true;
      }
      return selectedSystemKeys.some((key) =>
        key === UNCATEGORIZED_SEGMENT
          ? getAssignedSystems(i.urn).length === 0
          : getAssignedSystems(i.urn).some((s) => String(s.value) === key),
      );
    };
    // A row stays if it still matches the selected node OR was just changed
    // (sticky) — so assigning a system never yanks the row out from under you.
    return data.items.filter((i) => matchesNode(i) || stickyUrns.has(i.urn));
  }, [data.items, selectedSystemKeys, getAssignedSystems, stickyUrns]);

  const total = visibleItems.length;
  const startIndex = (page - 1) * pageSize;
  const pageItems = visibleItems.slice(startIndex, startIndex + pageSize);

  // Filter option lists derived from the full mock dataset (not filtered set,
  // so the dropdowns always show every value).
  const locationOptions = useMemo(
    () =>
      Array.from(new Set(MOCK_AWS_RESOURCES.map((r) => r.location))).map(
        (loc) => ({ label: loc, value: loc }),
      ),
    [],
  );
  const serviceOptions = useMemo(
    () =>
      Array.from(new Set(MOCK_AWS_RESOURCES.map((r) => r.service))).map(
        (svc) => ({ label: getServiceLabel(svc), value: svc }),
      ),
    [],
  );

  const pageUrns = pageItems.map((i) => i.urn);
  const isAllSelected =
    pageUrns.length > 0 && pageUrns.every((urn) => selected.has(urn));
  const isIndeterminate =
    !isAllSelected && pageUrns.some((urn) => selected.has(urn));
  const selectedRowsCount = selected.size;

  const handleSelectOne = (urn: string, checked: boolean) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (checked) {
        next.add(urn);
      } else {
        next.delete(urn);
      }
      return next;
    });
  };

  const handleSelectAll = (checked: boolean) => {
    setSelected((prev) => {
      const next = new Set(prev);
      pageUrns.forEach((urn) => {
        if (checked) {
          next.add(urn);
        } else {
          next.delete(urn);
        }
      });
      return next;
    });
  };

  const clearSelection = () => setSelected(new Set());

  const selectedUrns = useMemo(() => Array.from(selected), [selected]);
  const selectedItems = useMemo(
    () => data.items.filter((i) => selected.has(i.urn)),
    [data.items, selected],
  );
  const someSelectedHaveSystem = selectedItems.some(
    (i) => getAssignedSystems(i.urn).length > 0,
  );
  const someSelectedMuted = selectedItems.some(
    (i) => i.diff_status === DiffStatus.MUTED,
  );

  const handleBulkAssignSystem = (system?: DefaultOptionType) => {
    if (!system) {
      return;
    }
    selectedUrns.forEach((urn) => addSystem(urn, system));
    markSticky(selectedUrns);
    messageApi.success(
      `Assigned ${system.label} to ${selectedUrns.length} resources`,
    );
  };

  const handleBulkApprove = () => {
    selectedUrns.forEach((urn) => {
      if (getAssignedSystems(urn).length > 0) {
        approve(urn);
      }
    });
    messageApi.success(
      `Approved ${someSelectedHaveSystem ? "selected" : 0} resources`,
    );
    clearSelection();
  };
  const handleBulkIgnore = () => {
    selectedUrns.forEach((urn) => ignore(urn));
    messageApi.info(`Ignored ${selectedUrns.length} resources`);
    clearSelection();
  };
  const handleBulkRestore = () => {
    selectedUrns.forEach((urn) => restore(urn));
    messageApi.info(`Restored ${selectedUrns.length} resources`);
    clearSelection();
  };
  const handleBulkRemoveSystems = () => {
    selectedUrns.forEach((urn) => clearSystems(urn));
    markSticky(selectedUrns);
    messageApi.info(`Removed systems from ${selectedUrns.length} resources`);
    clearSelection();
  };

  const actionMenuItems = [
    {
      key: "assign",
      label: "Assign system",
      icon: <Icons.Add />,
      onClick: () => setBulkAssignOpen(true),
    },
    {
      key: "approve",
      label: "Approve",
      icon: <Icons.Checkmark />,
      disabled: !someSelectedHaveSystem,
      onClick: handleBulkApprove,
    },
    {
      key: "remove-systems",
      label: "Remove systems",
      icon: <Icons.Close />,
      disabled: !someSelectedHaveSystem,
      onClick: handleBulkRemoveSystems,
    },
    someSelectedMuted
      ? {
          key: "restore",
          label: "Restore",
          icon: <Icons.View />,
          onClick: handleBulkRestore,
        }
      : {
          key: "ignore",
          label: "Ignore",
          icon: <Icons.ViewOff />,
          onClick: handleBulkIgnore,
        },
  ];

  return (
    <>
      <Splitter className="h-[calc(100%-48px)] overflow-hidden">
        <Splitter.Panel
          defaultSize={250}
          style={{ paddingRight: "var(--fidesui-padding-sm)" }}
        >
          <WebsiteAssetExplorerTree
            title="Resource explorer"
            nodes={treeNodes}
            selectedKeys={selectedSystemKeys}
            isLoading={isLoading}
            onSelectKeys={(keys) => {
              setSelectedSystemKeys(keys);
              setPage(1);
            }}
          />
        </Splitter.Panel>
        <Splitter.Panel
          style={{
            paddingLeft: "var(--fidesui-padding-md)",
            overflow: "hidden",
          }}
        >
          <Flex vertical gap="medium" className="h-full overflow-hidden">
            <Alert
              showIcon
              type="info"
              message="Review detected AWS resources"
              description="Fides detected the following resources in your AWS infrastructure. Assign one or more systems to each resource, then approve to add it to your inventory. Ignore resources that aren't relevant to your privacy needs."
            />
            <Flex justify="space-between" gap="medium" wrap="wrap">
              <Space.Compact>
                <DebouncedSearchInput
                  value={search.searchQuery ?? ""}
                  onChange={search.updateSearch}
                  placeholder="Search by name or ARN"
                />
                <RegexToggle
                  value={searchRegex}
                  onChange={(val) => setSearchRegex(!!val)}
                />
              </Space.Compact>
              <Flex gap="small" align="center" wrap="wrap">
                <Select
                  placeholder="Status"
                  options={STATUS_FILTER_OPTIONS}
                  value={filters.statusFilters ?? []}
                  onChange={(values: string[]) =>
                    filters.setStatusFilters(values)
                  }
                  mode="multiple"
                  allowClear
                  maxTagCount="responsive"
                  maxTagPlaceholder={renderTagPlaceholder}
                  className="w-40"
                  aria-label="Filter by status"
                />
                <Select
                  placeholder="Location"
                  options={locationOptions}
                  value={filters.locationFilters ?? []}
                  onChange={(values: string[]) =>
                    filters.setLocationFilters(values)
                  }
                  mode="multiple"
                  allowClear
                  maxTagCount="responsive"
                  maxTagPlaceholder={renderTagPlaceholder}
                  className="w-40"
                  aria-label="Filter by location"
                />
                <Select
                  placeholder="Service"
                  options={serviceOptions}
                  value={filters.serviceFilters ?? []}
                  onChange={(values: string[]) =>
                    filters.setServiceFilters(values)
                  }
                  mode="multiple"
                  allowClear
                  maxTagCount="responsive"
                  maxTagPlaceholder={renderTagPlaceholder}
                  className="w-40"
                  aria-label="Filter by service"
                />
                <Dropdown
                  menu={{ items: actionMenuItems }}
                  disabled={selectedRowsCount === 0}
                >
                  <Button
                    type="primary"
                    icon={<Icons.ChevronDown />}
                    iconPlacement="end"
                    disabled={selectedRowsCount === 0}
                  >
                    Actions
                  </Button>
                </Dropdown>
              </Flex>
            </Flex>
            <Flex gap="medium" align="center">
              <Checkbox
                checked={isAllSelected}
                indeterminate={isIndeterminate}
                onChange={(e) => handleSelectAll(e.target.checked)}
                title="Select all"
              >
                Select all
              </Checkbox>
              {selectedRowsCount > 0 && (
                <Text strong>
                  {selectedRowsCount.toLocaleString()} selected
                </Text>
              )}
            </Flex>
            <Flex flex={1} style={{ minHeight: 0, overflow: "hidden" }}>
              <List
                dataSource={pageItems}
                loading={isLoading}
                className="size-full overflow-y-auto overflow-x-clip"
                locale={{
                  emptyText: (
                    <Empty
                      image={Empty.PRESENTED_IMAGE_SIMPLE}
                      description="All caught up!"
                    />
                  ),
                }}
                renderItem={(item) => (
                  <MockCloudInfraResourceListItem
                    item={item}
                    selected={selected.has(item.urn)}
                    onSelect={handleSelectOne}
                    assignedSystems={getAssignedSystems(item.urn)}
                    onAddSystem={(urn, system) => {
                      addSystem(urn, system);
                      markSticky([urn]);
                      messageApi.success(
                        `Added ${system.label} to ${item.name ?? urn}`,
                      );
                    }}
                    onRemoveSystem={(urn, val) => {
                      removeSystem(urn, val);
                      markSticky([urn]);
                    }}
                    onApprove={(urn) => {
                      approve(urn);
                      messageApi.success(`Approved ${item.name ?? urn}`);
                    }}
                    onIgnore={(urn) => {
                      ignore(urn);
                      messageApi.info(`Ignored ${item.name ?? urn}`);
                    }}
                    onRestore={(urn) => {
                      restore(urn);
                      messageApi.info(`Restored ${item.name ?? urn}`);
                    }}
                    onOpenDetails={setDetailsResource}
                  />
                )}
              />
            </Flex>
            <Pagination
              current={page}
              pageSize={pageSize}
              pageSizeOptions={PAGE_SIZE_OPTIONS.map(String)}
              onChange={(p, size) => {
                setPage(p);
                if (size !== pageSize) {
                  setPageSize(size);
                }
              }}
              onShowSizeChange={(_, size) => {
                setPageSize(size);
                setPage(1);
              }}
              total={total}
              showSizeChanger={{
                suffixIcon: <Icons.ChevronDown />,
              }}
              hideOnSinglePage={pageSize === PAGE_SIZE_OPTIONS[0]}
            />
          </Flex>
        </Splitter.Panel>
      </Splitter>
      <MockCloudInfraResourceDetailsDrawer
        resource={detailsResource}
        open={!!detailsResource}
        onClose={() => setDetailsResource(null)}
        assignedSystems={
          detailsResource ? getAssignedSystems(detailsResource.urn) : []
        }
        onAddSystem={(urn, system) => {
          addSystem(urn, system);
          markSticky([urn]);
          messageApi.success(
            `Added ${system.label} to ${detailsResource?.name ?? urn}`,
          );
        }}
        onRemoveSystem={(urn, val) => {
          removeSystem(urn, val);
          markSticky([urn]);
        }}
        onApprove={(urn) => {
          approve(urn);
          messageApi.success(`Approved ${detailsResource?.name ?? urn}`);
        }}
        onIgnore={(urn) => {
          ignore(urn);
          messageApi.info(`Ignored ${detailsResource?.name ?? urn}`);
        }}
        onRestore={(urn) => {
          restore(urn);
          messageApi.info(`Restored ${detailsResource?.name ?? urn}`);
        }}
      />
      <MockAssignSystemModal
        isOpen={bulkAssignOpen}
        onClose={() => setBulkAssignOpen(false)}
        onSave={(system) => {
          handleBulkAssignSystem(system);
        }}
      />
    </>
  );
};
