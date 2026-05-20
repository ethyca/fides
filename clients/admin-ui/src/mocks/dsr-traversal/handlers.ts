/* eslint-disable import/no-extraneous-dependencies */
import { rest } from "msw";

import {
  ActionType,
  TraversalPreviewResponse,
} from "~/features/dsr-traversal-visualizer/types";

import { mockProperty, mockTraversalPreview } from "./data";

export const dsrTraversalHandlers = () => {
  const apiBase = "/api/v1";

  return [
    // Properties picker -- the visualizer's PropertyPicker calls this.
    rest.get(`${apiBase}/plus/properties`, (_req, res, ctx) =>
      res(
        ctx.status(200),
        ctx.json({
          items: [mockProperty],
          total: 1,
          page: 1,
          size: 100,
          pages: 1,
        }),
      ),
    ),

    // Traversal preview for any property id -- returns the fixture with
    // action_type echoed back from the query string.
    rest.get(
      `${apiBase}/plus/properties/:propertyId/traversal-preview`,
      (req, res, ctx) => {
        const actionType =
          (req.url.searchParams.get("action_type") as ActionType) ||
          ActionType.ACCESS;
        const payload: TraversalPreviewResponse = {
          ...mockTraversalPreview,
          action_type: actionType,
        };
        return res(ctx.status(200), ctx.json(payload));
      },
    ),
  ];
};
