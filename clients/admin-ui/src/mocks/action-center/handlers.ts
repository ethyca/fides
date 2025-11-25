/* eslint-disable import/no-extraneous-dependencies */
import { rest } from "msw";

import { mockOktaApp, mockOktaMonitor } from "./data";

/**
 * MSW handlers for discovery monitor aggregate results
 */
export const discoveryMonitorHandlers = () => {
  const apiBase = "/api/v1";

  return [
    // GET - return mock Okta monitor
    rest.get(
      `${apiBase}/plus/discovery-monitor/aggregate-results`,
      (_req, res, ctx) =>
        res(
          ctx.status(200),
          ctx.json({
            items: [mockOktaMonitor],
            total: 1,
            page: 1,
            size: 25,
            pages: 1,
          }),
        ),
    ),
    // GET - return mock Okta app assets for system aggregate results
    rest.get(
      `${apiBase}/plus/discovery-monitor/system-aggregate-results`,
      (_req, res, ctx) =>
        res(
          ctx.status(200),
          ctx.json({
            items: [mockOktaApp],
            total: 10,
            page: 1,
            size: 25,
            pages: 1,
          }),
        ),
    ),
    // GET - Identity Provider Monitors (Okta) - list all monitors
    rest.get(`${apiBase}/plus/identity-provider-monitors`, (_req, res, ctx) => {
      const page = parseInt(_req.url.searchParams.get("page") || "1", 10);
      const size = parseInt(_req.url.searchParams.get("size") || "50", 10);

      return res(
        ctx.status(200),
        ctx.json({
          items: [mockOktaMonitor],
          total: 1,
          page,
          size,
          pages: 1,
        }),
      );
    }),
    // GET - Identity Provider Monitor Results (Okta) - get results for a monitor
    rest.get(
      `${apiBase}/plus/identity-provider-monitors/:monitor_config_key/results`,
      (_req, res, ctx) => {
        // const { monitor_config_key } = _req.params;
        const page = parseInt(_req.url.searchParams.get("page") || "1", 10);
        const size = parseInt(_req.url.searchParams.get("size") || "50", 10);
        const search = _req.url.searchParams.get("search");

        // Apply search filter if provided
        let filteredItems = [mockOktaApp];
        if (search) {
          const searchLower = search.toLowerCase();
          filteredItems = filteredItems.filter(
            (item) =>
              item.name?.toLowerCase().includes(searchLower) ||
              item.vendor_id?.toLowerCase().includes(searchLower),
          );
        }

        // Apply pagination
        const startIndex = (page - 1) * size;
        const endIndex = startIndex + size;
        const paginatedItems = filteredItems.slice(startIndex, endIndex);

        return res(
          ctx.status(200),
          ctx.json({
            items: paginatedItems,
            total: filteredItems.length,
            page,
            size,
            pages: Math.ceil(filteredItems.length / size),
          }),
        );
      },
    ),
    // POST - Create Identity Provider Monitor (Okta)
    rest.post(
      `${apiBase}/plus/identity-provider-monitors`,
      (_req, res, ctx) => {
        return res(
          ctx.status(200),
          ctx.json({
            ...mockOktaMonitor,
            ...(_req.body as Record<string, unknown>),
          }),
        );
      },
    ),
    // POST - Execute Identity Provider Monitor (Okta)
    rest.post(
      `${apiBase}/plus/identity-provider-monitors/:monitor_config_key/execute`,
      (_req, res, ctx) => {
        return res(
          ctx.status(200),
          ctx.json({
            monitor_execution_id: "550e8400-e29b-41d4-a716-446655440000",
            task_id: null,
          }),
        );
      },
    ),
  ];
};
