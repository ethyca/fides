import { DatePicker, Flex, Result } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import type { NextPage } from "next";
import { useCallback, useMemo } from "react";
import { useQueryState, parseAsStringLiteral } from "nuqs";

import { useGetFiltersQuery } from "~/features/access-control/access-control.slice";
import { AccessControlTableTabs } from "~/features/access-control/AccessControlTableTabs";
import { MOCK_UNRESOLVED_IDENTITIES } from "~/features/access-control/mockData";
import { UnresolvedBanner } from "~/features/access-control/SummaryCards";
import {
  type FacetDefinition,
  FacetedSearchInput,
} from "~/features/access-control/FacetedSearchInput";
import {
  RequestLogFilterContext,
  useRequestLogFilters,
} from "~/features/access-control/hooks/useRequestLogFilters";
import { PendingActionsCard } from "~/features/access-control/PendingActionsCard";
import type { FiltersResponse } from "~/features/access-control/types";
import { ViolationsChartCard } from "~/features/access-control/ViolationsChartCard";
import { useFeatures } from "~/features/common/features";
import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";

const FACET_LABELS: Record<
  keyof FiltersResponse,
  { key: string; label: string }
> = {
  consumers: { key: "consumer", label: "Consumer" },
  policies: { key: "policy", label: "Policy" },
  datasets: { key: "dataset", label: "Dataset" },
  data_uses: { key: "data_use", label: "Data use" },
  controls: { key: "control", label: "Control" },
};

const AccessControlPage: NextPage = () => {
  const { flags } = useFeatures();
  const filterState = useRequestLogFilters();
  const { filters, dateRange, setDateRange, searchValues, setSearchValues } =
    filterState;

  const { data: facetOptions } = useGetFiltersQuery(filters, {
    skip: !flags.alphaPurposeBasedAccessControl,
  });

  const facets: FacetDefinition[] = useMemo(() => {
    if (!facetOptions) {
      return [];
    }
    return (Object.keys(FACET_LABELS) as (keyof FiltersResponse)[])
      .filter((responseKey) => facetOptions[responseKey]?.length > 0)
      .map((responseKey) => {
        const { key, label } = FACET_LABELS[responseKey];
        const raw = facetOptions[responseKey];
        const hasEmpty = raw.some((v) => !v);
        const options = raw.filter(Boolean) as string[];
        if (hasEmpty) {
          options.push("");
        }
        return { key, label, options };
      });
  }, [facetOptions]);

  const [, setTab] = useQueryState(
    "tab",
    parseAsStringLiteral(["summary", "log", "consumers"] as const)
      .withDefault("summary")
      .withOptions({ history: "push" }),
  );

  const handleReviewIdentities = useCallback(() => {
    setTab("consumers");
  }, [setTab]);

  if (!flags.alphaPurposeBasedAccessControl) {
    return (
      <Layout title="Access control">
        <Result status="error" title="Access control feature is not enabled" />
      </Layout>
    );
  }

  return (
    <Layout title="Access control">
      <PageHeader heading="Access control" isSticky />
      <RequestLogFilterContext.Provider value={filterState}>
        <Flex vertical gap={16}>
          <UnresolvedBanner
            unresolvedCount={MOCK_UNRESOLVED_IDENTITIES.length}
            onReviewIdentities={handleReviewIdentities}
          />
          <Flex gap={12} align="center">
            <Flex flex={1}>
              <FacetedSearchInput
                facets={facets}
                value={searchValues}
                onChange={setSearchValues}
              />
            </Flex>
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
              aria-label="Date range"
              className="w-60"
            />
          </Flex>

          <Flex gap={32} className="px-4 py-6">
            <div className="min-w-0 flex-1">
              <ViolationsChartCard />
            </div>
            <div
              className="shrink-0 border-l border-solid"
              style={{ borderColor: palette.FIDESUI_NEUTRAL_100 }}
            />
            <div style={{ width: 260, flexShrink: 0 }}>
              <PendingActionsCard />
            </div>
          </Flex>

          <AccessControlTableTabs />
        </Flex>
      </RequestLogFilterContext.Provider>
    </Layout>
  );
};

export default AccessControlPage;
