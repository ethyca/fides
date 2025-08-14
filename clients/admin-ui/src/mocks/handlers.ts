import { rest } from "msw";

import { taxonomyHandlers } from "~/features/taxonomy/taxonomy.mocks";
import { RoleRegistryEnum, ScopeRegistryEnum } from "~/types/api";

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
  id: "root_user_id",
  user_id: "root_user_id",
  total_scopes: [
    ScopeRegistryEnum.DATA_CATEGORY_CREATE,
    ScopeRegistryEnum.DATA_CATEGORY_READ,
    ScopeRegistryEnum.DATA_CATEGORY_UPDATE,
    ScopeRegistryEnum.DATA_CATEGORY_DELETE,
    ScopeRegistryEnum.DATA_USE_CREATE,
    ScopeRegistryEnum.DATA_USE_READ,
    ScopeRegistryEnum.DATA_USE_UPDATE,
    ScopeRegistryEnum.DATA_USE_DELETE,
    ScopeRegistryEnum.DATA_SUBJECT_CREATE,
    ScopeRegistryEnum.DATA_SUBJECT_READ,
    ScopeRegistryEnum.DATA_SUBJECT_UPDATE,
    ScopeRegistryEnum.DATA_SUBJECT_DELETE,
    ScopeRegistryEnum.SYSTEM_GROUP_CREATE,
    ScopeRegistryEnum.SYSTEM_GROUP_READ,
    ScopeRegistryEnum.SYSTEM_GROUP_UPDATE,
    ScopeRegistryEnum.SYSTEM_GROUP_DELETE,
    ScopeRegistryEnum.TAXONOMY_CREATE,
    ScopeRegistryEnum.TAXONOMY_UPDATE,
    ScopeRegistryEnum.TAXONOMY_DELETE,
  ],
  roles: [RoleRegistryEnum.OWNER],
};

// eslint-disable-next-line import/prefer-default-export
export const handlers = [
  ...taxonomyHandlers(),

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
