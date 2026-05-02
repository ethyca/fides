/* eslint-disable import/no-extraneous-dependencies */
import { rest } from "msw";

import {
  computeCategoryDrift,
  formatDataUse,
} from "~/features/data-purposes/purposeUtils";
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

// CSV export — RoPA shape mirrors what the real fidesplus endpoint will return
// when called with `?download_csv=true`. Header order is the contract.
const ROPA_HEADER = [
  "Reference",
  "Processing activity",
  "Description",
  "Purpose of processing",
  "Lawful basis (Art. 6)",
  "Special category basis (Art. 9)",
  "Categories of data subjects",
  "Categories of personal data",
  "Categories of personal data (detected)",
  "Retention period (days)",
  "Features",
  "Last reviewed",
];

const escapeCsvCell = (value: unknown): string =>
  `"${String(value ?? "").replace(/"/g, '""')}"`;

const buildRoPACsv = (purposes: DataPurposeResponse[]): string => {
  const rows = purposes.map((purpose) => {
    const datasets = datasetsStore[purpose.fides_key] ?? [];
    return [
      purpose.fides_key,
      purpose.name,
      purpose.description ?? "",
      purpose.data_use,
      purpose.legal_basis_for_processing ?? "",
      purpose.special_category_legal_basis ?? "",
      purpose.data_subject ?? "",
      (purpose.data_categories ?? []).join("; "),
      getDetectedCategories(datasets).join("; "),
      purpose.retention_period ?? "",
      (purpose.features ?? []).join("; "),
      purpose.updated_at ?? "",
    ];
  });
  const body = [ROPA_HEADER, ...rows]
    .map((row) => row.map(escapeCsvCell).join(","))
    .join("\r\n");
  return `\ufeff${body}`;
};

export const dataPurposesHandlers = () => {
  const apiBase = "/api/v1";
  const plusBase = `${apiBase}/plus`;

  return [
    // --- Real-endpoint handlers (mirroring fidesplus routes) ---
    rest.get(`${apiBase}/data-purpose`, (req, res, ctx) => {
      const search = req.url.searchParams.get("search")?.toLowerCase() ?? "";
      const dataUse = req.url.searchParams.get("data_use");
      const consumer = req.url.searchParams.get("consumer");
      const category = req.url.searchParams.get("category");
      const status = req.url.searchParams.get("status");
      const downloadCsv = req.url.searchParams.get("download_csv") === "true";

      const purposeStatus = (purpose: DataPurposeResponse) => {
        const datasets = datasetsStore[purpose.fides_key] ?? [];
        return computeCategoryDrift(
          purpose.data_categories ?? [],
          getDetectedCategories(datasets),
        ).status;
      };

      const purposeAssignedSystemIds = (purpose: DataPurposeResponse) =>
        new Set(
          (systemsStore[purpose.fides_key] ?? [])
            .filter((assignment) => assignment.assigned)
            .map((assignment) => assignment.system_id),
        );

      const applyFilters = (
        purposes: DataPurposeResponse[],
        active: {
          search?: string;
          dataUse?: string | null;
          consumer?: string | null;
          category?: string | null;
          status?: string | null;
        },
      ) => {
        let result = purposes;
        if (active.search) {
          const term = active.search;
          result = result.filter(
            (purpose) =>
              purpose.name.toLowerCase().includes(term) ||
              purpose.fides_key.toLowerCase().includes(term),
          );
        }
        if (active.dataUse) {
          result = result.filter(
            (purpose) => purpose.data_use === active.dataUse,
          );
        }
        if (active.consumer) {
          result = result.filter((purpose) =>
            purposeAssignedSystemIds(purpose).has(active.consumer!),
          );
        }
        if (active.category) {
          result = result.filter((purpose) =>
            (purpose.data_categories ?? []).includes(active.category!),
          );
        }
        if (active.status) {
          result = result.filter(
            (purpose) => purposeStatus(purpose) === active.status,
          );
        }
        return result;
      };

      const allFilters = { search, dataUse, consumer, category, status };
      const filtered = applyFilters(purposesStore, allFilters);

      if (downloadCsv) {
        const csv = buildRoPACsv(filtered);
        return res(
          ctx.status(200),
          ctx.set("Content-Type", "text/csv; charset=utf-8"),
          ctx.set(
            "Content-Disposition",
            `attachment; filename="ropa-export.csv"`,
          ),
          ctx.body(csv),
        );
      }

      // Faceted filter options — each dimension's options are derived from the
      // population obtained by applying *all other* filters. The currently-
      // selected value persists in its own dropdown; values that would yield
      // zero results given the current selection don't appear. Mirrors the
      // action-center / discovered-assets pattern (see useDiscoveredAssetsTable).
      const consumerPool = applyFilters(purposesStore, {
        ...allFilters,
        consumer: null,
      });
      const dataUsePool = applyFilters(purposesStore, {
        ...allFilters,
        dataUse: null,
      });
      const categoryPool = applyFilters(purposesStore, {
        ...allFilters,
        category: null,
      });
      const statusPool = applyFilters(purposesStore, {
        ...allFilters,
        status: null,
      });

      const consumerMap = new Map<string, string>();
      consumerPool.forEach((purpose) => {
        (systemsStore[purpose.fides_key] ?? [])
          .filter((assignment) => assignment.assigned)
          .forEach((assignment) => {
            if (!consumerMap.has(assignment.system_id)) {
              consumerMap.set(assignment.system_id, assignment.system_name);
            }
          });
      });
      const dataUses = Array.from(
        new Set(dataUsePool.map((purpose) => purpose.data_use)),
      );
      const categories = new Set<string>();
      categoryPool.forEach((purpose) => {
        (purpose.data_categories ?? []).forEach((c) => categories.add(c));
      });
      const statuses = new Set<string>();
      statusPool.forEach((purpose) => statuses.add(purposeStatus(purpose)));
      const STATUS_LABELS: Record<string, string> = {
        drift: "Has risks",
        compliant: "Compliant",
        unknown: "Not scanned",
      };
      const STATUS_ORDER = ["drift", "compliant", "unknown"];

      return res(
        ctx.status(200),
        ctx.json({
          items: filtered,
          total: filtered.length,
          filter_options: {
            consumers: Array.from(consumerMap, ([value, label]) => ({
              value,
              label,
            })).sort((a, b) => a.label.localeCompare(b.label)),
            data_uses: dataUses
              .map((value) => ({ value, label: formatDataUse(value) }))
              .sort((a, b) => a.label.localeCompare(b.label)),
            categories: Array.from(categories)
              .sort()
              .map((value) => ({ value, label: value })),
            statuses: STATUS_ORDER.filter((value) => statuses.has(value)).map(
              (value) => ({ value, label: STATUS_LABELS[value] }),
            ),
          },
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
