import { Empty, Flex, Icons, List, Pagination, Space } from "fidesui";
import { useMemo } from "react";

import { DebouncedSearchInput } from "~/features/common/DebouncedSearchInput";
import ErrorPage from "~/features/common/errors/ErrorPage";
import { DiffStatus } from "~/types/api";

import { CloudInfraResourceListItem } from "../components/CloudInfraResourceListItem";
import { CloudInfraResourcesFilters } from "../components/CloudInfraResourcesFilters";
import { useCloudInfraFilters } from "../fields/useCloudInfraFilters";
import RegexToggle from "../forms/RegexToggle";
import { useCloudInfraMonitorResultsTable } from "../hooks/useCloudInfraMonitorResultsTable";
import { MOCK_AWS_MONITOR_KEY } from "../mock/awsCloudInfraMock";
import { MockCloudInfraResourcesTable } from "./MockCloudInfraResourcesTable";

const DEFAULT_STATUS_FILTERS = [DiffStatus.ADDITION, DiffStatus.REMOVAL];

interface CloudInfraResourcesTableProps {
  monitorId: string;
  showIgnored?: boolean;
  showApproved?: boolean;
}

const RealCloudInfraResourcesTable = ({
  monitorId,
  showIgnored,
  showApproved,
}: Required<CloudInfraResourcesTableProps>) => {
  const cloudInfraFilters = useCloudInfraFilters();

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
    error,
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

  if (error) {
    return (
      <ErrorPage
        error={error}
        defaultMessage="A problem occurred while fetching cloud infrastructure resources"
      />
    );
  }

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
        hideOnSinglePage
      />
    </Flex>
  );
};

export const CloudInfraResourcesTable = ({
  monitorId,
  showIgnored = false,
  showApproved = false,
}: CloudInfraResourcesTableProps) => {
  if (monitorId === MOCK_AWS_MONITOR_KEY) {
    return (
      <MockCloudInfraResourcesTable
        showIgnored={showIgnored}
        showApproved={showApproved}
      />
    );
  }
  return (
    <RealCloudInfraResourcesTable
      monitorId={monitorId}
      showIgnored={showIgnored}
      showApproved={showApproved}
    />
  );
};
