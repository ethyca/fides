import dayjs from "dayjs";
import { DatePicker, Flex } from "fidesui";
import { useRouter } from "next/router";
import { useMemo, useState } from "react";

import {
  useGetDataConsumerRequestsQuery,
  useGetFacetOptionsQuery,
} from "../access-control.slice";
import {
  type FacetDefinition,
  FacetedSearchInput,
  SEPARATOR,
} from "./FacetedSearchInput";
import { RequestLogTable } from "./RequestLogTable";
import { ViolationDetailDrawer } from "./ViolationDetailDrawer";
import { ViolationsBarChartCard } from "./ViolationsBarChartCard";

type FacetKey = "consumer" | "policy" | "dataset" | "data_use";

export const RequestLogPage = () => {
  const router = useRouter();
  const policyParam =
    typeof router.query.policy === "string" ? router.query.policy : null;

  const { data: facetOptions } = useGetFacetOptionsQuery();

  const facets: FacetDefinition[] = useMemo(
    () => [
      {
        key: "consumer",
        label: "Consumer",
        options: facetOptions?.consumers ?? [],
      },
      { key: "policy", label: "Policy", options: facetOptions?.policies ?? [] },
      {
        key: "dataset",
        label: "Dataset",
        options: facetOptions?.datasets ?? [],
      },
      {
        key: "data_use",
        label: "Data use",
        options: facetOptions?.data_uses ?? [],
      },
    ],
    [facetOptions],
  );

  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>(
    () => [dayjs().subtract(7, "day"), dayjs()],
  );
  const [searchValues, setSearchValues] = useState<string[]>(() =>
    policyParam ? [`policy${SEPARATOR}${policyParam}`] : [],
  );
  const [selectedViolationId, setSelectedViolationId] = useState<string | null>(
    null,
  );
  const [drawerOpen, setDrawerOpen] = useState(false);

  const dateParams = useMemo(() => {
    if (!dateRange) {
      return {
        start_date: dayjs().subtract(1, "day").toISOString(),
        end_date: dayjs().toISOString(),
      };
    }
    return {
      start_date: dateRange[0].toISOString(),
      end_date: dateRange[1].toISOString(),
    };
  }, [dateRange]);

  const facetFilters = useMemo(() => {
    const result: Partial<Record<FacetKey, string | string[]>> = {};
    searchValues.forEach((val) => {
      const [key, value] = val.split(SEPARATOR);
      if (key && value) {
        const facetKey = key as FacetKey;
        const existing = result[facetKey];
        if (Array.isArray(existing)) {
          existing.push(value);
        } else if (typeof existing === "string") {
          result[facetKey] = [existing, value];
        } else {
          result[facetKey] = value;
        }
      }
    });
    return result;
  }, [searchValues]);

  const filters = useMemo(
    () => ({ ...dateParams, ...facetFilters }),
    [dateParams, facetFilters],
  );

  const { data: chartData, isLoading: chartLoading } =
    useGetDataConsumerRequestsQuery(filters);

  return (
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
          aria-label="Date range"
          className="w-60"
        />
      </Flex>

      <ViolationsBarChartCard
        data={chartData?.items ?? []}
        totalViolations={chartData?.violations ?? 0}
        loading={chartLoading}
      />

      <RequestLogTable
        filters={filters}
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
  );
};
