import { Empty, Flex, Icons, List, Pagination, Space } from "fidesui";
import { useMemo } from "react";

import { DebouncedSearchInput } from "~/features/common/DebouncedSearchInput";
import { DiffStatus } from "~/types/api";

import { CloudInfraResourceListItem } from "../components/CloudInfraResourceListItem";
import { CloudInfraResourcesFilters } from "../components/CloudInfraResourcesFilters";
import { useCloudInfraFilters } from "../fields/useCloudInfraFilters";
import RegexToggle from "../forms/RegexToggle";
import { useCloudInfraMonitorResultsTable } from "../hooks/useCloudInfraMonitorResultsTable";

const DEFAULT_STATUS_FILTERS = [DiffStatus.ADDITION, DiffStatus.REMOVAL];

interface CloudInfraResourcesTableProps {
  monitorId: string;
  showIgnored?: boolean;
  showApproved?: boolean;
}

export const CloudInfraResourcesTable = ({
  monitorId,
  showIgnored = false,
  showApproved = false,
}: CloudInfraResourcesTableProps) => {
  const cloudInfraFilters = useCloudInfraFilters();

  // Build status filters combining the filter dropdown with page settings toggles.
  // The dropdown controls which primary statuses to show (addition, removal).
  // The toggles always add ignored/approved on top.
  const effectiveStatusFilters = useMemo(() => {
    const filters = cloudInfraFilters.statusFilters;
    const statuses = new Set<string>(
      filters && filters.length > 0 ? filters : DEFAULT_STATUS_FILTERS,
    );
    if (showIgnored) {
      statuses.add(DiffStatus.MUTED);
    }
    if (showApproved) {
      statuses.add(DiffStatus.MONITORED);
    }
    return Array.from(statuses);
  }, [cloudInfraFilters.statusFilters, showIgnored, showApproved]);

  const {
    data,
    isLoading,
    searchQuery,
    updateSearch,
    searchRegex,
    setSearchRegex,
    paginationProps,
  } = useCloudInfraMonitorResultsTable({
    monitorId,
    statusFilters: effectiveStatusFilters,
    locationFilters: cloudInfraFilters.locationFilters,
    serviceFilters: cloudInfraFilters.serviceFilters,
    accountFilters: cloudInfraFilters.accountFilters,
  });

  return (
    <Flex vertical gap="medium" className="h-full overflow-hidden">
      <Flex justify="space-between" gap="medium" wrap="wrap">
        <Space.Compact>
          <DebouncedSearchInput
            value={searchQuery}
            onChange={updateSearch}
            placeholder="Search by name or URN"
          />
          <RegexToggle
            value={searchRegex}
            onChange={(val) => setSearchRegex(!!val)}
          />
        </Space.Compact>
        <Flex gap="small" wrap="wrap">
          <CloudInfraResourcesFilters
            monitorId={monitorId}
            {...cloudInfraFilters}
          />
        </Flex>
      </Flex>
      <Flex flex={1} style={{ minHeight: 0, overflow: "hidden" }}>
        <List
          dataSource={data?.items}
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
          renderItem={(item) => <CloudInfraResourceListItem item={item} />}
        />
      </Flex>
      <Pagination
        {...paginationProps}
        total={data?.total || 0}
        showSizeChanger={{
          suffixIcon: <Icons.ChevronDown />,
        }}
        hideOnSinglePage={
          paginationProps.pageSize?.toString() ===
          paginationProps.pageSizeOptions?.[0]
        }
      />
    </Flex>
  );
};
