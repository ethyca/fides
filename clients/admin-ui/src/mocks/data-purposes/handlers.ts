/* eslint-disable import/no-extraneous-dependencies */
import { rest } from "msw";

import type { DataPurposeResponse } from "~/types/api";

import {
  mockAvailableDatasets,
  mockAvailableSystems,
  mockDataPurposes,
  mockPurposeDatasets,
  mockPurposeSystems,
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
const systemsStore: Record<string, PurposeSystemAssignment[]> =
  Object.fromEntries(
    Object.entries(mockPurposeSystems).map(([key, value]) => [key, [...value]]),
  );
const datasetsStore: Record<string, PurposeDatasetAssignment[]> =
  Object.fromEntries(
    Object.entries(mockPurposeDatasets).map(([key, value]) => [
      key,
      [...value],
    ]),
  );

const getDetectedCategories = (
  datasets: PurposeDatasetAssignment[],
): string[] => {
  const categories = new Set<string>();
  datasets.forEach((dataset) =>
    dataset.data_categories.forEach((category) => categories.add(category)),
  );
  return Array.from(categories);
};

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
          (purpose) =>
            purpose.name.toLowerCase().includes(search) ||
            purpose.fides_key.toLowerCase().includes(search),
        );
      }
      if (dataUse) {
        filtered = filtered.filter((purpose) => purpose.data_use === dataUse);
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
      const purpose = purposesStore.find(
        (candidate) => candidate.fides_key === fidesKey,
      );
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
      if (
        purposesStore.some((purpose) => purpose.fides_key === body.fides_key)
      ) {
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
      const index = purposesStore.findIndex(
        (purpose) => purpose.fides_key === fidesKey,
      );
      if (index === -1) {
        return res(ctx.status(404), ctx.json({ detail: "Purpose not found" }));
      }
      const updated: DataPurposeResponse = {
        ...purposesStore[index],
        ...body,
        fides_key: purposesStore[index].fides_key,
        id: purposesStore[index].id,
        updated_at: new Date().toISOString(),
      };
      purposesStore[index] = updated;
      return res(ctx.status(200), ctx.json(updated));
    }),

    // DELETE /api/v1/data-purpose/:fidesKey
    rest.delete(`${apiBase}/data-purpose/:fidesKey`, (req, res, ctx) => {
      const { fidesKey } = req.params;
      const index = purposesStore.findIndex(
        (purpose) => purpose.fides_key === fidesKey,
      );
      if (index === -1) {
        return res(ctx.status(404), ctx.json({ detail: "Purpose not found" }));
      }
      purposesStore.splice(index, 1);
      delete systemsStore[fidesKey as string];
      delete datasetsStore[fidesKey as string];
      return res(ctx.status(204));
    }),

    // --- MSW-only handlers (no real backend endpoint yet) ---
    // TODO: replace with real endpoints once fidesplus ships them.

    // GET /api/v1/plus/data-purpose/summaries — batched per-purpose enrichment
    rest.get(`${plusBase}/data-purpose/summaries`, (_req, res, ctx) => {
      const summaries = purposesStore.map((purpose) => {
        const systems = systemsStore[purpose.fides_key] ?? [];
        const datasets = datasetsStore[purpose.fides_key] ?? [];
        return {
          fides_key: purpose.fides_key,
          system_count: systems.filter((system) => system.assigned).length,
          dataset_count: datasets.length,
          detected_data_categories: getDetectedCategories(datasets),
          systems,
          datasets,
        };
      });
      return res(ctx.status(200), ctx.json(summaries));
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
          (systemsStore[fidesKey as string] ?? []).map(
            (system) => system.system_id,
          ),
        );
        const available = mockAvailableSystems.filter(
          (system) => !assignedIds.has(system.system_id),
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
            (dataset) => dataset.dataset_fides_key,
          ),
        );
        const available = mockAvailableDatasets.filter(
          (dataset) => !assignedKeys.has(dataset.dataset_fides_key),
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
        const existingIds = new Set(existing.map((system) => system.system_id));
        const additions = mockAvailableSystems
          .filter(
            (system) =>
              body.system_ids.includes(system.system_id) &&
              !existingIds.has(system.system_id),
          )
          .map<PurposeSystemAssignment>((system) => ({
            system_id: system.system_id,
            system_name: system.system_name,
            system_type: system.system_type,
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
        const removeIds = new Set(body.system_ids);
        systemsStore[key] = (systemsStore[key] ?? []).filter(
          (system) => !removeIds.has(system.system_id),
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
        const existingKeys = new Set(
          existing.map((dataset) => dataset.dataset_fides_key),
        );
        const additions = mockAvailableDatasets
          .filter(
            (dataset) =>
              body.dataset_fides_keys.includes(dataset.dataset_fides_key) &&
              !existingKeys.has(dataset.dataset_fides_key),
          )
          .map<PurposeDatasetAssignment>((dataset) => ({
            dataset_fides_key: dataset.dataset_fides_key,
            dataset_name: dataset.dataset_name,
            system_name: dataset.system_name,
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
        const removeKeys = new Set(body.dataset_fides_keys);
        datasetsStore[key] = (datasetsStore[key] ?? []).filter(
          (dataset) => !removeKeys.has(dataset.dataset_fides_key),
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
        const purposeIndex = purposesStore.findIndex(
          (purpose) => purpose.fides_key === key,
        );
        if (purposeIndex === -1) {
          return res(
            ctx.status(404),
            ctx.json({ detail: "Purpose not found" }),
          );
        }
        const existing = new Set(
          purposesStore[purposeIndex].data_categories ?? [],
        );
        body.categories.forEach((category) => existing.add(category));
        purposesStore[purposeIndex] = {
          ...purposesStore[purposeIndex],
          data_categories: Array.from(existing),
          updated_at: new Date().toISOString(),
        };
        return res(ctx.status(200), ctx.json(purposesStore[purposeIndex]));
      },
    ),

    // POST /api/v1/plus/data-purpose/:fidesKey/categories/misclassified
    rest.post(
      `${plusBase}/data-purpose/:fidesKey/categories/misclassified`,
      async (req, res, ctx) => {
        const { fidesKey } = req.params;
        const body = (await req.json()) as CategoryActionBody;
        const key = fidesKey as string;
        const categorySet = new Set(body.categories);
        const datasetKeys = new Set(body.dataset_fides_keys ?? []);
        if (datasetKeys.size > 0) {
          datasetsStore[key] = (datasetsStore[key] ?? []).map((dataset) =>
            datasetKeys.has(dataset.dataset_fides_key)
              ? {
                  ...dataset,
                  data_categories: dataset.data_categories.filter(
                    (category) => !categorySet.has(category),
                  ),
                }
              : dataset,
          );
        }
        return res(ctx.status(200), ctx.json(datasetsStore[key] ?? []));
      },
    ),
  ];
};
