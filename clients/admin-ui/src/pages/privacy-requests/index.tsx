import dayjs from "dayjs";
import { DatePicker, LocationSelect, Select, Space } from "fidesui";
import type { NextPage } from "next";
import { useCallback, useEffect, useMemo } from "react";

import { DebouncedSearchInput } from "~/features/common/DebouncedSearchInput";
import { useFeatures } from "~/features/common/features";
import FixedLayout from "~/features/common/FixedLayout";
import { useAntPagination } from "~/features/common/pagination/useAntPagination";
import Restrict from "~/features/common/Restrict";
import { SidePanel } from "~/features/common/SidePanel";
import { ManualTasks } from "~/features/manual-tasks/ManualTasks";
import ActionButtons from "~/features/privacy-requests/buttons/ActionButtons";
import {
  SubjectRequestActionTypeOptions,
  SubjectRequestStatusOptions,
} from "~/features/privacy-requests/constants";
import { CustomFieldFilter } from "~/features/privacy-requests/dashboard/CustomFieldFilter";
import usePrivacyRequestsFilters from "~/features/privacy-requests/dashboard/hooks/usePrivacyRequestsFilters";
import { PrivacyRequestsDashboard } from "~/features/privacy-requests/dashboard/PrivacyRequestsDashboard";
import PrivacyRequestSortMenu from "~/features/privacy-requests/dashboard/PrivacyRequestSortMenu";
import { extractUniqueCustomFields } from "~/features/privacy-requests/dashboard/utils";
import { useDSRErrorAlert } from "~/features/privacy-requests/hooks/useDSRErrorAlert";
import {
  PRIVACY_REQUEST_TABS,
  usePrivacyRequestTabs,
} from "~/features/privacy-requests/hooks/usePrivacyRequestTabs";
import { useGetPrivacyCenterConfigQuery } from "~/features/privacy-requests/privacy-requests.slice";
import SubmitPrivacyRequest from "~/features/privacy-requests/SubmitPrivacyRequest";
import { ActionType, PrivacyRequestStatus, ScopeRegistryEnum } from "~/types/api";

const PrivacyRequests: NextPage = () => {
  const { processing } = useDSRErrorAlert();
  const { plus: hasPlus } = useFeatures();
  const { activeTab, handleTabChange, availableTabs } = usePrivacyRequestTabs();

  // Lift filter and pagination state to the page level
  const pagination = useAntPagination();
  const filterState = usePrivacyRequestsFilters({ pagination });
  const { filters, setFilters, sortState, setSortState } = filterState;

  // Custom fields for dynamic filters
  const { data: privacyCenterConfig } = useGetPrivacyCenterConfigQuery();
  const uniqueCustomFields = useMemo(
    () => extractUniqueCustomFields(privacyCenterConfig?.actions),
    [privacyCenterConfig?.actions],
  );

  // Count active filters for the badge
  const activeFilterCount = useMemo(() => {
    let count = 0;
    if (filters.search) count += 1;
    if (filters.from || filters.to) count += 1;
    if (filters.status && filters.status.length > 0) count += 1;
    if (filters.action_type && filters.action_type.length > 0) count += 1;
    if (filters.location) count += 1;
    if (filters.custom_privacy_request_fields) {
      count += Object.values(filters.custom_privacy_request_fields).filter(
        (v) => v !== null,
      ).length;
    }
    return count;
  }, [filters]);

  const handleClearAllFilters = useCallback(() => {
    setFilters({
      search: null,
      from: null,
      to: null,
      status: null,
      action_type: null,
      location: null,
      custom_privacy_request_fields: null,
    });
  }, [setFilters]);

  // Date range helpers
  const dateRangeValue: [dayjs.Dayjs, dayjs.Dayjs] | null = useMemo(() => {
    if (filters.from && filters.to) {
      return [dayjs(filters.from), dayjs(filters.to)];
    }
    return null;
  }, [filters.from, filters.to]);

  const handleDateRangeChange = useCallback(
    (dates: [dayjs.Dayjs | null, dayjs.Dayjs | null] | null) => {
      const [from, to] = dates || [null, null];
      setFilters({
        from: from?.format("YYYY-MM-DD") ?? null,
        to: to?.format("YYYY-MM-DD") ?? null,
      });
    },
    [setFilters],
  );

  const handleStatusChange = useCallback(
    (value: PrivacyRequestStatus[]) => {
      setFilters({ status: value.length > 0 ? value : null });
    },
    [setFilters],
  );

  const handleActionTypeChange = useCallback(
    (value: ActionType[]) => {
      setFilters({ action_type: value.length > 0 ? value : null });
    },
    [setFilters],
  );

  const handleLocationChange = useCallback(
    (value: string | null | undefined) => {
      setFilters({ location: value ?? null });
    },
    [setFilters],
  );

  const handleCustomFieldChange = useCallback(
    (fieldName: string, value: string | null) => {
      const currentCustomFields = filters.custom_privacy_request_fields || {};
      const updatedCustomFields = {
        ...currentCustomFields,
        [fieldName]: value,
      };
      const cleanedFields = Object.fromEntries(
        Object.entries(updatedCustomFields).filter(([, v]) => v !== null),
      );
      setFilters({
        custom_privacy_request_fields:
          Object.keys(cleanedFields).length > 0 ? cleanedFields : null,
      });
    },
    [filters.custom_privacy_request_fields, setFilters],
  );

  useEffect(() => {
    processing();
  }, [processing]);

  const isRequestTab = activeTab === PRIVACY_REQUEST_TABS.REQUEST;

  const tabItems = useMemo(() => {
    const items: Array<{
      key: string;
      label: string;
      children: React.ReactNode;
    }> = [];

    if (availableTabs.request) {
      items.push({
        key: PRIVACY_REQUEST_TABS.REQUEST,
        label: "Request",
        children: (
          <PrivacyRequestsDashboard
            pagination={pagination}
            filterState={filterState}
          />
        ),
      });
    }

    if (availableTabs.manualTask) {
      items.push({
        key: PRIVACY_REQUEST_TABS.MANUAL_TASK,
        label: "Manual tasks",
        children: <ManualTasks />,
      });
    }

    return items;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [availableTabs.manualTask, availableTabs.request, filterState]);

  return (
    <>
      <SidePanel>
        <SidePanel.Identity
          title="Privacy requests"
          breadcrumbItems={[{ title: "All requests" }]}
        />
        <SidePanel.Navigation
          items={tabItems.map((t) => ({ key: t.key, label: t.label }))}
          activeKey={activeTab}
          onSelect={handleTabChange}
        />
        <SidePanel.Actions>
          <Space>
            {hasPlus && (
              <Restrict scopes={[ScopeRegistryEnum.PRIVACY_REQUEST_CREATE]}>
                <SubmitPrivacyRequest />
              </Restrict>
            )}
            <ActionButtons />
          </Space>
        </SidePanel.Actions>
        {isRequestTab && (
          <SidePanel.Filters
            activeCount={activeFilterCount}
            onClearAll={handleClearAllFilters}
          >
            <DebouncedSearchInput
              placeholder="Request ID or identity value"
              value={filters.search || ""}
              onChange={(value) => setFilters({ search: value || null })}
              data-testid="privacy-request-search"
            />
            <DatePicker.RangePicker
              format="YYYY-MM-DD"
              value={dateRangeValue}
              onChange={handleDateRangeChange}
              placeholder={["From", "To"]}
              allowClear
              data-testid="date-range-filter"
              aria-label="Date range"
            />
            <Select
              mode="multiple"
              placeholder="Status"
              options={SubjectRequestStatusOptions}
              value={filters.status || []}
              onChange={handleStatusChange}
              allowClear
              maxTagCount="responsive"
              data-testid="request-status-filter"
              aria-label="Status"
            />
            <Select
              mode="multiple"
              placeholder="Request type"
              options={SubjectRequestActionTypeOptions}
              value={filters.action_type || []}
              onChange={handleActionTypeChange}
              allowClear
              maxTagCount="responsive"
              data-testid="request-action-type-filter"
              aria-label="Request type"
            />
            <LocationSelect
              placeholder="Location"
              value={filters.location || null}
              onChange={handleLocationChange}
              allowClear
              data-testid="request-location-filter"
              aria-label="Location"
              popupMatchSelectWidth={300}
              includeCountryOnlyOptions
            />
            {Object.entries(uniqueCustomFields).map(
              ([fieldName, fieldDefinition]) => (
                <CustomFieldFilter
                  key={fieldName}
                  fieldName={fieldName}
                  fieldDefinition={fieldDefinition}
                  value={
                    filters.custom_privacy_request_fields?.[fieldName] ?? null
                  }
                  onChange={(value) => handleCustomFieldChange(fieldName, value)}
                />
              ),
            )}
            <PrivacyRequestSortMenu
              sortState={sortState}
              setSortState={setSortState}
            />
          </SidePanel.Filters>
        )}
      </SidePanel>
      <FixedLayout
        title="Privacy requests"
        mainProps={{ minWidth: "784px", overflowY: "scroll" }}
        fullHeight
      >
        {tabItems.find((t) => t.key === activeTab)?.children}
      </FixedLayout>
    </>
  );
};
export default PrivacyRequests;
