import { Button, DisplayValueType, Flex, Select, Tooltip } from "fidesui";
import { useMemo } from "react";

import useTaxonomies from "~/features/common/hooks/useTaxonomies";
import {
  INFRASTRUCTURE_STATUS_FILTER_MAP,
  InfrastructureStatusFilterOptionValue,
  parseFiltersToFilterValue,
} from "~/features/data-discovery-and-detection/action-center/fields/utils";
import { DiffStatus } from "~/types/api";

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
}: InfrastructureSystemsFiltersProps) => {
  const { getDataUseDisplayName } = useTaxonomies();

  // Fetch available filters from API
  const { data: availableFilters } = useGetIdentityProviderMonitorFiltersQuery(
    { monitor_config_key: monitorId },
    { skip: !monitorId },
  );

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

  const handleResetFilters = () => {
    setStatusFilters([DiffStatus.ADDITION]);
    setVendorFilters([]);
    setDataUsesFilters([]);
  };

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
      {statusFilterValue !== InfrastructureStatusFilterOptionValue.NEW && (
        <Button
          type="text"
          onClick={handleResetFilters}
          data-testid="reset-filters-button"
          aria-label="Reset filters to default"
        >
          Reset filters
        </Button>
      )}
      <Select
        placeholder="Status"
        options={STATUS_FILTER_OPTIONS}
        value={statusFilterValue}
        onChange={handleStatusChange}
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
