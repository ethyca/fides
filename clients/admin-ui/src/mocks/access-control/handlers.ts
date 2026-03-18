/* eslint-disable import/no-extraneous-dependencies */
import { rest } from "msw";

import {
  dataConsumersByViolationsData,
  generateChartData,
  policyViolationsData,
} from "./data";

const DEFAULT_START = new Date(Date.now() - 7 * 86_400_000).toISOString();
const DEFAULT_END = new Date().toISOString();

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
            violations: sorted.reduce(
              (sum, consumer) => sum + consumer.violations,
              0,
            ),
            total_requests: sorted.reduce(
              (sum, consumer) => sum + consumer.requests,
              0,
            ),
            active_consumers: sorted.length,
            items: sorted,
          }),
        );
      }

      const startDate =
        req.url.searchParams.get("start_date") ?? DEFAULT_START;
      const endDate = req.url.searchParams.get("end_date") ?? DEFAULT_END;

      return res(
        ctx.status(200),
        ctx.json(generateChartData(startDate, endDate)),
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
  ];
};
