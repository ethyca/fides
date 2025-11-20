import { useMemo, useState } from "react";

import { StagedResourceAPIResponse } from "~/types/api";

import { OKTA_APP_FILTER_TABS } from "../../constants/oktaAppFilters";
import { oktaStubClient } from "../utils/oktaStubClient";

interface UseOktaAppFiltersConfig {
  pageIndex: number;
  pageSize: number;
  searchQuery: string;
}

export const useOktaAppFilters = ({
  pageIndex,
  pageSize,
  searchQuery,
}: UseOktaAppFiltersConfig) => {
  const [activeTab, setActiveTab] = useState<string>("all");

  // Calculate counts for each Okta filter tab
  const filterCounts = useMemo(() => {
    const allMockApps = oktaStubClient.getAllMockApps();
    const counts: Record<string, number> = {};

    OKTA_APP_FILTER_TABS.forEach((tab) => {
      const filteredItems = allMockApps.filter((item) => {
        return tab.filter(item as StagedResourceAPIResponse);
      });
      counts[tab.value] = filteredItems.length;
    });

    return counts;
  }, []);

  // Use mock data for Okta apps and apply filters
  const mockData = useMemo(() => {
    const activeFilter = OKTA_APP_FILTER_TABS.find(
      (tab) => tab.value === activeTab,
    );
    const allMockApps = oktaStubClient.getAllMockApps();

    // Apply filter tab first
    let filteredItems = allMockApps.filter((item) => {
      return activeFilter?.filter(item as StagedResourceAPIResponse);
    });

    // Apply search if provided
    if (searchQuery) {
      const searchLower = searchQuery.toLowerCase();
      filteredItems = filteredItems.filter(
        (item) =>
          item.name?.toLowerCase().includes(searchLower) ??
          item.vendor_id?.toLowerCase().includes(searchLower),
      );
    }

    // Apply pagination
    const startIndex = (pageIndex - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    const paginatedItems = filteredItems.slice(startIndex, endIndex);

    return {
      items: paginatedItems,
      total: filteredItems.length,
      page: pageIndex,
      size: pageSize,
      pages: Math.ceil(filteredItems.length / pageSize),
    };
  }, [activeTab, pageIndex, pageSize, searchQuery]);

  // Convert Okta filter tabs to the same format as regular filter tabs
  const filterTabs = useMemo(
    () =>
      OKTA_APP_FILTER_TABS.map((tab) => ({
        label: `${tab.label} (${filterCounts[tab.value] || 0})`,
        hash: tab.value,
        params: {},
      })),
    [filterCounts],
  );

  const handleTabChange = async (tab: string) => {
    setActiveTab(tab);
  };

  return {
    filterTabs,
    activeTab,
    handleTabChange,
    filterCounts,
    mockData,
  };
};
