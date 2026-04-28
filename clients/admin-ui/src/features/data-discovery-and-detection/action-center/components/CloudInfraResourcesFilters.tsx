import { DisplayValueType, Flex, Select, Tooltip } from "fidesui";
import { useMemo } from "react";

import { DiffStatus } from "~/types/api";

import { useGetCloudInfraMonitorFiltersQuery } from "../../discovery-detection.slice";
import { useCloudInfraFilters } from "../fields/useCloudInfraFilters";
import { getServiceLabel } from "../utils/cloudInfraServiceInfo";

interface CloudInfraResourcesFiltersProps extends ReturnType<
  typeof useCloudInfraFilters
> {
  monitorId: string;
}

const STATUS_FILTER_OPTIONS = [
  { label: "New", value: DiffStatus.ADDITION },
  { label: "Removed", value: DiffStatus.REMOVAL },
];

export const CloudInfraResourcesFilters = ({
  monitorId,
  statusFilters,
  setStatusFilters,
  locationFilters,
  setLocationFilters,
  serviceFilters,
  setServiceFilters,
  accountFilters,
  setAccountFilters,
}: CloudInfraResourcesFiltersProps) => {
  // Fetch available filters from API
  const { data: availableFilters } = useGetCloudInfraMonitorFiltersQuery(
    { monitor_config_id: monitorId },
    { skip: !monitorId },
  );

  const locationOptions = useMemo(() => {
    if (!availableFilters?.location) {
      return [];
    }
    return availableFilters.location.map((loc) => ({
      label: loc,
      value: loc,
    }));
  }, [availableFilters?.location]);

  const serviceOptions = useMemo(() => {
    if (!availableFilters?.service) {
      return [];
    }
    return availableFilters.service.map((svc) => ({
      label: getServiceLabel(svc),
      value: svc,
    }));
  }, [availableFilters?.service]);

  const accountOptions = useMemo(() => {
    if (!availableFilters?.cloud_account_id) {
      return [];
    }
    return availableFilters.cloud_account_id.map((acct) => ({
      label: acct,
      value: acct,
    }));
  }, [availableFilters?.cloud_account_id]);

  const handleStatusChange = (values: string[]) => {
    setStatusFilters(values.length > 0 ? values : []);
  };

  const handleLocationChange = (values: string[]) => {
    setLocationFilters(values.length > 0 ? values : []);
  };

  const handleServiceChange = (values: string[]) => {
    setServiceFilters(values.length > 0 ? values : []);
  };

  const handleAccountChange = (values: string[]) => {
    setAccountFilters(values.length > 0 ? values : []);
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
    <Flex gap="small" align="center" wrap="wrap">
      <Select
        placeholder="Status"
        options={STATUS_FILTER_OPTIONS}
        value={statusFilters ?? []}
        onChange={handleStatusChange}
        mode="multiple"
        allowClear
        maxTagCount="responsive"
        maxTagPlaceholder={renderTagPlaceholder}
        className="w-40"
        data-testid="status-filter-select"
        aria-label="Filter by status"
      />
      <Select
        placeholder="Location"
        options={locationOptions}
        value={locationFilters ?? []}
        onChange={handleLocationChange}
        mode="multiple"
        allowClear
        maxTagCount="responsive"
        maxTagPlaceholder={renderTagPlaceholder}
        className="w-40"
        data-testid="location-filter-select"
        aria-label="Filter by location"
      />
      <Select
        placeholder="Service"
        options={serviceOptions}
        value={serviceFilters ?? []}
        onChange={handleServiceChange}
        mode="multiple"
        allowClear
        maxTagCount="responsive"
        maxTagPlaceholder={renderTagPlaceholder}
        className="w-40"
        data-testid="service-filter-select"
        aria-label="Filter by service"
      />
      <Select
        placeholder="Account ID"
        options={accountOptions}
        value={accountFilters ?? []}
        onChange={handleAccountChange}
        mode="multiple"
        allowClear
        maxTagCount="responsive"
        maxTagPlaceholder={renderTagPlaceholder}
        className="w-48"
        data-testid="account-filter-select"
        aria-label="Filter by account ID"
      />
    </Flex>
  );
};
