/* eslint-disable import/no-extraneous-dependencies */
import { rest } from "msw";

import { mockPosture, mockPriorityActions } from "./data";

/**
 * MSW handlers for dashboard endpoints
 */
export const dashboardHandlers = () => {
  const apiBase = "/api/v1";

  return [
    // GET /api/v1/plus/dashboard/posture
    rest.get(`${apiBase}/plus/dashboard/posture`, (_req, res, ctx) =>
      res(ctx.status(200), ctx.json(mockPosture)),
    ),

    // GET /api/v1/plus/dashboard/actions
    rest.get(`${apiBase}/plus/dashboard/actions`, (req, res, ctx) => {
      const page = parseInt(req.url.searchParams.get("page") ?? "1", 10);
      const size = parseInt(req.url.searchParams.get("size") ?? "8", 10);

      const start = (page - 1) * size;
      const end = start + size;
      const paginatedItems = mockPriorityActions.slice(start, end);

      return res(
        ctx.status(200),
        ctx.json({
          items: paginatedItems,
          total: mockPriorityActions.length,
          page,
          size,
          pages: Math.ceil(mockPriorityActions.length / size),
        }),
      );
    }),

    // PATCH /api/v1/plus/dashboard/actions/:actionId
    rest.patch(
      `${apiBase}/plus/dashboard/actions/:actionId`,
      async (req, res, ctx) => {
        const { actionId } = req.params;
        const body = await req.json();
        const action = mockPriorityActions.find((a) => a.id === actionId);

        if (!action) {
          return res(
            ctx.status(404),
            ctx.json({ detail: `Action with id ${actionId} not found` }),
          );
        }

        Object.assign(action, body);
        return res(ctx.status(200), ctx.json(action));
      },
    ),
  ];
};
