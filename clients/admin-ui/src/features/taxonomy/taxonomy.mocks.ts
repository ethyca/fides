/* eslint-disable import/no-extraneous-dependencies */
import { rest } from "msw";

import { TaxonomyEntity } from "./types";

// Seed data for system groups taxonomy
export const mockSystemGroupData: TaxonomyEntity[] = [
  {
    fides_key: "analytics_bi",
    name: "Analytics & Business Intelligence",
    description: "Systems for analytics and business intelligence",
    parent_key: null,
    active: true,
    is_default: false,
  },
  {
    fides_key: "customer_management",
    name: "Customer Management",
    description: "Systems for managing customer relationships",
    parent_key: null,
    active: true,
    is_default: false,
  },
  {
    fides_key: "internal_operations",
    name: "Internal Operations",
    description: "Systems for internal business operations",
    parent_key: null,
    active: true,
    is_default: false,
  },
  {
    fides_key: "legal_compliance",
    name: "Legal & Compliance",
    description: "Systems for legal and compliance management",
    parent_key: null,
    active: true,
    is_default: false,
  },
  {
    fides_key: "marketing",
    name: "Marketing",
    description: "Systems for marketing activities",
    parent_key: null,
    active: true,
    is_default: false,
  },
  {
    fides_key: "payments_billing",
    name: "Payments & Billing",
    description: "Systems for payment processing and billing",
    parent_key: null,
    active: true,
    is_default: false,
  },
  {
    fides_key: "product_service",
    name: "Product & Service Delivery",
    description: "Systems for product and service delivery",
    parent_key: null,
    active: true,
    is_default: false,
  },
  {
    fides_key: "research_development",
    name: "Research & Development",
    description: "Systems for research and development activities",
    parent_key: null,
    active: true,
    is_default: false,
  },
  {
    fides_key: "sales_revenue",
    name: "Sales & Revenue Operations",
    description: "Systems for sales and revenue operations",
    parent_key: null,
    active: true,
    is_default: false,
  },
  {
    fides_key: "security_fraud",
    name: "Security & Fraud",
    description: "Systems for security and fraud prevention",
    parent_key: null,
    active: true,
    is_default: false,
  },
  {
    fides_key: "customer_care",
    name: "Customer Care Global",
    description: "Global customer care and support systems",
    parent_key: null,
    active: true,
    is_default: false,
  },
  {
    fides_key: "marketing_media",
    name: "Marketing and Media Strategy - Owned",
    description: "Owned marketing and media strategy systems",
    parent_key: null,
    active: true,
    is_default: false,
  },
];

// Available dynamic taxonomies list for the UI selector
export interface AvailableTaxonomySummary {
  fides_key: string;
  name: string;
}

// Exclude system_group here; it's handled as a special core taxonomy in the UI
export const mockAvailableTaxonomies: AvailableTaxonomySummary[] = [];

// Storage helpers backed by localStorage when available (browser),
// with an in-memory fallback (Node/JSDOM).
const STORAGE_KEY = "mock_system_group_taxonomy";
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
  return [...mockSystemGroupData];
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

let systemGroupStorage = readStorage();

// Factory so tests / stories can override data
export const taxonomyHandlers = (
  initialData: TaxonomyEntity[] = mockSystemGroupData,
  taxonomyType = "system_group",
) => {
  // Initialize storage with provided data (and persist)
  systemGroupStorage = [...(hasLocalStorage ? readStorage() : initialData)];
  if (!hasLocalStorage) {
    // keep parity with old behavior in Node
    systemGroupStorage = [...initialData];
  }
  writeStorage(systemGroupStorage);

  const apiBase = "/api/v1"; // we match relative to avoid hard-coding host
  return [
    // GET - list available dynamic taxonomies
    rest.get(`${apiBase}/taxonomies`, (_req, res, ctx) =>
      res(ctx.status(200), ctx.json(mockAvailableTaxonomies)),
    ),

    // GET - return current storage
    rest.get(`${apiBase}/taxonomies/${taxonomyType}`, (_req, res, ctx) => {
      // Sort items so parents come before children using topological sort
      const sortItems = (items: typeof systemGroupStorage) => {
        const result: typeof systemGroupStorage = [];
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
          const addedInThisPass: typeof systemGroupStorage = [];

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

      const sortedItems = sortItems(systemGroupStorage);

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
          ? systemGroupStorage.some(
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

        systemGroupStorage.push(completeItem);
        writeStorage(systemGroupStorage);
        return res(ctx.status(201), ctx.json(completeItem));
      },
    ),

    // PUT (update) - update in storage
    rest.put(`${apiBase}/taxonomies/${taxonomyType}`, async (req, res, ctx) => {
      const updatedItem = (await req.json()) as TaxonomyEntity;
      const index = systemGroupStorage.findIndex(
        (item) => item.fides_key === updatedItem.fides_key,
      );
      if (index !== -1) {
        systemGroupStorage[index] = updatedItem;
        writeStorage(systemGroupStorage);
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
        systemGroupStorage = systemGroupStorage.filter(
          (item) => item.fides_key !== fidesKeyParam,
        );
        writeStorage(systemGroupStorage);
        return res(ctx.status(204));
      },
    ),
  ];
};
