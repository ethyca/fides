/**
 * Tree fixture for the §3 mock Schema Explorer.
 *
 * Mirrors the focal `legacy_orders_pg` dataset's collections so the left-rail
 * tree can render without any API call.
 */

export type FieldStatus = "approved" | "unlabeled" | "classified";

export interface MockField {
  name: string;
  type: string;
  status: FieldStatus;
  dataCategories: string[];
  isIdentity: boolean;
  isIdentityCandidate: boolean; // Metis suggestion
  fkRef: string | null;
  confidence: number; // 0-1
}

export interface MockCollectionDetail {
  name: string;
  fields: MockField[];
  status: "ok" | "needs-dsr-wiring" | "skipped";
  reason?: string;
}

export const MOCK_COLLECTION_DETAILS: Record<string, MockCollectionDetail> = {
  users: {
    name: "users",
    status: "needs-dsr-wiring",
    reason:
      "No identity field declared. Metis recommends `email` or `user_id`.",
    fields: [
      { name: "id", type: "integer", status: "approved", dataCategories: ["system.operations"], isIdentity: false, isIdentityCandidate: false, fkRef: null, confidence: 1.0 },
      { name: "email", type: "string", status: "classified", dataCategories: ["user.contact.email"], isIdentity: false, isIdentityCandidate: true, fkRef: null, confidence: 0.96 },
      { name: "user_id", type: "string", status: "classified", dataCategories: ["user.unique_id"], isIdentity: false, isIdentityCandidate: true, fkRef: null, confidence: 0.92 },
      { name: "first_name", type: "string", status: "approved", dataCategories: ["user.name.first"], isIdentity: false, isIdentityCandidate: false, fkRef: null, confidence: 0.88 },
      { name: "last_name", type: "string", status: "approved", dataCategories: ["user.name.last"], isIdentity: false, isIdentityCandidate: false, fkRef: null, confidence: 0.88 },
      { name: "phone", type: "string", status: "classified", dataCategories: ["user.contact.phone_number"], isIdentity: false, isIdentityCandidate: false, fkRef: null, confidence: 0.81 },
      { name: "created_at", type: "timestamp", status: "approved", dataCategories: ["system.operations"], isIdentity: false, isIdentityCandidate: false, fkRef: null, confidence: 1.0 },
      { name: "last_login_at", type: "timestamp", status: "approved", dataCategories: ["system.operations"], isIdentity: false, isIdentityCandidate: false, fkRef: null, confidence: 1.0 },
      { name: "address_id", type: "integer", status: "approved", dataCategories: ["system.operations"], isIdentity: false, isIdentityCandidate: false, fkRef: "addresses.id", confidence: 1.0 },
      { name: "metadata", type: "jsonb", status: "unlabeled", dataCategories: [], isIdentity: false, isIdentityCandidate: false, fkRef: null, confidence: 0.0 },
    ],
  },
  orders: {
    name: "orders",
    status: "ok",
    fields: [
      { name: "id", type: "integer", status: "approved", dataCategories: ["system.operations"], isIdentity: true, isIdentityCandidate: false, fkRef: null, confidence: 1.0 },
      { name: "user_id", type: "integer", status: "approved", dataCategories: ["user.unique_id"], isIdentity: false, isIdentityCandidate: false, fkRef: "users.id", confidence: 1.0 },
      { name: "total_amount", type: "decimal", status: "approved", dataCategories: ["user.financial"], isIdentity: false, isIdentityCandidate: false, fkRef: null, confidence: 0.94 },
      { name: "currency", type: "string(3)", status: "approved", dataCategories: ["system.operations"], isIdentity: false, isIdentityCandidate: false, fkRef: null, confidence: 1.0 },
      { name: "status", type: "enum", status: "approved", dataCategories: ["system.operations"], isIdentity: false, isIdentityCandidate: false, fkRef: null, confidence: 1.0 },
      { name: "placed_at", type: "timestamp", status: "approved", dataCategories: ["system.operations"], isIdentity: false, isIdentityCandidate: false, fkRef: null, confidence: 1.0 },
    ],
  },
  addresses: {
    name: "addresses",
    status: "needs-dsr-wiring",
    reason: "FK references unreachable user_id.",
    fields: [
      { name: "id", type: "integer", status: "approved", dataCategories: ["system.operations"], isIdentity: false, isIdentityCandidate: false, fkRef: null, confidence: 1.0 },
      { name: "user_id", type: "integer", status: "unlabeled", dataCategories: [], isIdentity: false, isIdentityCandidate: false, fkRef: null, confidence: 0.0 },
      { name: "line_1", type: "string", status: "approved", dataCategories: ["user.contact.address.street"], isIdentity: false, isIdentityCandidate: false, fkRef: null, confidence: 0.91 },
      { name: "city", type: "string", status: "approved", dataCategories: ["user.contact.address.city"], isIdentity: false, isIdentityCandidate: false, fkRef: null, confidence: 0.95 },
      { name: "postal_code", type: "string", status: "classified", dataCategories: ["user.contact.address.postal_code"], isIdentity: false, isIdentityCandidate: false, fkRef: null, confidence: 0.88 },
    ],
  },
};

export interface MockTreeNode {
  key: string;
  title: string;
  type: "dataset" | "collection";
  status?: "ok" | "needs-dsr-wiring" | "skipped";
  children?: MockTreeNode[];
}

export const MOCK_DATASET_TREE: MockTreeNode = {
  key: "legacy_orders_pg",
  title: "legacy_orders_pg",
  type: "dataset",
  children: [
    { key: "legacy_orders_pg.users", title: "users", type: "collection", status: "needs-dsr-wiring" },
    { key: "legacy_orders_pg.orders", title: "orders", type: "collection", status: "ok" },
    { key: "legacy_orders_pg.order_items", title: "order_items", type: "collection", status: "ok" },
    { key: "legacy_orders_pg.addresses", title: "addresses", type: "collection", status: "needs-dsr-wiring" },
    { key: "legacy_orders_pg.payments", title: "payments", type: "collection", status: "ok" },
    { key: "legacy_orders_pg.refunds", title: "refunds", type: "collection", status: "ok" },
    { key: "legacy_orders_pg.carts", title: "carts", type: "collection", status: "skipped" },
    { key: "legacy_orders_pg.audit_log", title: "audit_log", type: "collection", status: "skipped" },
    { key: "legacy_orders_pg.promotions", title: "promotions", type: "collection", status: "ok" },
    { key: "legacy_orders_pg.shipments", title: "shipments", type: "collection", status: "ok" },
    { key: "legacy_orders_pg.tax_records", title: "tax_records", type: "collection", status: "ok" },
  ],
};
