import type {
  IntegrationNodeData,
  ManualTaskNodeData,
  PreviewEdge,
  TraversalPreviewResponse,
} from "~/features/dsr-traversal-visualizer/types";
import {
  ActionStatus,
  ActionType,
  Reachability,
} from "~/features/dsr-traversal-visualizer/types";

export const MOCK_PROPERTY_ID = "FDS-MOCKED1";

export const mockProperty = {
  id: MOCK_PROPERTY_ID,
  name: "Mocked Property",
  type: "Website",
  experiences: [],
  privacy_center_config: null,
  stylesheet: null,
  paths: [],
};

const stage1Integrations: IntegrationNodeData[] = [
  {
    id: "integration:postgres-users",
    connection_key: "postgres-users",
    connector_type: "postgres",
    system: {
      fides_key: "users_db",
      name: "Customer Database",
      data_uses: ["essential.service"],
    },
    reachability: Reachability.REACHABLE,
    action_status: ActionStatus.ACTIVE,
    collection_count: { traversed: 4, total: 4 },
    data_categories: ["user.contact.email", "user.name", "user.unique_id"],
    datasets: [
      {
        fides_key: "users_db",
        collections: [
          {
            name: "customer",
            fields: [
              {
                name: "email",
                data_categories: ["user.contact.email"],
                is_identity: true,
              },
              {
                name: "first_name",
                data_categories: ["user.name"],
                is_identity: false,
              },
              {
                name: "id",
                data_categories: ["user.unique_id"],
                is_identity: false,
              },
            ],
          },
        ],
      },
    ],
  },
  {
    id: "integration:stripe-prod",
    connection_key: "stripe-prod",
    connector_type: "saas",
    saas_type: "stripe",
    system: {
      fides_key: "stripe",
      name: "Stripe",
      data_uses: ["essential.service.payment_processing"],
    },
    reachability: Reachability.REACHABLE,
    action_status: ActionStatus.ACTIVE,
    collection_count: { traversed: 3, total: 3 },
    data_categories: ["user.contact.email", "user.financial", "user.unique_id"],
    datasets: [
      {
        fides_key: "stripe",
        collections: [
          {
            name: "customers",
            fields: [
              {
                name: "email",
                data_categories: ["user.contact.email"],
                is_identity: true,
              },
              {
                name: "id",
                data_categories: ["user.unique_id"],
                is_identity: false,
              },
            ],
          },
          {
            name: "charges",
            fields: [
              {
                name: "amount",
                data_categories: ["user.financial"],
                is_identity: false,
              },
            ],
          },
        ],
      },
    ],
  },
  {
    id: "integration:salesforce",
    connection_key: "salesforce-prod",
    connector_type: "saas",
    saas_type: "salesforce",
    system: {
      fides_key: "salesforce",
      name: "Salesforce CRM",
      data_uses: ["marketing.advertising"],
    },
    reachability: Reachability.REACHABLE,
    action_status: ActionStatus.ACTIVE,
    collection_count: { traversed: 2, total: 2 },
    data_categories: ["user.contact.email", "user.name"],
    datasets: [
      {
        fides_key: "salesforce",
        collections: [
          {
            name: "Contact",
            fields: [
              {
                name: "Email",
                data_categories: ["user.contact.email"],
                is_identity: true,
              },
            ],
          },
        ],
      },
    ],
  },
];

const stage2Integrations: IntegrationNodeData[] = [
  {
    id: "integration:warehouse",
    connection_key: "warehouse-analytics",
    connector_type: "snowflake",
    system: {
      fides_key: "warehouse",
      name: "Analytics Warehouse",
      data_uses: ["analytics"],
    },
    reachability: Reachability.REACHABLE,
    action_status: ActionStatus.ACTIVE,
    collection_count: { traversed: 2, total: 5 },
    data_categories: ["user.unique_id", "user.behavior"],
    datasets: [
      {
        fides_key: "warehouse",
        collections: [
          {
            name: "user_events",
            fields: [
              {
                name: "user_id",
                data_categories: ["user.unique_id"],
                is_identity: false,
              },
              {
                name: "event_type",
                data_categories: ["user.behavior"],
                is_identity: false,
              },
            ],
          },
          {
            name: "sessions",
            fields: [],
          },
        ],
      },
    ],
  },
  {
    id: "integration:mailchimp",
    connection_key: "mailchimp",
    connector_type: "saas",
    saas_type: "mailchimp",
    system: {
      fides_key: "mailchimp",
      name: "Mailchimp",
      data_uses: ["marketing.advertising"],
    },
    reachability: Reachability.REACHABLE,
    action_status: ActionStatus.ACTIVE,
    collection_count: { traversed: 1, total: 1 },
    data_categories: ["user.contact.email"],
    datasets: [
      {
        fides_key: "mailchimp",
        collections: [
          {
            name: "members",
            fields: [
              {
                name: "email_address",
                data_categories: ["user.contact.email"],
                is_identity: true,
              },
            ],
          },
        ],
      },
    ],
  },
];

const gatedIntegration: IntegrationNodeData = {
  id: "integration:legal-archive",
  connection_key: "legal-archive",
  connector_type: "s3",
  system: {
    fides_key: "legal_archive",
    name: "Legal Archive",
    data_uses: ["essential.legal_obligation"],
  },
  reachability: Reachability.REACHABLE,
  action_status: ActionStatus.ACTIVE,
  collection_count: { traversed: 1, total: 1 },
  data_categories: ["user.contact.email"],
  datasets: [
    {
      fides_key: "legal_archive",
      collections: [
        {
          name: "retention_records",
          fields: [
            {
              name: "subject_email",
              data_categories: ["user.contact.email"],
              is_identity: true,
            },
          ],
        },
      ],
    },
  ],
};

const skippedIntegrations: IntegrationNodeData[] = [
  {
    id: "integration:legacy-erp",
    connection_key: "legacy-erp",
    connector_type: "mssql",
    system: {
      fides_key: "legacy_erp",
      name: "Legacy ERP",
    },
    reachability: Reachability.UNREACHABLE,
    action_status: ActionStatus.SKIPPED,
    collection_count: { traversed: 0, total: 8 },
    data_categories: [],
    datasets: [],
  },
  {
    id: "integration:vendor-x",
    connection_key: "vendor-x",
    connector_type: "saas",
    saas_type: "custom",
    system: {
      fides_key: "vendor_x",
      name: "Vendor X",
    },
    reachability: Reachability.UNREACHABLE,
    action_status: ActionStatus.SKIPPED,
    collection_count: { traversed: 0, total: 2 },
    data_categories: [],
    datasets: [],
  },
];

const manualTask: ManualTaskNodeData = {
  id: "manual:legal-review",
  name: "Legal review",
  assignees: [
    { type: "team", name: "Legal & Compliance" },
    { type: "user", name: "Alex Jordan" },
  ],
  fields: [
    {
      name: "approval",
      type: "checkbox",
      label: "Confirm release authorized",
      help_text: "Required before legal archive can be accessed.",
      required: true,
    },
    {
      name: "notes",
      type: "text",
      label: "Reviewer notes",
      required: false,
    },
  ],
  conditions: [
    {
      summary: "Subject is in a regulated jurisdiction",
      expression: "subject.jurisdiction in ['EU', 'UK', 'CA']",
    },
  ],
  gates: ["integration:legal-archive"],
};

const allIntegrations = [
  ...stage1Integrations,
  ...stage2Integrations,
  gatedIntegration,
  ...skippedIntegrations,
];

const edges: PreviewEdge[] = [
  // Stage 1: identity feeds each first-stage integration
  ...stage1Integrations.map((i) => ({
    source: "identity-root",
    target: i.id,
    kind: "depends_on" as const,
    dep_count: 1,
  })),
  // Stage 2: warehouse depends on postgres + stripe; mailchimp depends on salesforce
  {
    source: "integration:postgres-users",
    target: "integration:warehouse",
    kind: "depends_on" as const,
    dep_count: 2,
  },
  {
    source: "integration:stripe-prod",
    target: "integration:warehouse",
    kind: "depends_on" as const,
    dep_count: 1,
  },
  {
    source: "integration:salesforce",
    target: "integration:mailchimp",
    kind: "depends_on" as const,
    dep_count: 1,
  },
  // Gated lane: legal archive depends on identity + is gated by manual review
  {
    source: "identity-root",
    target: "integration:legal-archive",
    kind: "depends_on" as const,
    dep_count: 1,
  },
  {
    source: "manual:legal-review",
    target: "integration:legal-archive",
    kind: "gates" as const,
  },
];

export const mockTraversalPreview: TraversalPreviewResponse = {
  property: { id: MOCK_PROPERTY_ID, name: "Mocked Property" },
  action_type: ActionType.ACCESS,
  computed_at: "2026-05-11T22:00:00Z",
  cache_hit: false,
  identity_root: {
    id: "identity-root",
    identity_types: ["email", "phone_number"],
    privacy_center_forms: [
      {
        id: "form:default",
        name: "Default DSR form",
        url_path: "/privacy-center/dsr",
      },
    ],
  },
  integrations: allIntegrations,
  manual_tasks: [manualTask],
  edges,
  warnings: [],
};
