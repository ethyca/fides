/* eslint-disable import/no-extraneous-dependencies */
import { rest } from "msw";

import {
  aggregateLogsToTimeseries,
  allViolationLogs,
  buildSummaryFromLogs,
  dataConsumersByViolationsData,
  filterLogs,
  LOG_CONSUMERS,
  LOG_CONTROLS,
  LOG_DATA_USES,
  LOG_DATASETS,
  POLICIES,
  policyViolationsData,
} from "./data";

const DEFAULT_START = new Date(Date.now() - 7 * 86_400_000).toISOString();
const DEFAULT_END = new Date().toISOString();

const getParam = (url: URL, key: string): string | string[] | null => {
  const values = url.searchParams.getAll(key);
  if (values.length === 0) {
    return null;
  }
  return values.length === 1 ? values[0] : values;
};

const getFilters = (url: URL) => ({
  consumer: getParam(url, "consumer"),
  policy: getParam(url, "policy"),
  dataset: getParam(url, "dataset"),
  data_use: getParam(url, "data_use"),
  control: getParam(url, "control"),
  start_date: url.searchParams.get("start_date"),
  end_date: url.searchParams.get("end_date"),
});

export const accessControlHandlers = () => {
  const apiBase = "/api/v1";

  return [
    rest.get(`${apiBase}/access-control/summary`, (req, res, ctx) => {
      const filters = getFilters(req.url);
      const startDate = filters.start_date ?? DEFAULT_START;
      const endDate = filters.end_date ?? DEFAULT_END;
      const filtered = filterLogs(allViolationLogs, {
        ...filters,
        start_date: startDate,
        end_date: endDate,
      });

      return res(
        ctx.status(200),
        ctx.json(buildSummaryFromLogs(filtered, startDate, endDate)),
      );
    }),

    rest.get(`${apiBase}/access-control/requests`, (req, res, ctx) => {
      const filters = getFilters(req.url);
      const startDate = filters.start_date ?? DEFAULT_START;
      const endDate = filters.end_date ?? DEFAULT_END;
      const filtered = filterLogs(allViolationLogs, {
        ...filters,
        start_date: startDate,
        end_date: endDate,
      });

      return res(
        ctx.status(200),
        ctx.json(aggregateLogsToTimeseries(filtered, startDate, endDate)),
      );
    }),

    rest.get(`${apiBase}/access-control/consumers`, (req, res, ctx) => {
      const orderBy = req.url.searchParams.get("order_by") || "violation_count";
      const sorted = [...dataConsumersByViolationsData].sort((a, b) =>
        orderBy === "request_count"
          ? b.requests - a.requests
          : b.violations - a.violations,
      );
      return res(ctx.status(200), ctx.json({ items: sorted }));
    }),

    rest.get(`${apiBase}/access-control/violations/logs`, (req, res, ctx) => {
      const cursor = req.url.searchParams.get("cursor");
      const size = parseInt(req.url.searchParams.get("size") ?? "25", 10);

      const filters = getFilters(req.url);
      const filtered = filterLogs(allViolationLogs, filters);

      let startIdx = 0;
      if (cursor) {
        const cursorIdx = filtered.findIndex((l) => l.id === cursor);
        startIdx = cursorIdx >= 0 ? cursorIdx + 1 : 0;
      }

      const items = filtered.slice(startIdx, startIdx + size);
      const nextCursor =
        startIdx + size < filtered.length
          ? (items[items.length - 1]?.id ?? null)
          : null;

      return res(
        ctx.status(200),
        ctx.json({
          items,
          next_cursor: nextCursor,
          size,
        }),
      );
    }),

    rest.get(`${apiBase}/access-control/violations`, (req, res, ctx) => {
      const page = parseInt(req.url.searchParams.get("page") ?? "1", 10);
      const size = parseInt(req.url.searchParams.get("size") ?? "10", 10);
      const start = (page - 1) * size;
      const items = policyViolationsData.slice(start, start + size);

      return res(
        ctx.status(200),
        ctx.json({
          items,
          total: policyViolationsData.length,
          page,
          size,
          pages: Math.ceil(policyViolationsData.length / size),
        }),
      );
    }),

    rest.get(`${apiBase}/access-control/violations/:id`, (req, res, ctx) => {
      const log = allViolationLogs.find((l) => l.id === req.params.id);
      if (!log) {
        return res(ctx.status(404), ctx.json({ detail: "Not found" }));
      }
      return res(ctx.status(200), ctx.json(log));
    }),

    rest.get(`${apiBase}/access-control/filters`, (req, res, ctx) => {
      const filters = getFilters(req.url);
      const filtered = filterLogs(allViolationLogs, filters);

      const consumers = [...new Set(filtered.map((l) => l.consumer))].sort();
      const policies = [
        ...new Set(filtered.map((l) => l.policy).filter(Boolean)),
      ].sort() as string[];
      const datasets = [...new Set(filtered.map((l) => l.dataset))].sort();
      const dataUses = [
        ...new Set(filtered.map((l) => l.data_use).filter(Boolean)),
      ].sort() as string[];
      const controls = [
        ...new Set(filtered.map((l) => l.control).filter(Boolean)),
      ].sort() as string[];

      return res(
        ctx.status(200),
        ctx.json({
          consumers: filters.consumer ? consumers : LOG_CONSUMERS,
          policies: filters.policy ? policies : POLICIES,
          datasets: filters.dataset ? datasets : LOG_DATASETS,
          data_uses: filters.data_use ? dataUses : LOG_DATA_USES,
          controls: filters.control ? controls : LOG_CONTROLS,
        }),
      );
    }),
  ];
};
