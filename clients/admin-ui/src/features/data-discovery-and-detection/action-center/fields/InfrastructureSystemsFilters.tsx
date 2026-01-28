import { Button, DisplayValueType, Flex, Select, Tooltip } from "fidesui";
import { useMemo } from "react";

import useTaxonomies from "~/features/common/hooks/useTaxonomies";
import { DiffStatus } from "~/types/api";

import { useGetIdentityProviderMonitorFiltersQuery } from "../../discovery-detection.slice";
import {
  INFRASTRUCTURE_DIFF_STATUS_LABEL,
  VENDOR_FILTER_OPTIONS,
} from "../constants";
import { useInfrastructureSystemsFilters } from "./useInfrastructureSystemsFilters";

interface InfrastructureSystemsFiltersProps
  extends ReturnType<typeof useInfrastructureSystemsFilters> {
  monitorId: string;
}

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

  const statusFilterValue = useMemo(() => {
    if (!statusFilters || statusFilters.length === 0) {
      return undefined;
    }
    return statusFilters[0];
  }, [statusFilters]);

  const statusOptions = useMemo(() => {
    if (!availableFilters?.diff_status) {
      return [];
    }
    return availableFilters.diff_status.map((status) => ({
      label: INFRASTRUCTURE_DIFF_STATUS_LABEL[status as DiffStatus] ?? status,
      value: status,
    }));
  }, [availableFilters?.diff_status]);

  const typeFilterValue = useMemo(() => {
    if (!vendorFilters || vendorFilters.length === 0) {
      return undefined;
    }
    return vendorFilters[0];
  }, [vendorFilters]);

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
    if (value) {
      setStatusFilters([value]);
    } else {
      setStatusFilters([]);
    }
  };

  const handleTypeChange = (value: string | undefined) => {
    if (value) {
      setVendorFilters([value]);
    } else {
      setVendorFilters([]);
    }
  };

  const handleDataUseChange = (value: string[]) => {
    setDataUsesFilters(value.length > 0 ? value : []);
  };

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
        options={statusOptions}
        value={statusFilterValue}
        onChange={handleStatusChange}
        allowClear
        className="w-40"
        data-testid="status-filter-select"
        aria-label="Filter by status"
      />

      <Select
        placeholder="Type"
        options={VENDOR_FILTER_OPTIONS.map((option) => ({
          label: option.label,
          value: option.key,
        }))}
        value={typeFilterValue}
        onChange={handleTypeChange}
        allowClear
        className="w-40"
        data-testid="type-filter-select"
        aria-label="Filter by type"
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
