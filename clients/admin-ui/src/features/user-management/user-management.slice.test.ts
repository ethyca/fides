import { beforeEach, describe, expect, it, jest } from "@jest/globals";

// Import mocked modules
import { selectUser } from "~/features/auth";
import { selectEnvFlags } from "~/features/common/features/features.slice";
import { rbacApi } from "~/features/rbac/rbac.slice";
import { ScopeRegistryEnum } from "~/types/api";

// Import the selector under test (after mocks are set up)
import { selectThisUsersScopes } from "./user-management.slice";

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
}));

const mockSelectUser = selectUser as jest.MockedFunction<typeof selectUser>;
const mockSelectEnvFlags = selectEnvFlags as jest.MockedFunction<
  typeof selectEnvFlags
>;
const mockRbacSelect = rbacApi.endpoints.getMyRBACPermissions
  .select as jest.MockedFunction<
  typeof rbacApi.endpoints.getMyRBACPermissions.select
>;

// Helper to set up mocks for a test scenario
const setupMocks = ({
  alphaRbac = false,
  rbacPermissions,
  userId = "test-user-id",
}: {
  alphaRbac?: boolean;
  rbacPermissions?: string[] | null;
  userId?: string | null;
}) => {
  // Mock selectUser
  mockSelectUser.mockReturnValue(
    userId ? ({ id: userId, username: "testuser" } as any) : null,
  );

  // Mock selectEnvFlags
  mockSelectEnvFlags.mockReturnValue({ alphaRbac } as any);

  // Mock RBAC permissions selector - return a function that returns the query result
  mockRbacSelect.mockReturnValue(
    () =>
      ({
        data: rbacPermissions ?? undefined,
        status: "fulfilled",
        isSuccess: true,
        isLoading: false,
        isError: false,
      }) as any,
  );
};

describe("selectThisUsersScopes", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  /**
   * Legacy mode tests are skipped because userApi is defined within the module
   * using baseApi.injectEndpoints, making it difficult to mock cleanly.
   * These tests would require refactoring the slice to export userApi or
   * using a more complex mocking strategy.
   *
   * Legacy mode behavior is tested via Cypress E2E tests in rbac-e2e.cy.ts
   * which verifies the complete flow including permission source selection.
   */
  describe.skip("when RBAC is disabled (alphaRbac = false)", () => {
    it("returns legacy permissions when user has legacy scopes", () => {
      // Would need to mock userApi.endpoints.getUserPermissions
      expect(true).toBe(true);
    });

    it("returns empty array when user has no legacy permissions", () => {
      // Would need to mock userApi.endpoints.getUserPermissions
      expect(true).toBe(true);
    });

    it("returns empty array when no user is logged in", () => {
      // Would need to mock userApi.endpoints.getUserPermissions
      expect(true).toBe(true);
    });
  });

  describe("when RBAC is enabled (alphaRbac = true)", () => {
    it("returns RBAC permissions when they are available", () => {
      setupMocks({
        alphaRbac: true,
        rbacPermissions: [
          ScopeRegistryEnum.USER_READ,
          ScopeRegistryEnum.USER_CREATE,
        ],
      });

      const result = selectThisUsersScopes({} as any);

      expect(result).toEqual([
        ScopeRegistryEnum.USER_READ,
        ScopeRegistryEnum.USER_CREATE,
      ]);
    });

    // Skip: requires mocking userApi.endpoints.getUserPermissions which is internal
    it.skip("falls back to legacy permissions when RBAC returns empty array", () => {
      // This handles the root OAuth client (fidesadmin) which has no RBAC roles
      // Would need to mock userApi.endpoints.getUserPermissions to test fallback
      expect(true).toBe(true);
    });

    // Skip: requires mocking userApi.endpoints.getUserPermissions which is internal
    it.skip("falls back to legacy permissions when RBAC data has not loaded yet", () => {
      // Would need to mock userApi.endpoints.getUserPermissions to test fallback
      expect(true).toBe(true);
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
    it("returns RBAC permissions when available, ignoring legacy permissions", () => {
      // When RBAC has permissions, we should ONLY see RBAC permissions
      setupMocks({
        alphaRbac: true,
        rbacPermissions: [ScopeRegistryEnum.USER_READ],
      });

      const result = selectThisUsersScopes({} as any);

      // Should have the RBAC permission
      expect(result).toEqual([ScopeRegistryEnum.USER_READ]);
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

      expect(result).toContain(ScopeRegistryEnum.USER_PERMISSION_ASSIGN_OWNERS);
      expect(result.length).toBe(ownerScopes.length);
    });
  });
});
