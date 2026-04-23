/* eslint-disable import/no-extraneous-dependencies */
import { rest } from "msw";

import type { DataPurposeResponse } from "~/types/api";

import {
  mockDataPurposes,
  mockPurposeDatasets,
  mockPurposeSystems,
  type PurposeDatasetAssignment,
  type PurposeSystemAssignment,
} from "./data";

// In-memory stores so mock mutations persist for the session. The detail-page
// PR adds mutation handlers that write to `systemsStore`/`datasetsStore`; for
// now the listing's summaries endpoint reads from them to compute counts and
// detected categories.
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
    // TODO: replace with real endpoint once fidesplus ships it.
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
  ];
};
