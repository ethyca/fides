import { Button, DisplayValueType, Flex, Select, Tooltip } from "fidesui";
import { useEffect, useMemo } from "react";

import useTaxonomies from "~/features/common/hooks/useTaxonomies";
import { DiffStatus } from "~/types/api/models/DiffStatus";

import { useGetIdentityProviderMonitorFiltersQuery } from "../../discovery-detection.slice";
import { useInfrastructureSystemsFilters } from "./useInfrastructureSystemsFilters";

interface InfrastructureSystemsFiltersProps
  extends ReturnType<typeof useInfrastructureSystemsFilters> {
  monitorId: string;
}

enum StatusFilterOptionValue {
  NEW = "new",
  KNOWN = "known",
  UNKNOWN = "unknown",
  IGNORED = "ignored",
}

const STATUS_FILTER_OPTIONS = [
  { label: "New", value: StatusFilterOptionValue.NEW },
  { label: "Known systems", value: StatusFilterOptionValue.KNOWN },
  { label: "Unknown systems", value: StatusFilterOptionValue.UNKNOWN },
  { label: "Ignored", value: StatusFilterOptionValue.IGNORED },
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
  const statusFilterValue = useMemo(() => {
    const hasAdditionStatus =
      statusFilters &&
      statusFilters.length > 0 &&
      statusFilters[0] === DiffStatus.ADDITION;
    const hasMutedStatus =
      statusFilters &&
      statusFilters.length > 0 &&
      statusFilters[0] === DiffStatus.MUTED;
    const hasKnownVendor =
      vendorFilters && vendorFilters.length > 0 && vendorFilters[0] === "known";
    const hasUnknownVendor =
      vendorFilters &&
      vendorFilters.length > 0 &&
      vendorFilters[0] === "unknown";

    if (hasAdditionStatus && hasKnownVendor) {
      return StatusFilterOptionValue.KNOWN;
    }
    if (hasAdditionStatus && hasUnknownVendor) {
      return StatusFilterOptionValue.UNKNOWN;
    }
    if (hasAdditionStatus && !hasKnownVendor && !hasUnknownVendor) {
      return StatusFilterOptionValue.NEW;
    }
    if (hasMutedStatus) {
      return StatusFilterOptionValue.IGNORED;
    }
    return undefined;
  }, [statusFilters, vendorFilters]);

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
    if (!value) {
      setStatusFilters([]);
      setVendorFilters([]);
      return;
    }

    switch (value) {
      case StatusFilterOptionValue.NEW:
        setStatusFilters([DiffStatus.ADDITION]);
        setVendorFilters([]);
        break;
      case StatusFilterOptionValue.KNOWN:
        setStatusFilters([DiffStatus.ADDITION]);
        setVendorFilters(["known"]);
        break;
      case StatusFilterOptionValue.UNKNOWN:
        setStatusFilters([DiffStatus.ADDITION]);
        setVendorFilters(["unknown"]);
        break;
      case StatusFilterOptionValue.IGNORED:
        setStatusFilters([DiffStatus.MUTED]);
        setVendorFilters([]);
        break;
      default:
        setStatusFilters([]);
        setVendorFilters([]);
    }
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
      setStatusFilters([DiffStatus.ADDITION]);
      setVendorFilters([]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Only run on mount to set initial default

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
