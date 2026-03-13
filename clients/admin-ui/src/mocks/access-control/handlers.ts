/* eslint-disable import/no-extraneous-dependencies */
import { rest } from "msw";

import {
  dataConsumersByViolationsData,
  generateChartData,
  generateLiveLogs,
  policyViolationsData,
} from "./data";

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
            items: sorted,
          }),
        );
      }

      const startDate = req.url.searchParams.get("start_date");
      const endDate = req.url.searchParams.get("end_date");

      return res(
        ctx.status(200),
        ctx.json(
          generateChartData(
            startDate ?? new Date(Date.now() - 7 * 86_400_000).toISOString(),
            endDate ?? new Date().toISOString(),
          ),
        ),
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

      const consumer = req.url.searchParams.get("consumer");
      const policy = req.url.searchParams.get("policy");
      const dataset = req.url.searchParams.get("dataset");
      const dataUse = req.url.searchParams.get("data_use");

      const allLogs = generateLiveLogs(200);
      const filtered = allLogs.filter((log) => {
        if (consumer && log.consumer !== consumer) {
          return false;
        }
        if (policy && log.policy !== policy) {
          return false;
        }
        if (dataset && log.dataset !== dataset) {
          return false;
        }
        if (dataUse && log.data_use !== dataUse) {
          return false;
        }
        return true;
      });

      const start = (page - 1) * size;
      const items = filtered.slice(start, start + size);

      return res(
        ctx.status(200),
        ctx.json({
          items,
          total: filtered.length,
          page,
          size,
          pages: Math.ceil(filtered.length / size),
        }),
      );
    }),
  ];
};
