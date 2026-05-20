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
  Tooltip,
  Typography,
  useMessage,
} from "fidesui";
import { useMemo, useState } from "react";

import { DebouncedSearchInput } from "~/features/common/DebouncedSearchInput";
import { useSearch } from "~/features/common/hooks";
import { DiffStatus } from "~/types/api";
import { CloudInfraStagedResource } from "~/types/api/models/CloudInfraStagedResource";

import { AssignSystemModal } from "../AssignSystemModal";
import { MockCloudInfraResourceDetailsDrawer } from "../components/MockCloudInfraResourceDetailsDrawer";
import { MockCloudInfraResourceListItem } from "../components/MockCloudInfraResourceListItem";
import { useCloudInfraFilters } from "../fields/useCloudInfraFilters";
import RegexToggle from "../forms/RegexToggle";
import { useMockCloudInfraResources } from "../hooks/useMockCloudInfraResources";
import { MOCK_AWS_RESOURCES } from "../mock/awsCloudInfraMock";
import { getServiceLabel } from "../utils/cloudInfraServiceInfo";

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
    approve,
    ignore,
    restore,
  } = useMockCloudInfraResources({
    statusFilters: effectiveStatusFilters,
    locationFilters: filters.locationFilters,
    serviceFilters: filters.serviceFilters,
    accountFilters: filters.accountFilters,
    search: search.searchQuery ?? "",
    searchRegex,
  });

  const { total } = data;
  const startIndex = (page - 1) * pageSize;
  const pageItems = data.items.slice(startIndex, startIndex + pageSize);

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
  const accountOptions = useMemo(
    () =>
      Array.from(
        new Set(MOCK_AWS_RESOURCES.map((r) => r.cloud_account_id)),
      ).map((acct) => ({ label: acct, value: acct })),
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
    <Flex vertical gap="medium" className="h-full overflow-hidden">
      <Alert
        showIcon
        type="info"
        message="Review detected AWS resources"
        description="Fides detected the following resources in your AWS infrastructure. Assign one or more systems to each resource, then approve to add it to your inventory. Ignore resources that aren't relevant to your privacy program."
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
            onChange={(values: string[]) => filters.setStatusFilters(values)}
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
            onChange={(values: string[]) => filters.setLocationFilters(values)}
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
            onChange={(values: string[]) => filters.setServiceFilters(values)}
            mode="multiple"
            allowClear
            maxTagCount="responsive"
            maxTagPlaceholder={renderTagPlaceholder}
            className="w-40"
            aria-label="Filter by service"
          />
          <Select
            placeholder="Account ID"
            options={accountOptions}
            value={filters.accountFilters ?? []}
            onChange={(values: string[]) => filters.setAccountFilters(values)}
            mode="multiple"
            allowClear
            maxTagCount="responsive"
            maxTagPlaceholder={renderTagPlaceholder}
            className="w-48"
            aria-label="Filter by account ID"
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
          <Text strong>{selectedRowsCount.toLocaleString()} selected</Text>
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
                messageApi.success(
                  `Added ${system.label} to ${item.name ?? urn}`,
                );
              }}
              onRemoveSystem={removeSystem}
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
      <MockCloudInfraResourceDetailsDrawer
        resource={detailsResource}
        open={!!detailsResource}
        onClose={() => setDetailsResource(null)}
        assignedSystems={
          detailsResource ? getAssignedSystems(detailsResource.urn) : []
        }
        onAddSystem={(urn, system) => {
          addSystem(urn, system);
          messageApi.success(
            `Added ${system.label} to ${detailsResource?.name ?? urn}`,
          );
        }}
        onRemoveSystem={removeSystem}
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
      <AssignSystemModal
        isOpen={bulkAssignOpen}
        onClose={() => setBulkAssignOpen(false)}
        onSave={(system) => {
          handleBulkAssignSystem(system);
        }}
      />
    </Flex>
  );
};
