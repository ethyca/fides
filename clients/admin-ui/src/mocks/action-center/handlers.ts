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
  ];
};
