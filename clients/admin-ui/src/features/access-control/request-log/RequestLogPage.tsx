import dayjs from "dayjs";
import { DatePicker, Flex, Switch, Typography } from "fidesui";
import { useRouter } from "next/router";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import type { PolicyViolationLog } from "../types";

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
  const [liveTail, setLiveTail] = useState(false);
  const [liveTailItems, setLiveTailItems] = useState<PolicyViolationLog[]>([]);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const dateParams = useMemo(() => {
    if (liveTail) {
      return {
        start_date: dayjs().subtract(12, "hour").toISOString(),
        end_date: dayjs().toISOString(),
      };
    }
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
  }, [dateRange, liveTail]);

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

  const generateMockItems = useCallback((): PolicyViolationLog[] => {
    const consumers = ["Analytics Service", "ML Pipeline", "Reporting API", "Data Export", "BI Dashboard"];
    const policies = ["Restrict PII Access", "Data Minimization", "Purpose Limitation", "Consent Required"];
    const datasets = ["postgres.users", "postgres.orders", "snowflake.events", "bigquery.analytics"];
    const dataUses = ["marketing", "analytics", "ml_training", "third_party_sharing"];
    const pick = <T,>(arr: T[]): T => arr[Math.floor(Math.random() * arr.length)];
    const count = Math.floor(Math.random() * 6) + 1;

    return Array.from({ length: count }, (_, i) => ({
      id: `live-${Date.now()}-${i}`,
      timestamp: dayjs().toISOString(),
      consumer: pick(consumers),
      consumer_email: `service-${Math.floor(Math.random() * 100)}@example.com`,
      policy: pick(policies),
      policy_description: "Auto-generated violation during live tail",
      dataset: pick(datasets),
      data_use: pick(dataUses),
      sql_statement: `SELECT * FROM ${pick(["users", "orders", "events"])} WHERE id = ${Math.floor(Math.random() * 1000)}`,
    }));
  }, []);

  useEffect(() => {
    if (liveTail) {
      intervalRef.current = setInterval(() => {
        setLiveTailItems((prev) => [...generateMockItems(), ...prev]);
      }, 2000);
    } else {
      setLiveTailItems([]);
    }
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [liveTail, generateMockItems]);

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

      <ViolationsBarChartCard
        data={chartData?.items ?? []}
        totalViolations={chartData?.violations ?? 0}
        loading={chartLoading}
      />

      <RequestLogTable
        filters={filters}
        liveTailItems={liveTailItems}
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
