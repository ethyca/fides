/* eslint-disable import/no-extraneous-dependencies */
import { rest } from "msw";

import { mockPolicies } from "./data";

/**
 * MSW handlers for DSR policy endpoints
 */
export const policyHandlers = () => {
  const apiBase = "/api/v1";

  return [
    // GET /api/v1/dsr/policy - list all policies
    rest.get(`${apiBase}/dsr/policy`, (req, res, ctx) => {
      const page = parseInt(req.url.searchParams.get("page") ?? "1", 10);
      const size = parseInt(req.url.searchParams.get("size") ?? "50", 10);

      const start = (page - 1) * size;
      const end = start + size;
      const paginatedItems = mockPolicies.slice(start, end);

      return res(
        ctx.status(200),
        ctx.json({
          items: paginatedItems,
          total: mockPolicies.length,
          page,
          size,
          pages: Math.ceil(mockPolicies.length / size),
        }),
      );
    }),
  ];
};
