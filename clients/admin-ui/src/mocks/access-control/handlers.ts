/* eslint-disable import/no-extraneous-dependencies */
import { rest } from "msw";

import type { TimeRange } from "~/features/access-control/types";

import {
  dataConsumerRequestsData,
  dataConsumersByViolationsData,
  policyViolationLogsData,
  policyViolationsData,
} from "./data";

const TIME_RANGE_KEYS: Record<string, TimeRange> = {
  "1": "24h",
  "7": "7d",
  "30": "30d",
};

const inferTimeRange = (
  startDate: string | null,
  endDate: string | null,
): TimeRange => {
  if (!startDate || !endDate) {
    return "7d";
  }
  const diffDays = Math.round(
    (new Date(endDate).getTime() - new Date(startDate).getTime()) /
      (1000 * 60 * 60 * 24),
  );
  return TIME_RANGE_KEYS[String(diffDays)] ?? "7d";
};

export const accessControlHandlers = () => {
  const apiBase = "/api/v1";

  return [
    rest.get(`${apiBase}/data-consumer/requests`, (req, res, ctx) => {
      const groupBy = req.url.searchParams.get("group_by");

      if (groupBy === "consumer") {
        const orderBy =
          req.url.searchParams.get("order_by") || "violation_count";
        const sorted = [...dataConsumersByViolationsData].sort((a, b) =>
          orderBy === "request_count"
            ? b.requests - a.requests
            : b.violations - a.violations,
        );
        return res(
          ctx.status(200),
          ctx.json({
            violations: sorted.reduce((sum, consumer) => sum + consumer.violations, 0),
            total_requests: sorted.reduce((sum, consumer) => sum + consumer.requests, 0),
            active_consumers: sorted.length,
            items: sorted,
          }),
        );
      }

      const timeRange = inferTimeRange(
        req.url.searchParams.get("start_date"),
        req.url.searchParams.get("end_date"),
      );
      return res(
        ctx.status(200),
        ctx.json(dataConsumerRequestsData[timeRange]),
      );
    }),

    rest.get(`${apiBase}/policy/violations`, (req, res, ctx) => {
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

    rest.get(`${apiBase}/policy/violations/logs`, (req, res, ctx) => {
      const page = parseInt(req.url.searchParams.get("page") ?? "1", 10);
      const size = parseInt(req.url.searchParams.get("size") ?? "25", 10);
      const start = (page - 1) * size;
      const items = policyViolationLogsData.slice(start, start + size);

      return res(
        ctx.status(200),
        ctx.json({
          items,
          total: policyViolationLogsData.length,
          page,
          size,
          pages: Math.ceil(policyViolationLogsData.length / size),
        }),
      );
    }),
  ];
};
