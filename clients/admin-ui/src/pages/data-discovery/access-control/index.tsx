import { DatePicker, Flex, Switch, Typography } from "fidesui";
import type { NextPage } from "next";
import { useMemo } from "react";

import {
  useGetConsumersByViolationsQuery,
  useGetFiltersQuery,
} from "~/features/access-control/access-control.slice";
import { AccessControlTableTabs } from "~/features/access-control/AccessControlTableTabs";
import {
  type FacetDefinition,
  FacetedSearchInput,
} from "~/features/access-control/request-log/FacetedSearchInput";
import {
  RequestLogFilterContext,
  useRequestLogFilters,
} from "~/features/access-control/request-log/useRequestLogFilters";
import { SummaryCards } from "~/features/access-control/summary/SummaryCards";
import type { FiltersResponse } from "~/features/access-control/types";
import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";

const FACET_CONFIG: {
  responseKey: keyof FiltersResponse;
  facetKey: string;
  label: string;
}[] = [
  { responseKey: "consumers", facetKey: "consumer", label: "Consumer" },
  { responseKey: "policies", facetKey: "policy", label: "Policy" },
  { responseKey: "datasets", facetKey: "dataset", label: "Dataset" },
  { responseKey: "data_uses", facetKey: "data_use", label: "Data use" },
  { responseKey: "controls", facetKey: "control", label: "Control" },
];

const AccessControlPage: NextPage = () => {
  const filterState = useRequestLogFilters();
  const {
    filters,
    dateRange,
    setDateRange,
    searchValues,
    setSearchValues,
    liveTail,
    setLiveTail,
  } = filterState;

  const { data: facetOptions } = useGetFiltersQuery(filters);

  const { data: consumersData, isLoading: consumersLoading } =
    useGetConsumersByViolationsQuery({
      ...filters,
      order_by: "violation_count",
    });

  const facets: FacetDefinition[] = useMemo(
    () =>
      FACET_CONFIG.map(({ responseKey, facetKey, label }) => {
        const raw = facetOptions?.[responseKey] ?? [];
        const hasEmpty = raw.some((v) => !v);
        const options = raw.filter(Boolean) as string[];
        if (hasEmpty) {
          options.push("");
        }
        return { key: facetKey, label, options };
      }),
    [facetOptions],
  );

  return (
    <Layout title="Access control">
      <PageHeader heading="Access control" isSticky />
      <RequestLogFilterContext.Provider value={filterState}>
        <div className="px-6">
          <Flex vertical gap={16}>
            <Flex gap={12} align="center">
              <div className="flex-1">
                <FacetedSearchInput
                  facets={facets}
                  value={searchValues}
                  onChange={setSearchValues}
                />
              </div>
              <DatePicker.RangePicker
                format="YYYY-MM-DD"
                value={dateRange}
                onChange={(dates) => {
                  if (dates && dates[0] && dates[1]) {
                    setDateRange([dates[0], dates[1]]);
                  } else {
                    setDateRange(null);
                  }
                }}
                placeholder={["From", "To"]}
                allowClear
                disabled={liveTail}
                aria-label="Date range"
                className="w-60"
              />
              <Flex align="center" gap={8}>
                <Switch
                  size="small"
                  checked={liveTail}
                  onChange={setLiveTail}
                />
                <Typography.Text
                  className={liveTail ? "text-green-600" : "text-gray-500"}
                >
                  Live tail
                </Typography.Text>
              </Flex>
            </Flex>

            <SummaryCards
              consumersData={consumersData}
              loading={consumersLoading}
            />

            <AccessControlTableTabs />
          </Flex>
        </div>
      </RequestLogFilterContext.Provider>
    </Layout>
  );
};

export default AccessControlPage;
