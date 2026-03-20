import { DatePicker, Flex, Switch, Typography } from "fidesui";
import { useMemo, useState } from "react";

import { useGetFiltersQuery } from "../access-control.slice";
import type { FiltersResponse } from "../types";
import { type FacetDefinition, FacetedSearchInput } from "./FacetedSearchInput";
import { RequestLogTable } from "./RequestLogTable";

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
import {
  RequestLogFilterContext,
  useRequestLogFilters,
} from "./useRequestLogFilters";
import { ViolationDetailDrawer } from "./ViolationDetailDrawer";
import { ViolationsBarChartCard } from "./ViolationsBarChartCard";

export const RequestLogPage = () => {
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

  const [selectedViolationId, setSelectedViolationId] = useState<string | null>(
    null,
  );
  const [drawerOpen, setDrawerOpen] = useState(false);

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
    <RequestLogFilterContext.Provider value={filterState}>
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
            <Switch size="small" checked={liveTail} onChange={setLiveTail} />
            <Typography.Text
              className={liveTail ? "text-green-600" : "text-gray-500"}
            >
              Live tail
            </Typography.Text>
          </Flex>
        </Flex>

        <ViolationsBarChartCard />

        <RequestLogTable
          onRowClick={(record) => {
            setSelectedViolationId(record.id);
            setDrawerOpen(true);
          }}
        />

        <ViolationDetailDrawer
          violationId={selectedViolationId}
          open={drawerOpen}
          onClose={() => setDrawerOpen(false)}
        />
      </Flex>
    </RequestLogFilterContext.Provider>
  );
};
