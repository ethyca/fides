/* eslint-disable import/no-extraneous-dependencies */
import { rest } from "msw";

import { TaxonomyEntity } from "~/features/taxonomy/types";

// Seed data for System Groups taxonomy
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

export interface AvailableTaxonomySummary {
  fides_key: string;
  name: string;
}

export const mockAvailableSystemTaxonomies: AvailableTaxonomySummary[] = [];

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
      /* ignore */
    }
  }
  return [...mockSystemGroupData];
};

const writeStorage = (data: TaxonomyEntity[]) => {
  if (hasLocalStorage) {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
    } catch {
      /* ignore */
    }
  }
};

let systemGroupStorage = readStorage();

export const systemGroupHandlers = (
  initialData: TaxonomyEntity[] = mockSystemGroupData,
) => {
  systemGroupStorage = [...(hasLocalStorage ? readStorage() : initialData)];
  if (!hasLocalStorage) {
    systemGroupStorage = [...initialData];
  }
  writeStorage(systemGroupStorage);

  const apiBase = "/api/v1";

  const sortItems = (items: typeof systemGroupStorage) => {
    const result: typeof systemGroupStorage = [];
    const remaining = [...items];
    const roots = remaining.filter((i) => i.parent_key === null);
    roots.sort((a, b) => a.fides_key.localeCompare(b.fides_key));
    result.push(...roots);
    remaining.splice(
      0,
      remaining.length,
      ...remaining.filter((i) => i.parent_key !== null),
    );
    while (remaining.length) {
      const added: typeof systemGroupStorage = [];
      for (let i = remaining.length - 1; i >= 0; i -= 1) {
        const item = remaining[i];
        if (result.some((p) => p.fides_key === item.parent_key)) {
          added.push(item);
          remaining.splice(i, 1);
        }
      }
      if (!added.length) {
        result.push(...remaining);
        break;
      }
      added.sort((a, b) => a.fides_key.localeCompare(b.fides_key));
      result.push(...added);
    }
    return result;
  };

  return [
    rest.get(`${apiBase}/system_group`, (_req, res, ctx) =>
      res(ctx.status(200), ctx.json(sortItems(systemGroupStorage))),
    ),

    rest.post(`${apiBase}/system_group`, async (req, res, ctx) => {
      const newItem = (await req.json()) as Partial<TaxonomyEntity>;
      const fidesKey =
        newItem.fides_key ||
        (newItem.name
          ? newItem.name.toLowerCase().replace(/[^a-z0-9]/g, "_")
          : `sys_${Date.now()}`);
      const completeItem: TaxonomyEntity = {
        fides_key: fidesKey,
        name: newItem.name || null,
        description: newItem.description || null,
        parent_key: newItem.parent_key || null,
        active: newItem.active !== undefined ? newItem.active : true,
        is_default: false,
      };
      systemGroupStorage.push(completeItem);
      writeStorage(systemGroupStorage);
      return res(ctx.status(201), ctx.json(completeItem));
    }),

    rest.put(`${apiBase}/system_group`, async (req, res, ctx) => {
      const updated = (await req.json()) as TaxonomyEntity;
      const idx = systemGroupStorage.findIndex(
        (i) => i.fides_key === updated.fides_key,
      );
      if (idx !== -1) {
        systemGroupStorage[idx] = updated;
        writeStorage(systemGroupStorage);
      }
      return res(ctx.status(200), ctx.json(updated));
    }),

    rest.delete(`${apiBase}/system_group/:fides_key`, (req, res, ctx) => {
      const { fides_key: fidesKey } = req.params as { fides_key: string };
      systemGroupStorage = systemGroupStorage.filter(
        (i) => i.fides_key !== fidesKey,
      );
      writeStorage(systemGroupStorage);
      return res(ctx.status(204));
    }),
  ];
};
