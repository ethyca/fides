import { rest } from "msw";

import { systemGroupHandlers } from "~/features/system-groups/system-groups.mocks";
import { taxonomyHandlers } from "~/features/taxonomy/taxonomy.mocks";

interface SubjectRequestBody {
  username: string;
}

const mockSubjectRequestPreviewResponse = {
  items: [
    {
      status: "error",
      identity: {
        email: "james.braithwaite@email.com",
      },
      created_at: "August 4, 2021, 09:35:46 PST",
      reviewed_by: "Sammie_Shanahan@gmail.com",
      id: "123",
    },
    {
      status: "denied",
      identity: {
        phone: "555-325-685-126",
      },
      created_at: "August 4, 2021, 09:35:46 PST",
      reviewed_by: "Richmond33@yahoo.com",
      id: "456",
    },
    {
      status: "pending",
      identity: {
        email: "mary.jane.@email.com",
      },
      created_at: "August 4, 2021, 09:35:46 PST",
      reviewed_by: "Oceane.Volkman@gmail.com",
      id: "789",
    },
    {
      status: "new",
      identity: {
        email: "jeremiah.stones@email.com",
      },
      created_at: "August 4, 2021, 09:35:46 PST",
      reviewed_by: "Verdie64@yahoo.com",
      id: "012",
    },
    {
      status: "completed",
      identity: {
        phone: "283-774-5003",
      },
      created_at: "August 4, 2021, 09:35:46 PST",
      reviewed_by: "Maximo_Willms0@gmail.com",
      id: "345",
    },
  ],
};

// Mock user permissions to enable taxonomy editing
const mockUserPermissions = {
  roles: ["owner"],
  id: "fidesadmin",
  user_id: "fidesadmin",
  total_scopes: [
    // Comprehensive scopes list (same as backend owner) + system_group scopes
    "cli-objects:create",
    "cli-objects:delete",
    "cli-objects:read",
    "cli-objects:update",
    "client:create",
    "client:delete",
    "client:read",
    "client:update",
    "config:read",
    "config:update",
    "connection:authorize",
    "connection:create_or_update",
    "connection:delete",
    "connection:instantiate",
    "connection:read",
    "connection_type:read",
    "connector_template:register",
    "consent:read",
    "consent_settings:read",
    "consent_settings:update",
    "ctl_dataset:create",
    "ctl_dataset:delete",
    "ctl_dataset:read",
    "ctl_dataset:update",
    "ctl_policy:create",
    "ctl_policy:delete",
    "ctl_policy:read",
    "ctl_policy:update",
    "current-privacy-preference:read",
    "data_category:create",
    "data_category:delete",
    "data_category:read",
    "data_category:update",
    "data_subject:create",
    "data_subject:delete",
    "data_subject:read",
    "data_subject:update",
    "data_use:create",
    "data_use:delete",
    "data_use:read",
    "data_use:update",
    "database:reset",
    "dataset:create_or_update",
    "dataset:delete",
    "dataset:read",
    "dataset:test",
    "encryption:exec",
    "evaluation:create",
    "evaluation:delete",
    "evaluation:read",
    "evaluation:update",
    "fides_taxonomy:update",
    "generate:exec",
    "masking:exec",
    "masking:read",
    "messaging-template:update",
    "messaging:create_or_update",
    "messaging:delete",
    "messaging:read",
    "organization:create",
    "organization:delete",
    "organization:read",
    "organization:update",
    "policy:create_or_update",
    "policy:delete",
    "policy:read",
    "privacy-experience:create",
    "privacy-experience:read",
    "privacy-experience:update",
    "privacy-notice:create",
    "privacy-notice:read",
    "privacy-notice:update",
    "privacy-preference-history:read",
    "privacy-request-access-results:read",
    "privacy-request-email-integrations:send",
    "privacy-request-notifications:create_or_update",
    "privacy-request-notifications:read",
    "privacy-request:create",
    "privacy-request:delete",
    "privacy-request:manual-steps:respond",
    "privacy-request:manual-steps:review",
    "privacy-request:read",
    "privacy-request:resume",
    "privacy-request:review",
    "privacy-request:transfer",
    "privacy-request:upload_data",
    "privacy-request:view_data",
    "rule:create_or_update",
    "rule:delete",
    "rule:read",
    "saas_config:create_or_update",
    "saas_config:delete",
    "saas_config:read",
    "scope:read",
    "storage:create_or_update",
    "storage:delete",
    "storage:read",
    "system:create",
    "system:delete",
    "system:read",
    "system:update",
    "system_manager:delete",
    "system_manager:read",
    "system_manager:update",
    "taxonomy:create",
    "taxonomy:delete",
    "taxonomy:update",
    "user-permission:assign_owners",
    "user-permission:create",
    "user-permission:read",
    "user-permission:update",
    "user:create",
    "user:delete",
    "user:password-reset",
    "user:read",
    "user:read-own",
    "user:update",
    "validate:exec",
    "webhook:create_or_update",
    "webhook:delete",
    "webhook:read",
    "worker-stats:read",
    // --- System group taxonomy scopes ---
    "system_group:create",
    "system_group:read",
    "system_group:update",
    "system_group:delete",
  ],
};

// eslint-disable-next-line import/prefer-default-export
export const handlers = [
  ...taxonomyHandlers(),
  ...systemGroupHandlers(),

  // Mock user permissions endpoint
  rest.get("/api/v1/user/:userId/permission", (_req, res, ctx) =>
    res(ctx.status(200), ctx.json(mockUserPermissions)),
  ),

  rest.get<SubjectRequestBody>(
    "http://localhost:8080/api/v1/privacy-request",
    async (req, res, ctx) => {
      // mock loading response
      await new Promise((resolve) => {
        setTimeout(() => resolve(null), 1000);
      });

      return res(ctx.json(mockSubjectRequestPreviewResponse));
    },
  ),
];
