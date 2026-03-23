import dayjs from "dayjs";
import type { ChartDataRequest } from "fidesui";
import { useRouter } from "next/router";
import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
} from "react";

import { SEPARATOR } from "../FacetedSearchInput";

type FacetKey = "consumer" | "policy" | "dataset" | "data_use" | "control";

export interface RequestLogFilters {
  start_date: string;
  end_date: string;
  consumer?: string | string[];
  policy?: string | string[];
  dataset?: string | string[];
  data_use?: string | string[];
  control?: string | string[];
}

export interface TimeseriesFilters extends RequestLogFilters {
  interval?: number;
}

export interface RequestLogFilterState {
  filters: RequestLogFilters;
  timeseriesFilters: TimeseriesFilters;
  dateRange: [dayjs.Dayjs, dayjs.Dayjs] | null;
  setDateRange: (range: [dayjs.Dayjs, dayjs.Dayjs] | null) => void;
  searchValues: string[];
  setSearchValues: (values: string[]) => void;
  liveTail: boolean;
  setLiveTail: (value: boolean) => void;
  onChartIntervalChange: (request: ChartDataRequest) => void;
  applyFacets: (facets: Record<string, string>) => void;
}

export const RequestLogFilterContext =
  createContext<RequestLogFilterState | null>(null);

export const useRequestLogFilterContext = (): RequestLogFilterState => {
  const ctx = useContext(RequestLogFilterContext);
  if (!ctx) {
    throw new Error(
      "useRequestLogFilterContext must be used within a RequestLogFilterContext.Provider",
    );
  }
  return ctx;
};

export const useRequestLogFilters = (): RequestLogFilterState => {
  const router = useRouter();

  const [dateRange, setDateRange] = useState<
    [dayjs.Dayjs, dayjs.Dayjs] | null
  >(() => [dayjs().subtract(7, "day"), dayjs()]);

  const [searchValues, setSearchValues] = useState<string[]>(() => {
    const initial: string[] = [];
    for (const key of ["policy", "control"] as const) {
      const val = router.query[key];
      if (typeof val === "string" && val) {
        initial.push(`${key}${SEPARATOR}${val}`);
      }
    }
    return initial;
  });

  const [liveTail, setLiveTail] = useState(false);
  const [intervalHours, setIntervalHours] = useState<number | undefined>();

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

  const filters: RequestLogFilters = useMemo(
    () => ({ ...dateParams, ...facetFilters }),
    [dateParams, facetFilters],
  );

  const timeseriesFilters: TimeseriesFilters = useMemo(
    () => ({
      ...filters,
      ...(intervalHours != null ? { interval: intervalHours } : {}),
    }),
    [filters, intervalHours],
  );

  const onChartIntervalChange = useCallback((request: ChartDataRequest) => {
    setIntervalHours(request.interval);
  }, []);

  const applyFacets = useCallback(
    (facets: Record<string, string>) => {
      const encoded = Object.entries(facets).map(
        ([key, value]) => `${key}${SEPARATOR}${value}`,
      );
      setSearchValues(encoded);
    },
    [setSearchValues],
  );

  return {
    filters,
    timeseriesFilters,
    dateRange,
    setDateRange,
    searchValues,
    setSearchValues,
    liveTail,
    setLiveTail,
    onChartIntervalChange,
    applyFacets,
  };
};
