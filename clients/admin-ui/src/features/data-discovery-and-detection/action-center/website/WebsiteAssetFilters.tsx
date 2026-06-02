import { formatIsoLocation, isoStringToEntry } from "fidesui";
import { useMemo } from "react";

import { FilterSelect } from "~/features/common/dropdown/FilterSelect";
import { PRIVACY_NOTICE_REGION_RECORD } from "~/features/common/privacy-notice-regions";
import { ConsentStatus, DiffStatus, PrivacyNoticeRegion } from "~/types/api";

import { useGetWebsiteMonitorResourceFiltersQuery } from "../action-center.slice";
import { DiscoveryStatusDisplayNames } from "../constants";
import isConsentCategory from "../utils/isConsentCategory";

interface DiscoveredAssetsFilterValues {
  resource_type?: string[];
  data_uses?: string[];
  locations?: string[];
  consent_aggregated?: string[];
}

interface WebsiteAssetFiltersProps {
  monitorId: string;
  resolvedSystemId: string;
  diffStatus?: DiffStatus[];
  search?: string;
  value: DiscoveredAssetsFilterValues;
  onChange: (next: DiscoveredAssetsFilterValues) => void;
  showComplianceFilter?: boolean;
}

const toOptions = (
  values: string[] | undefined | null,
  getLabel: (value: string) => string = (v) => v,
) => (values ?? []).map((value) => ({ label: getLabel(value), value }));

const formatLocation = (location: string): string => {
  const isoEntry = isoStringToEntry(location);
  return isoEntry
    ? formatIsoLocation({ isoEntry })
    : (PRIVACY_NOTICE_REGION_RECORD[location as PrivacyNoticeRegion] ??
        location);
};

const WebsiteAssetFilters = ({
  monitorId,
  resolvedSystemId,
  diffStatus,
  search,
  value,
  onChange,
  showComplianceFilter,
}: WebsiteAssetFiltersProps) => {
  const { data: filterOptions } = useGetWebsiteMonitorResourceFiltersQuery({
    monitor_config_id: monitorId,
    resolved_system_id: resolvedSystemId,
    diff_status: diffStatus,
    search,
    ...value,
  });

  const typeOptions = useMemo(
    () => toOptions(filterOptions?.resource_type),
    [filterOptions?.resource_type],
  );
  const consentCategoryOptions = useMemo(
    () => toOptions(filterOptions?.data_uses?.filter(isConsentCategory)),
    [filterOptions?.data_uses],
  );
  const locationOptions = useMemo(
    () => toOptions(filterOptions?.locations, formatLocation),
    [filterOptions?.locations],
  );
  const complianceOptions = useMemo(
    () =>
      toOptions(
        filterOptions?.consent_aggregated,
        (status) =>
          DiscoveryStatusDisplayNames[status as ConsentStatus] ?? status,
      ),
    [filterOptions?.consent_aggregated],
  );

  const update = (key: keyof DiscoveredAssetsFilterValues, next: string[]) =>
    onChange({ ...value, [key]: next.length ? next : undefined });

  return (
    <>
      <FilterSelect
        mode="multiple"
        placeholder="Type"
        options={typeOptions}
        value={value.resource_type ?? []}
        onChange={(next) => update("resource_type", next as string[])}
        className="w-40"
        data-testid="filter-type"
      />
      <FilterSelect
        mode="multiple"
        placeholder="Categories of consent"
        options={consentCategoryOptions}
        value={value.data_uses ?? []}
        onChange={(next) => update("data_uses", next as string[])}
        className="w-56"
        data-testid="filter-consent-category"
      />
      <FilterSelect
        mode="multiple"
        placeholder="Location"
        options={locationOptions}
        value={value.locations ?? []}
        onChange={(next) => update("locations", next as string[])}
        className="w-44"
        data-testid="filter-location"
      />
      {showComplianceFilter && (
        <FilterSelect
          mode="multiple"
          placeholder="Compliance"
          options={complianceOptions}
          value={value.consent_aggregated ?? []}
          onChange={(next) => update("consent_aggregated", next as string[])}
          className="w-44"
          data-testid="filter-compliance"
        />
      )}
    </>
  );
};

export default WebsiteAssetFilters;
