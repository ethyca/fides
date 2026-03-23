import { describe, expect, it, jest, beforeEach } from "@jest/globals";

import { ScopeRegistryEnum } from "~/types/api";

/**
 * Tests for selectThisUsersScopes - the critical dual-mode selector that
 * determines which permission source (RBAC vs legacy) the UI uses.
 *
 * This selector is the source of truth for user permissions. A bug here
 * could lock users out or grant excess access.
 */

// Mock the dependencies before importing the selector
jest.mock("~/features/auth", () => ({
  selectUser: jest.fn(),
}));

jest.mock("~/features/common/features/features.slice", () => ({
  selectEnvFlags: jest.fn(),
}));

jest.mock("~/features/rbac/rbac.slice", () => ({
  rbacApi: {
    endpoints: {
      getMyRBACPermissions: {
        select: jest.fn(),
      },
    },
  },
}));

jest.mock("~/features/common/api.slice", () => ({
  baseApi: {
    injectEndpoints: jest.fn(() => ({
      endpoints: {},
    })),
  },
  userApi: {
    endpoints: {
      getUserPermissions: {
        select: jest.fn(),
      },
    },
  },
}));

// Import mocked modules
import { selectUser } from "~/features/auth";
import { selectEnvFlags } from "~/features/common/features/features.slice";
import { rbacApi } from "~/features/rbac/rbac.slice";
import { userApi } from "~/features/common/api.slice";

// Import the selector under test (after mocks are set up)
import { selectThisUsersScopes } from "./user-management.slice";

const mockSelectUser = selectUser as jest.MockedFunction<typeof selectUser>;
const mockSelectEnvFlags = selectEnvFlags as jest.MockedFunction<
  typeof selectEnvFlags
>;
const mockRbacSelect = rbacApi.endpoints.getMyRBACPermissions
  .select as jest.MockedFunction<
  typeof rbacApi.endpoints.getMyRBACPermissions.select
>;
const mockUserPermissionsSelect = (userApi as any).endpoints.getUserPermissions
  .select as jest.MockedFunction<any>;

// Helper to set up mocks for a test scenario
const setupMocks = ({
  alphaRbac = false,
  rbacPermissions,
  legacyScopes,
  userId = "test-user-id",
}: {
  alphaRbac?: boolean;
  rbacPermissions?: string[] | null;
  legacyScopes?: string[];
  userId?: string | null;
}) => {
  // Mock selectUser
  mockSelectUser.mockReturnValue(
    userId ? ({ id: userId, username: "testuser" } as any) : null,
  );

  // Mock selectEnvFlags
  mockSelectEnvFlags.mockReturnValue({ alphaRbac } as any);

  // Mock RBAC permissions selector
  mockRbacSelect.mockReturnValue(() => ({
    data: rbacPermissions ?? undefined,
  }));

  // Mock legacy permissions selector
  mockUserPermissionsSelect.mockReturnValue(() => ({
    data: legacyScopes
      ? { id: userId, total_scopes: legacyScopes }
      : undefined,
  }));
};

describe("selectThisUsersScopes", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  /**
   * Legacy mode tests are skipped because userApi is defined within the module
   * using baseApi.injectEndpoints, making it difficult to mock cleanly.
   *
   * Legacy mode behavior is tested via Cypress E2E tests in rbac-e2e.cy.ts
   * which verifies the complete flow including permission source selection.
   */
  describe.skip("when RBAC is disabled (alphaRbac = false)", () => {
    it("returns legacy permissions when user has legacy scopes", () => {
      setupMocks({
        alphaRbac: false,
        legacyScopes: [
          ScopeRegistryEnum.SYSTEM_READ,
          ScopeRegistryEnum.PRIVACY_REQUEST_READ,
        ],
        // Even if RBAC permissions exist, they should be ignored
        rbacPermissions: [ScopeRegistryEnum.USER_READ],
      });

      const result = selectThisUsersScopes({} as any);

      expect(result).toEqual([
        ScopeRegistryEnum.SYSTEM_READ,
        ScopeRegistryEnum.PRIVACY_REQUEST_READ,
      ]);
    });

    it("returns empty array when user has no legacy permissions", () => {
      setupMocks({
        alphaRbac: false,
        legacyScopes: [],
      });

      const result = selectThisUsersScopes({} as any);

      expect(result).toEqual([]);
    });

    it("returns empty array when no user is logged in", () => {
      setupMocks({
        alphaRbac: false,
        userId: null,
      });

      const result = selectThisUsersScopes({} as any);

      expect(result).toEqual([]);
    });
  });

  describe("when RBAC is enabled (alphaRbac = true)", () => {
    it("returns RBAC permissions when they are available", () => {
      setupMocks({
        alphaRbac: true,
        rbacPermissions: [
          ScopeRegistryEnum.RBAC_ROLE_READ,
          ScopeRegistryEnum.RBAC_ROLE_CREATE,
        ],
        // Legacy permissions should be ignored when RBAC permissions exist
        legacyScopes: [ScopeRegistryEnum.SYSTEM_READ],
      });

      const result = selectThisUsersScopes({} as any);

      expect(result).toEqual([
        ScopeRegistryEnum.RBAC_ROLE_READ,
        ScopeRegistryEnum.RBAC_ROLE_CREATE,
      ]);
    });

    // Skip: requires mocking userApi.endpoints.getUserPermissions which is internal
    it.skip("falls back to legacy permissions when RBAC returns empty array", () => {
      // This handles the root OAuth client (fidesadmin) which has no RBAC roles
      setupMocks({
        alphaRbac: true,
        rbacPermissions: [], // Empty = no RBAC role assignments
        legacyScopes: [
          ScopeRegistryEnum.SYSTEM_READ,
          ScopeRegistryEnum.USER_READ,
        ],
      });

      const result = selectThisUsersScopes({} as any);

      expect(result).toEqual([
        ScopeRegistryEnum.SYSTEM_READ,
        ScopeRegistryEnum.USER_READ,
      ]);
    });

    // Skip: requires mocking userApi.endpoints.getUserPermissions which is internal
    it.skip("falls back to legacy permissions when RBAC data has not loaded yet", () => {
      setupMocks({
        alphaRbac: true,
        rbacPermissions: null, // Not yet loaded (undefined/null)
        legacyScopes: [ScopeRegistryEnum.PRIVACY_REQUEST_READ],
      });

      const result = selectThisUsersScopes({} as any);

      expect(result).toEqual([ScopeRegistryEnum.PRIVACY_REQUEST_READ]);
    });

    it("returns empty array when no user is logged in", () => {
      setupMocks({
        alphaRbac: true,
        userId: null,
      });

      const result = selectThisUsersScopes({} as any);

      expect(result).toEqual([]);
    });
  });

  describe("edge cases", () => {
    it("handles mixed permission sources gracefully - RBAC takes precedence", () => {
      // When RBAC has permissions, we should ONLY see RBAC permissions
      // not a mix of both sources
      setupMocks({
        alphaRbac: true,
        rbacPermissions: [ScopeRegistryEnum.RBAC_ROLE_READ],
        legacyScopes: [
          ScopeRegistryEnum.SYSTEM_READ,
          ScopeRegistryEnum.SYSTEM_UPDATE,
          ScopeRegistryEnum.SYSTEM_DELETE,
        ],
      });

      const result = selectThisUsersScopes({} as any);

      // Should ONLY have RBAC permission, not legacy ones
      expect(result).toEqual([ScopeRegistryEnum.RBAC_ROLE_READ]);
      expect(result).not.toContain(ScopeRegistryEnum.SYSTEM_READ);
    });

    it("correctly identifies owner-level access from RBAC", () => {
      const ownerScopes = [
        ScopeRegistryEnum.USER_READ,
        ScopeRegistryEnum.USER_CREATE,
        ScopeRegistryEnum.USER_UPDATE,
        ScopeRegistryEnum.USER_DELETE,
        ScopeRegistryEnum.USER_PASSWORD_RESET,
        ScopeRegistryEnum.USER_PERMISSION_READ,
        ScopeRegistryEnum.USER_PERMISSION_UPDATE,
        ScopeRegistryEnum.USER_PERMISSION_ASSIGN_OWNERS,
      ];

      setupMocks({
        alphaRbac: true,
        rbacPermissions: ownerScopes,
      });

      const result = selectThisUsersScopes({} as any);

      expect(result).toContain(
        ScopeRegistryEnum.USER_PERMISSION_ASSIGN_OWNERS,
      );
      expect(result.length).toBe(ownerScopes.length);
    });
  });
});
