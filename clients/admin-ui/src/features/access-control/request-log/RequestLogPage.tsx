import dayjs from "dayjs";
import { DatePicker, Flex } from "fidesui";
import { useRouter } from "next/router";
import { useCallback, useMemo, useState } from "react";

import {
  LOG_CONSUMERS,
  LOG_DATA_USES,
  LOG_DATASETS,
  POLICIES,
} from "~/mocks/access-control/data";

import { useGetDataConsumerRequestsQuery } from "../access-control.slice";
import {
  type FacetDefinition,
  FacetedSearchInput,
  SEPARATOR,
} from "./FacetedSearchInput";
import { RequestLogTable } from "./RequestLogTable";
import { ViolationsBarChartCard } from "./ViolationsBarChartCard";

const FACETS: FacetDefinition[] = [
  { key: "consumer", label: "Consumer", options: LOG_CONSUMERS },
  { key: "policy", label: "Policy", options: POLICIES },
  { key: "dataset", label: "Dataset", options: LOG_DATASETS },
  { key: "data_use", label: "Data use", options: LOG_DATA_USES },
];

const getDefaultDateRange = (): [dayjs.Dayjs, dayjs.Dayjs] => {
  return [dayjs().subtract(7, "day"), dayjs()];
};

const RequestLogPage = () => {
  const router = useRouter();
  const policyParam =
    typeof router.query.policy === "string" ? router.query.policy : null;

  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>(
    getDefaultDateRange,
  );
  const [searchValues, setSearchValues] = useState<string[]>(() =>
    policyParam ? [`policy${SEPARATOR}${policyParam}`] : [],
  );

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

  const filters = useMemo(() => {
    const result: Record<string, string | undefined> = {
      ...dateParams,
    };
    searchValues.forEach((val) => {
      const [key, value] = val.split(SEPARATOR);
      if (key && value) {
        result[key] = value;
      }
    });
    return result;
  }, [searchValues, dateParams]);

  const { data: chartData, isLoading: chartLoading } =
    useGetDataConsumerRequestsQuery(dateParams);

  const handleDateRangeChange = useCallback(
    (dates: [dayjs.Dayjs | null, dayjs.Dayjs | null] | null) => {
      if (dates && dates[0] && dates[1]) {
        setDateRange([dates[0], dates[1]]);
      } else {
        setDateRange(null);
      }
    },
    [],
  );

  return (
    <div className="flex flex-col gap-4">
      <Flex gap={12} align="center">
        <div className="flex-1">
          <FacetedSearchInput
            facets={FACETS}
            value={searchValues}
            onChange={setSearchValues}
          />
        </div>
        <DatePicker.RangePicker
          format="YYYY-MM-DD"
          value={dateRange}
          onChange={handleDateRangeChange}
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

      <RequestLogTable filters={filters} />
    </div>
  );
};

export { RequestLogPage };
