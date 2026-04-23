/* eslint-disable import/no-extraneous-dependencies */
import { rest } from "msw";

import type { DataPurposeResponse } from "~/types/api";

import {
  mockAvailableDatasets,
  mockAvailableSystems,
  mockDataPurposes,
  mockPurposeCoverage,
  mockPurposeDatasets,
  mockPurposeSystems,
  type PurposeCoverage,
  type PurposeDatasetAssignment,
  type PurposeSystemAssignment,
} from "./data";

interface BulkDatasetKeysBody {
  dataset_fides_keys: string[];
}

interface CategoryActionBody {
  categories: string[];
  dataset_fides_keys?: string[];
}

interface AssignSystemsBody {
  system_ids: string[];
}

// In-memory stores so mock mutations persist for the session.
const purposesStore: DataPurposeResponse[] = [...mockDataPurposes];
const coverageStore: Record<string, PurposeCoverage> = {
  ...mockPurposeCoverage,
};
const systemsStore: Record<string, PurposeSystemAssignment[]> =
  Object.fromEntries(
    Object.entries(mockPurposeSystems).map(([k, v]) => [k, [...v]]),
  );
const datasetsStore: Record<string, PurposeDatasetAssignment[]> =
  Object.fromEntries(
    Object.entries(mockPurposeDatasets).map(([k, v]) => [k, [...v]]),
  );

export const dataPurposesHandlers = () => {
  const apiBase = "/api/v1";
  const plusBase = `${apiBase}/plus`;

  return [
    // --- Real-endpoint handlers (mirroring fidesplus routes) ---

    // GET /api/v1/data-purpose — paginated list
    rest.get(`${apiBase}/data-purpose`, (req, res, ctx) => {
      const page = parseInt(req.url.searchParams.get("page") ?? "1", 10);
      const size = parseInt(req.url.searchParams.get("size") ?? "50", 10);
      const search = req.url.searchParams.get("search")?.toLowerCase() ?? "";
      const dataUse = req.url.searchParams.get("data_use");

      let filtered = [...purposesStore];
      if (search) {
        filtered = filtered.filter(
          (p) =>
            p.name.toLowerCase().includes(search) ||
            p.fides_key.toLowerCase().includes(search),
        );
      }
      if (dataUse) {
        filtered = filtered.filter((p) => p.data_use === dataUse);
      }

      const start = (page - 1) * size;
      const items = filtered.slice(start, start + size);

      return res(
        ctx.status(200),
        ctx.json({
          items,
          total: filtered.length,
          page,
          size,
          pages: Math.max(1, Math.ceil(filtered.length / size)),
        }),
      );
    }),

    // GET /api/v1/data-purpose/:fidesKey
    rest.get(`${apiBase}/data-purpose/:fidesKey`, (req, res, ctx) => {
      const { fidesKey } = req.params;
      const purpose = purposesStore.find((p) => p.fides_key === fidesKey);
      if (!purpose) {
        return res(ctx.status(404), ctx.json({ detail: "Purpose not found" }));
      }
      return res(ctx.status(200), ctx.json(purpose));
    }),

    // POST /api/v1/data-purpose
    rest.post(`${apiBase}/data-purpose`, async (req, res, ctx) => {
      const body = (await req.json()) as Partial<DataPurposeResponse>;
      if (!body.fides_key || !body.name || !body.data_use) {
        return res(
          ctx.status(422),
          ctx.json({ detail: "fides_key, name and data_use are required" }),
        );
      }
      if (purposesStore.some((p) => p.fides_key === body.fides_key)) {
        return res(
          ctx.status(409),
          ctx.json({ detail: "Purpose with this fides_key already exists" }),
        );
      }
      const now = new Date().toISOString();
      const created: DataPurposeResponse = {
        id: body.fides_key,
        fides_key: body.fides_key,
        name: body.name,
        description: body.description ?? null,
        data_use: body.data_use,
        data_subject: body.data_subject ?? null,
        data_categories: body.data_categories ?? [],
        legal_basis_for_processing: body.legal_basis_for_processing ?? null,
        flexible_legal_basis_for_processing:
          body.flexible_legal_basis_for_processing ?? false,
        special_category_legal_basis: body.special_category_legal_basis ?? null,
        impact_assessment_location: body.impact_assessment_location ?? null,
        retention_period: body.retention_period ?? null,
        features: body.features ?? [],
        created_at: now,
        updated_at: now,
      };
      purposesStore.push(created);
      return res(ctx.status(201), ctx.json(created));
    }),

    // PUT /api/v1/data-purpose/:fidesKey
    rest.put(`${apiBase}/data-purpose/:fidesKey`, async (req, res, ctx) => {
      const { fidesKey } = req.params;
      const body = (await req.json()) as Partial<DataPurposeResponse>;
      const idx = purposesStore.findIndex((p) => p.fides_key === fidesKey);
      if (idx === -1) {
        return res(ctx.status(404), ctx.json({ detail: "Purpose not found" }));
      }
      const updated: DataPurposeResponse = {
        ...purposesStore[idx],
        ...body,
        fides_key: purposesStore[idx].fides_key,
        id: purposesStore[idx].id,
        updated_at: new Date().toISOString(),
      };
      purposesStore[idx] = updated;
      return res(ctx.status(200), ctx.json(updated));
    }),

    // DELETE /api/v1/data-purpose/:fidesKey
    rest.delete(`${apiBase}/data-purpose/:fidesKey`, (req, res, ctx) => {
      const { fidesKey } = req.params;
      const idx = purposesStore.findIndex((p) => p.fides_key === fidesKey);
      if (idx === -1) {
        return res(ctx.status(404), ctx.json({ detail: "Purpose not found" }));
      }
      purposesStore.splice(idx, 1);
      delete coverageStore[fidesKey as string];
      delete systemsStore[fidesKey as string];
      delete datasetsStore[fidesKey as string];
      return res(ctx.status(204));
    }),

    // --- MSW-only handlers (no real backend endpoint yet) ---
    // TODO: replace with real endpoints once fidesplus ships them.

    // GET /api/v1/plus/data-purpose/summaries — batched per-purpose enrichment
    rest.get(`${plusBase}/data-purpose/summaries`, (_req, res, ctx) => {
      const summaries = purposesStore.map((p) => {
        const systems = systemsStore[p.fides_key] ?? [];
        const datasets = datasetsStore[p.fides_key] ?? [];
        const coverage = coverageStore[p.fides_key];
        return {
          fides_key: p.fides_key,
          system_count: systems.filter((s) => s.assigned).length,
          dataset_count: datasets.length,
          detected_data_categories: coverage?.detected_data_categories ?? [],
          systems,
          datasets,
        };
      });
      return res(ctx.status(200), ctx.json(summaries));
    }),

    // GET /api/v1/plus/data-purpose/:fidesKey/coverage
    rest.get(`${plusBase}/data-purpose/:fidesKey/coverage`, (req, res, ctx) => {
      const { fidesKey } = req.params;
      const coverage = coverageStore[fidesKey as string];
      if (!coverage) {
        return res(
          ctx.status(200),
          ctx.json({
            fides_key: fidesKey,
            systems: { assigned: 0, total: 0 },
            datasets: { assigned: 0, total: 0 },
            tables: { assigned: 0, total: 0 },
            fields: { assigned: 0, total: 0 },
            detected_data_categories: [],
          }),
        );
      }
      return res(ctx.status(200), ctx.json(coverage));
    }),

    // GET /api/v1/plus/data-purpose/:fidesKey/systems
    rest.get(`${plusBase}/data-purpose/:fidesKey/systems`, (req, res, ctx) => {
      const { fidesKey } = req.params;
      return res(
        ctx.status(200),
        ctx.json(systemsStore[fidesKey as string] ?? []),
      );
    }),

    // GET /api/v1/plus/data-purpose/:fidesKey/datasets
    rest.get(`${plusBase}/data-purpose/:fidesKey/datasets`, (req, res, ctx) => {
      const { fidesKey } = req.params;
      return res(
        ctx.status(200),
        ctx.json(datasetsStore[fidesKey as string] ?? []),
      );
    }),

    // GET /api/v1/plus/data-purpose/:fidesKey/available-systems
    // "Available" = not yet assigned to this purpose.
    rest.get(
      `${plusBase}/data-purpose/:fidesKey/available-systems`,
      (req, res, ctx) => {
        const { fidesKey } = req.params;
        const assignedIds = new Set(
          (systemsStore[fidesKey as string] ?? []).map((s) => s.system_id),
        );
        const available = mockAvailableSystems.filter(
          (s) => !assignedIds.has(s.system_id),
        );
        return res(ctx.status(200), ctx.json(available));
      },
    ),

    // GET /api/v1/plus/data-purpose/:fidesKey/available-datasets
    // "Available" = not yet assigned to this purpose.
    rest.get(
      `${plusBase}/data-purpose/:fidesKey/available-datasets`,
      (req, res, ctx) => {
        const { fidesKey } = req.params;
        const assignedKeys = new Set(
          (datasetsStore[fidesKey as string] ?? []).map(
            (d) => d.dataset_fides_key,
          ),
        );
        const available = mockAvailableDatasets.filter(
          (d) => !assignedKeys.has(d.dataset_fides_key),
        );
        return res(ctx.status(200), ctx.json(available));
      },
    ),

    // PUT /api/v1/plus/data-purpose/:fidesKey/systems — assign systems (bulk)
    rest.put(
      `${plusBase}/data-purpose/:fidesKey/systems`,
      async (req, res, ctx) => {
        const { fidesKey } = req.params;
        const body = (await req.json()) as AssignSystemsBody;
        const key = fidesKey as string;
        const existing = systemsStore[key] ?? [];
        const existingIds = new Set(existing.map((s) => s.system_id));
        const additions = mockAvailableSystems
          .filter(
            (s) =>
              body.system_ids.includes(s.system_id) &&
              !existingIds.has(s.system_id),
          )
          .map<PurposeSystemAssignment>((s) => ({
            system_id: s.system_id,
            system_name: s.system_name,
            system_type: s.system_type,
            assigned: true,
            consumer_category: "system",
          }));
        systemsStore[key] = [...existing, ...additions];
        return res(ctx.status(200), ctx.json(systemsStore[key]));
      },
    ),

    // DELETE /api/v1/plus/data-purpose/:fidesKey/systems — remove systems (bulk)
    rest.delete(
      `${plusBase}/data-purpose/:fidesKey/systems`,
      async (req, res, ctx) => {
        const { fidesKey } = req.params;
        const body = (await req.json()) as AssignSystemsBody;
        const key = fidesKey as string;
        const remove = new Set(body.system_ids);
        systemsStore[key] = (systemsStore[key] ?? []).filter(
          (s) => !remove.has(s.system_id),
        );
        return res(ctx.status(200), ctx.json(systemsStore[key]));
      },
    ),

    // PUT /api/v1/plus/data-purpose/:fidesKey/datasets — add datasets (bulk)
    rest.put(
      `${plusBase}/data-purpose/:fidesKey/datasets`,
      async (req, res, ctx) => {
        const { fidesKey } = req.params;
        const body = (await req.json()) as BulkDatasetKeysBody;
        const key = fidesKey as string;
        const existing = datasetsStore[key] ?? [];
        const existingKeys = new Set(existing.map((d) => d.dataset_fides_key));
        const additions = mockAvailableDatasets
          .filter(
            (d) =>
              body.dataset_fides_keys.includes(d.dataset_fides_key) &&
              !existingKeys.has(d.dataset_fides_key),
          )
          .map<PurposeDatasetAssignment>((d) => ({
            dataset_fides_key: d.dataset_fides_key,
            dataset_name: d.dataset_name,
            system_name: d.system_name,
            collection_count: 0,
            data_categories: [],
            updated_at: new Date().toISOString(),
            steward: "Unassigned",
          }));
        datasetsStore[key] = [...existing, ...additions];
        return res(ctx.status(200), ctx.json(datasetsStore[key]));
      },
    ),

    // DELETE /api/v1/plus/data-purpose/:fidesKey/datasets — remove datasets (bulk)
    rest.delete(
      `${plusBase}/data-purpose/:fidesKey/datasets`,
      async (req, res, ctx) => {
        const { fidesKey } = req.params;
        const body = (await req.json()) as BulkDatasetKeysBody;
        const key = fidesKey as string;
        const remove = new Set(body.dataset_fides_keys);
        datasetsStore[key] = (datasetsStore[key] ?? []).filter(
          (d) => !remove.has(d.dataset_fides_key),
        );
        return res(ctx.status(200), ctx.json(datasetsStore[key]));
      },
    ),

    // POST /api/v1/plus/data-purpose/:fidesKey/categories/accept
    rest.post(
      `${plusBase}/data-purpose/:fidesKey/categories/accept`,
      async (req, res, ctx) => {
        const { fidesKey } = req.params;
        const body = (await req.json()) as CategoryActionBody;
        const key = fidesKey as string;
        const purposeIdx = purposesStore.findIndex((p) => p.fides_key === key);
        if (purposeIdx === -1) {
          return res(
            ctx.status(404),
            ctx.json({ detail: "Purpose not found" }),
          );
        }
        const existing = new Set(
          purposesStore[purposeIdx].data_categories ?? [],
        );
        body.categories.forEach((c) => existing.add(c));
        purposesStore[purposeIdx] = {
          ...purposesStore[purposeIdx],
          data_categories: Array.from(existing),
          updated_at: new Date().toISOString(),
        };
        return res(ctx.status(200), ctx.json(purposesStore[purposeIdx]));
      },
    ),

    // POST /api/v1/plus/data-purpose/:fidesKey/categories/misclassified
    rest.post(
      `${plusBase}/data-purpose/:fidesKey/categories/misclassified`,
      async (req, res, ctx) => {
        const { fidesKey } = req.params;
        const body = (await req.json()) as CategoryActionBody;
        const key = fidesKey as string;
        const catSet = new Set(body.categories);
        const datasetKeys = new Set(body.dataset_fides_keys ?? []);
        const cov = coverageStore[key];
        if (cov) {
          coverageStore[key] = {
            ...cov,
            detected_data_categories: cov.detected_data_categories.filter(
              (c) => !catSet.has(c),
            ),
          };
        }
        if (datasetKeys.size > 0) {
          datasetsStore[key] = (datasetsStore[key] ?? []).map((d) =>
            datasetKeys.has(d.dataset_fides_key)
              ? {
                  ...d,
                  data_categories: d.data_categories.filter(
                    (c) => !catSet.has(c),
                  ),
                }
              : d,
          );
        }
        return res(
          ctx.status(200),
          ctx.json({
            coverage: coverageStore[key],
            datasets: datasetsStore[key] ?? [],
          }),
        );
      },
    ),
  ];
};
