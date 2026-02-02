import { Button, DisplayValueType, Flex, Select, Tooltip } from "fidesui";
import { useEffect, useMemo } from "react";

import useTaxonomies from "~/features/common/hooks/useTaxonomies";
import {
  INFRASTRUCTURE_STATUS_FILTER_MAP,
  InfrastructureStatusFilterOptionValue,
  parseFiltersToFilterValue,
} from "~/features/data-discovery-and-detection/action-center/fields/utils";

import { useGetIdentityProviderMonitorFiltersQuery } from "../../discovery-detection.slice";
import { useInfrastructureSystemsFilters } from "../fields/useInfrastructureSystemsFilters";

interface InfrastructureSystemsFiltersProps
  extends ReturnType<typeof useInfrastructureSystemsFilters> {
  monitorId: string;
}

const STATUS_FILTER_OPTIONS = [
  {
    label: "New",
    value: InfrastructureStatusFilterOptionValue.NEW,
  },
  {
    label: "Known systems",
    value: InfrastructureStatusFilterOptionValue.KNOWN,
  },
  {
    label: "Unknown systems",
    value: InfrastructureStatusFilterOptionValue.UNKNOWN,
  },
  {
    label: "Ignored",
    value: InfrastructureStatusFilterOptionValue.IGNORED,
  },
];

export const InfrastructureSystemsFilters = ({
  monitorId,
  statusFilters,
  setStatusFilters,
  vendorFilters,
  setVendorFilters,
  dataUsesFilters,
  setDataUsesFilters,
  reset,
}: InfrastructureSystemsFiltersProps) => {
  const { getDataUseDisplayName } = useTaxonomies();

  // Fetch available filters from API
  const { data: availableFilters } = useGetIdentityProviderMonitorFiltersQuery(
    { monitor_config_key: monitorId },
    { skip: !monitorId },
  );

  // Map the actual filter values back to the dropdown option value
  const statusFilterValue = useMemo(
    () => parseFiltersToFilterValue(statusFilters, vendorFilters),
    [statusFilters, vendorFilters],
  );

  const dataUseOptions = useMemo(() => {
    if (!availableFilters?.data_uses) {
      return [];
    }
    return availableFilters.data_uses.map((dataUse) => ({
      label: getDataUseDisplayName(dataUse),
      value: dataUse,
    }));
  }, [availableFilters?.data_uses, getDataUseDisplayName]);

  const handleStatusChange = (value: string | undefined) => {
    const { diffStatusFilter, vendorIdFilter } =
      INFRASTRUCTURE_STATUS_FILTER_MAP[
        value as InfrastructureStatusFilterOptionValue
      ] ?? { diffStatusFilter: [], vendorIdFilter: [] };
    setStatusFilters(diffStatusFilter);
    setVendorFilters(vendorIdFilter);
  };

  const handleDataUseChange = (value: string[]) => {
    setDataUsesFilters(value.length > 0 ? value : []);
  };

  // Set initial value to "New" if no filters are set (only on mount)
  useEffect(() => {
    if (
      (!statusFilters || statusFilters.length === 0) &&
      (!vendorFilters || vendorFilters.length === 0)
    ) {
      handleStatusChange(InfrastructureStatusFilterOptionValue.NEW);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const hasActiveFilters =
    (statusFilters && statusFilters.length > 0) ||
    (vendorFilters && vendorFilters.length > 0) ||
    (dataUsesFilters && dataUsesFilters.length > 0);

  const renderTagPlaceholder = (omittedValues: DisplayValueType[]) => (
    <Tooltip
      title={
        <Flex vertical>
          {omittedValues.map(({ label, value }) => (
            <span key={value}>{label}</span>
          ))}
        </Flex>
      }
    >
      <span>+ {omittedValues.length}</span>
    </Tooltip>
  );

  return (
    <Flex gap="small" align="center">
      {hasActiveFilters && (
        <Button
          type="text"
          onClick={reset}
          data-testid="clear-filters-button"
          aria-label="Clear all filters"
        >
          Clear filters
        </Button>
      )}
      <Select
        placeholder="Status"
        options={STATUS_FILTER_OPTIONS}
        value={statusFilterValue}
        onChange={handleStatusChange}
        allowClear
        className="w-40"
        data-testid="status-filter-select"
        aria-label="Filter by status"
      />
      <Select
        placeholder="Data use"
        options={dataUseOptions}
        value={dataUsesFilters ?? []}
        onChange={handleDataUseChange}
        mode="multiple"
        allowClear
        maxTagCount="responsive"
        maxTagPlaceholder={renderTagPlaceholder}
        className="w-72"
        data-testid="data-use-filter-select"
        aria-label="Filter by data use"
      />
    </Flex>
  );
};
