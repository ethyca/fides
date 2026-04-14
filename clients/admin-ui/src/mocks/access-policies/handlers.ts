/* eslint-disable import/no-extraneous-dependencies */
import { rest } from "msw";

import {
  AccessPolicy,
  Control,
} from "~/features/access-policies/access-policies.slice";

import { mockAccessPolicies, mockControls } from "./data";
import { generatedPoliciesForIndustry } from "./generated-policies";
import {
  GEO_DATA_USES,
  INDUSTRY_DATA_USES,
  INDUSTRY_LABELS,
} from "./onboarding-data";

/**
 * MSW handlers for access policy endpoints
 */
export const accessPoliciesHandlers = () => {
  const apiBase = "/api/v1";
  // Use mutable copies so create/update/delete persist within a session
  const policies: AccessPolicy[] = [...mockAccessPolicies];
  const controls: Control[] = [...mockControls];

  return [
    // GET /api/v1/plus/access-policy - list all
    rest.get(`${apiBase}/plus/access-policy`, (req, res, ctx) => {
      const page = parseInt(req.url.searchParams.get("page") ?? "1", 10);
      const size = parseInt(req.url.searchParams.get("size") ?? "50", 10);

      const start = (page - 1) * size;
      const paginatedItems = policies.slice(start, start + size);

      return res(
        ctx.status(200),
        ctx.json({
          items: paginatedItems,
          total: policies.length,
          page,
          size,
          pages: Math.ceil(policies.length / size),
        }),
      );
    }),

    // GET /api/v1/plus/access-policy/presets/industries - available industries
    rest.get(
      `${apiBase}/plus/access-policy/presets/industries`,
      (_req, res, ctx) =>
        res(
          ctx.status(200),
          ctx.json({
            items: Object.keys(INDUSTRY_DATA_USES).map((key) => ({
              label: INDUSTRY_LABELS[key] ?? key,
              value: key,
            })),
          }),
        ),
    ),

    // GET /api/v1/plus/access-policy/presets/config - saved config
    rest.get(`${apiBase}/plus/access-policy/presets/config`, (_req, res, ctx) =>
      res(
        ctx.status(200),
        ctx.json({ industry: "fintech", geographies: ["eea", "us"] }),
      ),
    ),

    // GET /api/v1/plus/access-policy/presets/data-uses - data uses by industry + geography
    rest.get(
      `${apiBase}/plus/access-policy/presets/data-uses`,
      (req, res, ctx) => {
        const industry = req.url.searchParams.get("industry") ?? "";
        const geographies = req.url.searchParams.getAll("geographies");

        const industryUses = INDUSTRY_DATA_USES[industry] ?? [];
        const geoUses = geographies.flatMap((geo) => GEO_DATA_USES[geo] ?? []);
        const uses = [
          ...industryUses,
          ...geoUses.filter((u) => !industryUses.includes(u)),
        ];

        return res(ctx.status(200), ctx.json({ items: uses }));
      },
    ),

    // POST /api/v1/plus/access-policy/presets/generate - generate policies from onboarding
    rest.post(
      `${apiBase}/plus/access-policy/presets/generate`,
      (_req, res, ctx) => {
        // Push generated policies into the mutable array so the list view picks them up
        const generated = generatedPoliciesForIndustry();
        generated.forEach((p) => policies.push(p));

        return res(
          ctx.delay(800),
          ctx.status(200),
          ctx.json({ status: "success" }),
        );
      },
    ),

    // GET /api/v1/plus/controls - list controls
    rest.get(`${apiBase}/plus/controls`, (_req, res, ctx) =>
      res(ctx.status(200), ctx.json(controls)),
    ),

    // POST /api/v1/plus/controls - create control
    rest.post(`${apiBase}/plus/controls`, async (req, res, ctx) => {
      const body = await req.json();
      const key =
        body.key ??
        body.label
          .toLowerCase()
          .replace(/[^a-z0-9]+/g, "_")
          .replace(/^_|_$/g, "");
      if (controls.find((c) => c.key === key)) {
        return res(
          ctx.status(409),
          ctx.json({
            detail: `Control with key '${key}' already exists`,
          }),
        );
      }
      const newControl: Control = {
        key,
        label: body.label,
        description: body.description,
      };
      controls.push(newControl);
      return res(ctx.status(201), ctx.json(newControl));
    }),

    // PATCH /api/v1/plus/controls/:key - update control
    rest.patch(`${apiBase}/plus/controls/:key`, async (req, res, ctx) => {
      const { key } = req.params;
      const index = controls.findIndex((c) => c.key === key);
      if (index === -1) {
        return res(
          ctx.status(404),
          ctx.json({ detail: `No control found with key '${key}'` }),
        );
      }
      const body = await req.json();
      controls[index] = {
        ...controls[index],
        label: body.label,
        description: body.description,
      };
      return res(ctx.status(200), ctx.json(controls[index]));
    }),

    // DELETE /api/v1/plus/controls/:key - delete control
    rest.delete(`${apiBase}/plus/controls/:key`, (req, res, ctx) => {
      const { key } = req.params;
      const index = controls.findIndex((c) => c.key === key);
      if (index === -1) {
        return res(
          ctx.status(404),
          ctx.json({ detail: `No control found with key '${key}'` }),
        );
      }
      const assignedCount = policies.filter((p) =>
        p.controls?.includes(key as string),
      ).length;
      if (assignedCount > 0) {
        return res(
          ctx.status(409),
          ctx.json({
            detail: `Cannot delete control '${key}': it is assigned to ${assignedCount} ${assignedCount === 1 ? "policy" : "policies"}. Reassign or remove those policies first.`,
          }),
        );
      }
      controls.splice(index, 1);
      return res(ctx.status(204));
    }),

    // GET /api/v1/plus/access-policy/:id - get single
    rest.get(`${apiBase}/plus/access-policy/:id`, (req, res, ctx) => {
      const { id } = req.params;
      const policy = policies.find((p) => p.id === id);

      if (!policy) {
        return res(
          ctx.status(404),
          ctx.json({ detail: `Access policy with id ${id} not found` }),
        );
      }

      return res(ctx.status(200), ctx.json(policy));
    }),

    // POST /api/v1/plus/access-policy - create
    rest.post(`${apiBase}/plus/access-policy`, async (req, res, ctx) => {
      const body = await req.json();
      const newPolicy: AccessPolicy = {
        ...body,
        id: `policy-${Date.now()}`,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      policies.push(newPolicy);
      return res(ctx.status(201), ctx.json(newPolicy));
    }),

    // POST /api/v1/plus/access-policy/:id/reorder - reorder
    rest.post(
      `${apiBase}/plus/access-policy/:id/reorder`,
      async (req, res, ctx) => {
        const { id } = req.params;
        const body = await req.json();
        // eslint-disable-next-line @typescript-eslint/naming-convention
        const { insert_after_id: insertAfterId } = body;

        const idx = policies.findIndex((p) => p.id === id);
        if (idx === -1) {
          return res(
            ctx.status(404),
            ctx.json({ detail: `Access policy with id ${id} not found` }),
          );
        }

        const [moved] = policies.splice(idx, 1);
        if (insertAfterId === null || insertAfterId === undefined) {
          policies.unshift(moved);
        } else {
          const afterIdx = policies.findIndex((p) => p.id === insertAfterId);
          if (afterIdx === -1) {
            return res(
              ctx.status(404),
              ctx.json({
                detail: `Access policy with id ${insertAfterId} not found`,
              }),
            );
          }
          policies.splice(afterIdx + 1, 0, moved);
        }

        // Reassign sequential priorities in YAML so subsequent GETs reflect the new order
        policies.forEach((policy, i) => {
          if (policy.yaml) {
            // eslint-disable-next-line no-param-reassign
            policy.yaml = policy.yaml.replace(
              /^priority:\s*\d+/m,
              `priority: ${(i + 1) * 100}`,
            );
          }
        });

        return res(ctx.status(204));
      },
    ),

    // PATCH /api/v1/plus/access-policy/:id - partial update
    rest.patch(`${apiBase}/plus/access-policy/:id`, async (req, res, ctx) => {
      const { id } = req.params;
      const index = policies.findIndex((p) => p.id === id);

      if (index === -1) {
        return res(
          ctx.status(404),
          ctx.json({ detail: `Access policy with id ${id} not found` }),
        );
      }

      const body = await req.json();
      policies[index] = {
        ...policies[index],
        ...body,
        id: id as string,
        updated_at: new Date().toISOString(),
      };
      return res(ctx.status(200), ctx.json(policies[index]));
    }),

    // DELETE /api/v1/plus/access-policy/:id - delete
    rest.delete(`${apiBase}/plus/access-policy/:id`, (req, res, ctx) => {
      const { id } = req.params;
      const index = policies.findIndex((p) => p.id === id);

      if (index === -1) {
        return res(
          ctx.status(404),
          ctx.json({ detail: `Access policy with id ${id} not found` }),
        );
      }

      policies.splice(index, 1);
      return res(ctx.status(204));
    }),
  ];
};
