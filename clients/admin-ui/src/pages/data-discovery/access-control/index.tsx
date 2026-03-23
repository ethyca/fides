import { Col, DatePicker, Flex, Row } from "fidesui";
import type { NextPage } from "next";
import { useMemo } from "react";

import { useGetFiltersQuery } from "~/features/access-control/access-control.slice";
import { AccessControlTableTabs } from "~/features/access-control/AccessControlTableTabs";
import {
  type FacetDefinition,
  FacetedSearchInput,
} from "~/features/access-control/FacetedSearchInput";
import { DataConsumersCard } from "~/features/access-control/DataConsumersCard";
import {
  RequestLogFilterContext,
  useRequestLogFilters,
} from "~/features/access-control/hooks/useRequestLogFilters";
import type { FiltersResponse } from "~/features/access-control/types";
import { ViolationRateCard } from "~/features/access-control/ViolationRateCard";
import { ViolationsChartCard } from "~/features/access-control/ViolationsChartCard";
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
  const { filters, dateRange, setDateRange, searchValues, setSearchValues } =
    filterState;

  const { data: facetOptions } = useGetFiltersQuery(filters);

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
        <Flex vertical gap={16}>
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

          <Row gutter={16}>
            <Col span={14}>
              <ViolationsChartCard />
            </Col>
            <Col span={5}>
              <ViolationRateCard />
            </Col>
            <Col span={5}>
              <DataConsumersCard />
            </Col>
          </Row>

          <AccessControlTableTabs />
        </Flex>
      </RequestLogFilterContext.Provider>
    </Layout>
  );
};

export default AccessControlPage;
