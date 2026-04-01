/* eslint-disable import/no-extraneous-dependencies */
import { rest } from "msw";

import type { ManualFieldListItem } from "~/types/api";

import { mockManualTaskFilterOptions, mockManualTasks } from "./data";

export const manualTasksHandlers = () => {
  const apiBase = "/api/v1";
  const tasks: ManualFieldListItem[] = [...mockManualTasks];

  return [
    // GET /api/v1/plus/manual-fields - paginated list with filters
    rest.get(`${apiBase}/plus/manual-fields`, (req, res, ctx) => {
      const page = parseInt(req.url.searchParams.get("page") ?? "1", 10);
      const size = parseInt(req.url.searchParams.get("size") ?? "25", 10);
      const status = req.url.searchParams.get("status");
      const requestType = req.url.searchParams.get("request_type");
      const systemName = req.url.searchParams.get("system_name");
      const assignedUserId = req.url.searchParams.get("assigned_user_id");
      const privacyRequestId = req.url.searchParams.get("privacy_request_id");

      let filtered = [...tasks];

      if (status) {
        filtered = filtered.filter((t) => t.status === status);
      }
      if (requestType) {
        filtered = filtered.filter((t) => t.request_type === requestType);
      }
      if (systemName) {
        filtered = filtered.filter((t) => t.system?.name === systemName);
      }
      if (assignedUserId) {
        filtered = filtered.filter((t) =>
          t.assigned_users?.some((u) => u.id === assignedUserId),
        );
      }
      if (privacyRequestId) {
        filtered = filtered.filter(
          (t) => t.privacy_request.id === privacyRequestId,
        );
      }

      const start = (page - 1) * size;
      const paginatedItems = filtered.slice(start, start + size);

      return res(
        ctx.status(200),
        ctx.json({
          items: paginatedItems,
          total: filtered.length,
          page,
          size,
          pages: Math.ceil(filtered.length / size),
          filter_options: mockManualTaskFilterOptions,
        }),
      );
    }),

    // GET /api/v1/plus/manual-fields/:taskId - single task detail
    rest.get(`${apiBase}/plus/manual-fields/:taskId`, (req, res, ctx) => {
      const { taskId } = req.params;
      const task = tasks.find((t) => t.manual_field_id === taskId);

      if (!task) {
        return res(
          ctx.status(404),
          ctx.json({ detail: `Manual field ${taskId} not found` }),
        );
      }

      return res(ctx.status(200), ctx.json(task));
    }),

    // POST /api/v1/privacy-request/:privacyRequestId/manual-field/:manualFieldId/complete
    rest.post(
      `${apiBase}/privacy-request/:privacyRequestId/manual-field/:manualFieldId/complete`,
      (req, res, ctx) => {
        const { manualFieldId } = req.params;
        const task = tasks.find((t) => t.manual_field_id === manualFieldId);

        if (task) {
          task.status = "completed" as ManualFieldListItem["status"];
          task.updated_at = new Date().toISOString();
        }

        return res(
          ctx.status(200),
          ctx.json({
            manual_field_id: manualFieldId,
            status: "completed",
          }),
        );
      },
    ),

    // POST /api/v1/privacy-request/:privacyRequestId/manual-field/:manualFieldId/skip
    rest.post(
      `${apiBase}/privacy-request/:privacyRequestId/manual-field/:manualFieldId/skip`,
      (req, res, ctx) => {
        const { manualFieldId } = req.params;
        const task = tasks.find((t) => t.manual_field_id === manualFieldId);

        if (task) {
          task.status = "skipped" as ManualFieldListItem["status"];
          task.updated_at = new Date().toISOString();
        }

        return res(
          ctx.status(200),
          ctx.json({
            manual_field_id: manualFieldId,
            status: "skipped",
          }),
        );
      },
    ),

    // POST /api/v1/plus/manual-fields/export
    rest.post(`${apiBase}/plus/manual-fields/export`, (_req, res, ctx) =>
      res(
        ctx.status(200),
        ctx.set("content-type", "text/csv"),
        ctx.body("name,status,system_name,request_type\n"),
      ),
    ),
  ];
};
