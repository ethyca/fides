/* eslint-disable import/no-extraneous-dependencies */
import { rest } from "msw";

import { ActionType } from "~/features/dashboard/types";

import {
  mockAgentBriefing,
  mockPosture,
  mockPriorityActions,
  mockPrivacyRequests,
  mockSystemCoverage,
} from "./data";

const DIMENSION_ACTION_TYPES: Record<string, ActionType[]> = {
  coverage: [ActionType.SYSTEM_REVIEW, ActionType.STEWARD_ASSIGNMENT],
  classification_health: [ActionType.CLASSIFICATION_REVIEW],
  dsr_compliance: [ActionType.DSR_ACTION],
  consent_alignment: [ActionType.CONSENT_ANOMALY, ActionType.POLICY_VIOLATION],
};

export const dashboardHandlers = () => {
  const apiBase = "/api/v1";

  return [
    rest.get(`${apiBase}/plus/dashboard/posture`, (_req, res, ctx) =>
      res(ctx.status(200), ctx.json(mockPosture)),
    ),

    rest.get(`${apiBase}/plus/dashboard/actions`, (req, res, ctx) => {
      const page = parseInt(req.url.searchParams.get("page") ?? "1", 10);
      const size = parseInt(req.url.searchParams.get("size") ?? "8", 10);
      const dimension = req.url.searchParams.get("dimension");

      let items = mockPriorityActions;
      if (dimension) {
        const allowedTypes =
          DIMENSION_ACTION_TYPES[
            dimension as keyof typeof DIMENSION_ACTION_TYPES
          ];
        if (allowedTypes) {
          items = items.filter((a) => allowedTypes.includes(a.type));
        }
      }

      const start = (page - 1) * size;
      const end = start + size;
      const paginatedItems = items.slice(start, end);

      return res(
        ctx.status(200),
        ctx.json({
          items: paginatedItems,
          total: items.length,
          page,
          size,
          pages: Math.ceil(items.length / size),
        }),
      );
    }),

    rest.get(`${apiBase}/plus/dashboard/system-coverage`, (_req, res, ctx) =>
      res(ctx.status(200), ctx.json(mockSystemCoverage)),
    ),

    rest.get(`${apiBase}/plus/dashboard/privacy-requests`, (_req, res, ctx) =>
      res(ctx.status(200), ctx.json(mockPrivacyRequests)),
    ),

    rest.get(`${apiBase}/plus/dashboard/agent-briefing`, (_req, res, ctx) =>
      res(ctx.status(200), ctx.json(mockAgentBriefing)),
    ),

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
