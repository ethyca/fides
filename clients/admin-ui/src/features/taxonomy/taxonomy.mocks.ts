/* eslint-disable import/no-extraneous-dependencies */
import { rest } from "msw";

import { TaxonomyEntity } from "./types";

// Seed data for Sensitivity taxonomy
export const mockSensitivityData: TaxonomyEntity[] = [
  {
    fides_key: "low",
    name: "Low",
    description: "Low sensitivity",
    parent_key: null,
    active: true,
    is_default: false,
  },
  {
    fides_key: "medium",
    name: "Medium",
    description: "Medium sensitivity",
    parent_key: null,
    active: true,
    is_default: false,
  },
  {
    fides_key: "high",
    name: "High",
    description: "High sensitivity",
    parent_key: null,
    active: true,
    is_default: false,
  },
];

// Available dynamic taxonomies list for the UI selector (only sensitivity for now)
export interface AvailableTaxonomySummary {
  fides_key: string;
  name: string;
}

export const mockAvailableTaxonomies: AvailableTaxonomySummary[] = [
  { fides_key: "sensitivity", name: "Sensitivity" },
];

// Storage helpers backed by localStorage when available (browser),
// with an in-memory fallback (Node/JSDOM).
const STORAGE_KEY = "mock_sensitivity_taxonomy";
const hasLocalStorage = typeof window !== "undefined" && !!window.localStorage;

const readStorage = (): TaxonomyEntity[] => {
  if (hasLocalStorage) {
    try {
      const raw = window.localStorage.getItem(STORAGE_KEY);
      if (raw) {
        return JSON.parse(raw) as TaxonomyEntity[];
      }
    } catch {
      // ignore parsing errors and fall back to seed
    }
  }
  return [...mockSensitivityData];
};

const writeStorage = (data: TaxonomyEntity[]) => {
  if (hasLocalStorage) {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
    } catch {
      // ignore quota or serialization errors
    }
  }
};

let sensitivityStorage = readStorage();

// Factory so tests / stories can override data
export const taxonomyHandlers = (
  initialData: TaxonomyEntity[] = mockSensitivityData,
  taxonomyType = "sensitivity",
) => {
  sensitivityStorage = [...(hasLocalStorage ? readStorage() : initialData)];
  writeStorage(sensitivityStorage);

  const apiBase = "/api/v1"; // we match relative to avoid hard-coding host
  return [
    // GET - list available dynamic taxonomies
    rest.get(`${apiBase}/taxonomies`, (_req, res, ctx) =>
      res(ctx.status(200), ctx.json(mockAvailableTaxonomies)),
    ),

    // GET - return current storage
    rest.get(`${apiBase}/taxonomies/${taxonomyType}`, (_req, res, ctx) => {
      // Sort items so parents come before children using topological sort
      const sortItems = (items: typeof sensitivityStorage) => {
        const result: typeof sensitivityStorage = [];
        const remaining = [...items];

        // First pass: add all root items (parent_key === null)
        const rootItems = remaining.filter((item) => item.parent_key === null);
        rootItems.sort((a, b) => a.fides_key.localeCompare(b.fides_key));
        result.push(...rootItems);

        // Remove root items from remaining
        remaining.splice(
          0,
          remaining.length,
          ...remaining.filter((item) => item.parent_key !== null),
        );

        // Add children after their parents
        while (remaining.length > 0) {
          const addedInThisPass: typeof sensitivityStorage = [];

          for (let i = remaining.length - 1; i >= 0; i -= 1) {
            const item = remaining[i];
            // Check if parent already exists in result
            if (
              result.some(
                (resultItem) => resultItem.fides_key === item.parent_key,
              )
            ) {
              addedInThisPass.push(item);
              remaining.splice(i, 1);
            }
          }

          if (addedInThisPass.length === 0) {
            // No progress made, add remaining items to avoid infinite loop
            result.push(...remaining);
            break;
          }

          // Sort children alphabetically and add to result
          addedInThisPass.sort((a, b) =>
            a.fides_key.localeCompare(b.fides_key),
          );
          result.push(...addedInThisPass);
        }

        return result;
      };

      const sortedItems = sortItems(sensitivityStorage);

      return res(ctx.status(200), ctx.json(sortedItems));
    }),
    // POST (create) - add to storage
    rest.post(
      `${apiBase}/taxonomies/${taxonomyType}`,
      async (req, res, ctx) => {
        const newItem = (await req.json()) as Partial<TaxonomyEntity>;

        // Generate fides_key from name if not provided
        const fidesKey =
          newItem.fides_key ||
          (newItem.name && newItem.name.trim()
            ? newItem.name
                .toLowerCase()
                .replace(/&/g, "and")
                .replace(/'/g, "") // Remove apostrophes
                .replace(/[^a-z0-9]/g, "_")
                .replace(/_+/g, "_") // Replace multiple underscores with single
                .replace(/^_|_$/g, "") // Remove leading/trailing underscores
            : `new_item_${Date.now()}`);

        // Validate parent_key exists in storage
        const parentExists = newItem.parent_key
          ? sensitivityStorage.some(
              (item) => item.fides_key === newItem.parent_key,
            )
          : true;

        // If parent is missing, create as root item (no console logs to satisfy lint rules)

        const completeItem: TaxonomyEntity = {
          fides_key: fidesKey,
          name: newItem.name || null,
          description: newItem.description || null,
          parent_key: parentExists ? newItem.parent_key || null : null,
          active: newItem.active !== undefined ? newItem.active : true,
          is_default:
            newItem.is_default !== undefined ? newItem.is_default : false,
        };

        sensitivityStorage.push(completeItem);
        writeStorage(sensitivityStorage);
        return res(ctx.status(201), ctx.json(completeItem));
      },
    ),
    // PUT (update) - update in storage
    rest.put(`${apiBase}/taxonomies/${taxonomyType}`, async (req, res, ctx) => {
      const updatedItem = (await req.json()) as TaxonomyEntity;
      const index = sensitivityStorage.findIndex(
        (item) => item.fides_key === updatedItem.fides_key,
      );
      if (index !== -1) {
        sensitivityStorage[index] = updatedItem;
        writeStorage(sensitivityStorage);
      }
      return res(ctx.status(200), ctx.json(updatedItem));
    }),
    // DELETE - remove from storage
    rest.delete(
      `${apiBase}/taxonomies/${taxonomyType}/:fides_key`,
      (req, res, ctx) => {
        const { fides_key: fidesKeyParam } = req.params as {
          fides_key: string;
        };
        sensitivityStorage = sensitivityStorage.filter(
          (item) => item.fides_key !== fidesKeyParam,
        );
        writeStorage(sensitivityStorage);
        return res(ctx.status(204));
      },
    ),
  ];
};
