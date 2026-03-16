/**
 * RBAC End-to-End Tests
 *
 * These tests validate that RBAC permissions work correctly by verifying
 * the UI responds appropriately to user permissions.
 *
 * Environment modes:
 * - CI: Uses mocked API responses to simulate different permission sets
 * - Local with backend: Set CYPRESS_REAL_API=true to test with real users/roles
 */

import {
  stubHomePage,
  stubPlus,
  stubSystemCrud,
  stubTaxonomyEntities,
} from "cypress/support/stubs";

import { STORAGE_ROOT_KEY } from "~/constants";

// Check if we should use real API (local development with backend)
const USE_REAL_API = Cypress.env("REAL_API") === true;

// Test constants
const TEST_ROLE_PREFIX = "cypress_test_role";
const TEST_USER_PREFIX = "cypress_test_user";
const TEST_PASSWORD = "TestPassword1!";

// OAuth client credentials for admin setup (real API mode)
const OAUTH_CLIENT_ID = "fidesadmin";
const OAUTH_CLIENT_SECRET = "fidesadminsecret";

// Backend API URL
const API_URL = Cypress.env("API_URL") || "http://localhost:8080";

// Helper to generate unique names
const uniqueId = () => Math.random().toString(36).substring(2, 10);

interface TestRole {
  id: string;
  name: string;
  key: string;
}

interface TestUser {
  id: string;
  username: string;
}

interface TestUserRole {
  id: string;
}

/**
 * Permission sets for mock testing
 */
const PERMISSION_SETS = {
  systemsViewer: {
    id: "test-user-systems-viewer",
    total_scopes: ["system:read", "connection:read", "connection_type:read"],
  },
  privacyRequestViewer: {
    id: "test-user-pr-viewer",
    total_scopes: ["privacy-request:read", "policy:read"],
  },
  minimal: {
    id: "test-user-minimal",
    total_scopes: ["user:read"],
  },
  mixed: {
    id: "test-user-mixed",
    total_scopes: [
      "system:read",
      "connection:read",
      "connection_type:read",
      "privacy-request:read",
      "privacy-request:review",
      "policy:read",
    ],
  },
};

/**
 * Setup mocked auth state and visit a URL
 */
const loginWithPermissions = (permissionSet: keyof typeof PERMISSION_SETS) => {
  const permissions = PERMISSION_SETS[permissionSet];

  // Set up auth state
  const authState = {
    user: {
      id: permissions.id,
      username: `test_${permissionSet}`,
      created_at: new Date().toISOString(),
    },
    token: "mock-token",
  };

  cy.window().then((win) => {
    win.localStorage.setItem(
      STORAGE_ROOT_KEY,
      JSON.stringify({
        auth: JSON.stringify(authState),
      }),
    );
  });

  // Intercept permissions endpoint for this user
  cy.intercept("/api/v1/user/*/permission", {
    body: permissions,
  }).as("getPermissions");

  cy.visit("/");
  cy.url().should("not.include", "/login", { timeout: 10000 });
};

/**
 * RBAC API Helper Functions (real API mode only)
 */
const rbacApi = {
  getAdminToken(): Cypress.Chainable<string> {
    return cy
      .request({
        method: "POST",
        url: `${API_URL}/api/v1/oauth/token`,
        form: true,
        body: {
          grant_type: "client_credentials",
          client_id: OAUTH_CLIENT_ID,
          client_secret: OAUTH_CLIENT_SECRET,
        },
        failOnStatusCode: false,
      })
      .then((response) => {
        if (response.status !== 200) {
          throw new Error(
            `Failed to get OAuth token: ${response.status} - ${JSON.stringify(response.body)}`,
          );
        }
        return response.body.access_token as string;
      });
  },

  createRole(
    token: string,
    name: string,
    description: string,
  ): Cypress.Chainable<TestRole> {
    const key = name.toLowerCase().replace(/\s+/g, "_");
    return cy
      .request({
        method: "POST",
        url: `${API_URL}/api/v1/plus/rbac/roles`,
        headers: { Authorization: `Bearer ${token}` },
        body: { name, key, description },
        failOnStatusCode: false,
      })
      .then((response) => {
        if (response.status !== 201) {
          throw new Error(
            `Failed to create role: ${response.status} - ${JSON.stringify(response.body)}`,
          );
        }
        return response.body as TestRole;
      });
  },

  updateRolePermissions(
    token: string,
    roleId: string,
    permissionCodes: string[],
  ): Cypress.Chainable<void> {
    return cy
      .request({
        method: "PUT",
        url: `${API_URL}/api/v1/plus/rbac/roles/${roleId}/permissions`,
        headers: { Authorization: `Bearer ${token}` },
        body: { permission_codes: permissionCodes },
        failOnStatusCode: false,
      })
      .then((response) => {
        if (response.status !== 200) {
          throw new Error(
            `Failed to update role permissions: ${response.status}`,
          );
        }
      });
  },

  deleteRole(token: string, roleId: string): Cypress.Chainable<void> {
    return cy
      .request({
        method: "DELETE",
        url: `${API_URL}/api/v1/plus/rbac/roles/${roleId}`,
        headers: { Authorization: `Bearer ${token}` },
        failOnStatusCode: false,
      })
      .then(() => {});
  },

  createUser(
    token: string,
    username: string,
    password: string,
  ): Cypress.Chainable<TestUser> {
    const email = `${username}@test.example.com`;
    return cy
      .request({
        method: "POST",
        url: `${API_URL}/api/v1/user`,
        headers: { Authorization: `Bearer ${token}` },
        body: {
          username,
          password,
          email_address: email,
          first_name: "Test",
          last_name: "User",
        },
        failOnStatusCode: false,
      })
      .then((response) => {
        if (response.status !== 201 && response.status !== 200) {
          throw new Error(`Failed to create user: ${response.status}`);
        }
        return response.body as TestUser;
      });
  },

  deleteUser(token: string, userId: string): Cypress.Chainable<void> {
    return cy
      .request({
        method: "DELETE",
        url: `${API_URL}/api/v1/user/${userId}`,
        headers: { Authorization: `Bearer ${token}` },
        failOnStatusCode: false,
      })
      .then(() => {});
  },

  assignRoleToUser(
    token: string,
    userId: string,
    roleId: string,
  ): Cypress.Chainable<TestUserRole> {
    return cy
      .request({
        method: "POST",
        url: `${API_URL}/api/v1/plus/rbac/users/${userId}/roles`,
        headers: { Authorization: `Bearer ${token}` },
        body: { role_id: roleId },
        failOnStatusCode: false,
      })
      .then((response) => {
        if (response.status !== 201) {
          throw new Error(`Failed to assign role: ${response.status}`);
        }
        return response.body as TestUserRole;
      });
  },

  removeUserRole(
    token: string,
    userId: string,
    assignmentId: string,
  ): Cypress.Chainable<void> {
    return cy
      .request({
        method: "DELETE",
        url: `${API_URL}/api/v1/plus/rbac/users/${userId}/roles/${assignmentId}`,
        headers: { Authorization: `Bearer ${token}` },
        failOnStatusCode: false,
      })
      .then(() => {});
  },
};

/**
 * Login as a specific user (real API mode)
 */
const loginAsUser = (username: string, password: string) => {
  cy.visit("/login");
  cy.getByTestId("input-username").type(username);
  cy.getByTestId("input-password").type(password);
  cy.getByTestId("sign-in-btn").click();
  cy.url().should("not.include", "/login", { timeout: 10000 });
};

describe("RBAC E2E Tests", () => {
  // Variables for real API mode
  let adminToken: string;
  let testRole: TestRole | null = null;
  let testUser: TestUser | null = null;
  let testUserRole: TestUserRole | null = null;

  before(() => {
    if (USE_REAL_API) {
      rbacApi.getAdminToken().then((token) => {
        adminToken = token;
      });
    }
  });

  beforeEach(() => {
    if (USE_REAL_API) {
      // Real API mode: let requests through to backend
      cy.intercept("/api/v1/**", (req) => {
        req.continue();
      }).as("realApiRequest");
    } else {
      // Mock mode: set up standard stubs
      stubHomePage();
      stubSystemCrud();
      stubPlus(true);
      stubTaxonomyEntities();

      // Stub privacy requests for navigation
      cy.intercept("GET", "/api/v1/privacy-request*", {
        body: { items: [], total: 0, page: 1, size: 25, pages: 1 },
      }).as("getPrivacyRequests");

      cy.intercept("GET", "/api/v1/plus/custom-asset/logo", {
        statusCode: 404,
      }).as("getLogo");
    }
  });

  afterEach(() => {
    if (USE_REAL_API) {
      // Cleanup after each test
      if (testUserRole && testUser && adminToken) {
        rbacApi.removeUserRole(adminToken, testUser.id, testUserRole.id);
        testUserRole = null;
      }
      if (testUser && adminToken) {
        rbacApi.deleteUser(adminToken, testUser.id);
        testUser = null;
      }
      if (testRole && adminToken) {
        rbacApi.deleteRole(adminToken, testRole.id);
        testRole = null;
      }
    }
  });

  describe("Systems Read-Only Role", () => {
    it("user with only system:read can view systems but not edit", () => {
      if (USE_REAL_API) {
        // Real API: Create actual role and user
        const testId = uniqueId();
        const roleName = `${TEST_ROLE_PREFIX}_systems_viewer_${testId}`;
        const username = `${TEST_USER_PREFIX}_${testId}`;

        rbacApi
          .createRole(adminToken, roleName, "Test role for systems viewer")
          .then((role) => {
            testRole = role;
            return rbacApi.updateRolePermissions(adminToken, role.id, [
              "system:read",
              "connection:read",
              "connection_type:read",
            ]);
          });

        cy.then(() => {
          return rbacApi
            .createUser(adminToken, username, TEST_PASSWORD)
            .then((user) => {
              testUser = user;
            });
        });

        cy.then(() => {
          return rbacApi
            .assignRoleToUser(adminToken, testUser!.id, testRole!.id)
            .then((assignment) => {
              testUserRole = assignment;
            });
        });

        cy.then(() => {
          loginAsUser(username, TEST_PASSWORD);
        });
      } else {
        // Mock mode: simulate user with systems viewer permissions
        loginWithPermissions("systemsViewer");
      }

      // Verify navigation
      cy.getByTestId("Data inventory-nav-group").click();
      cy.getByTestId("System inventory-nav-link").should("be.visible");
      cy.getByTestId("System inventory-nav-link").click();
      cy.url().should("include", "/systems");
      cy.url().should("not.include", "/login");
      cy.getByTestId("Add systems-nav-link").should("not.exist");
    });
  });

  describe("Privacy Request Viewer (No Review)", () => {
    it("user with privacy-request:read but not review has limited access", () => {
      if (USE_REAL_API) {
        const testId = uniqueId();
        const roleName = `${TEST_ROLE_PREFIX}_pr_viewer_${testId}`;
        const username = `${TEST_USER_PREFIX}_${testId}`;

        rbacApi
          .createRole(adminToken, roleName, "Test role for PR viewer")
          .then((role) => {
            testRole = role;
            return rbacApi.updateRolePermissions(adminToken, role.id, [
              "privacy-request:read",
              "policy:read",
            ]);
          });

        cy.then(() => {
          return rbacApi
            .createUser(adminToken, username, TEST_PASSWORD)
            .then((user) => {
              testUser = user;
            });
        });

        cy.then(() => {
          return rbacApi
            .assignRoleToUser(adminToken, testUser!.id, testRole!.id)
            .then((assignment) => {
              testUserRole = assignment;
            });
        });

        cy.then(() => {
          loginAsUser(username, TEST_PASSWORD);
        });
      } else {
        loginWithPermissions("privacyRequestViewer");
      }

      cy.getByTestId("Privacy requests-nav-group").click();
      cy.getByTestId("Request manager-nav-link").should("be.visible");
      cy.getByTestId("Request manager-nav-link").click();
      cy.url().should("include", "/privacy-requests");
      cy.url().should("not.include", "/login");
    });
  });

  describe("Minimal Permissions", () => {
    it("user with minimal permissions sees limited navigation", () => {
      if (USE_REAL_API) {
        const testId = uniqueId();
        const roleName = `${TEST_ROLE_PREFIX}_minimal_${testId}`;
        const username = `${TEST_USER_PREFIX}_${testId}`;

        rbacApi
          .createRole(
            adminToken,
            roleName,
            "Test role with minimal permissions",
          )
          .then((role) => {
            testRole = role;
            return rbacApi.updateRolePermissions(adminToken, role.id, [
              "user:read",
            ]);
          });

        cy.then(() => {
          return rbacApi
            .createUser(adminToken, username, TEST_PASSWORD)
            .then((user) => {
              testUser = user;
            });
        });

        cy.then(() => {
          return rbacApi
            .assignRoleToUser(adminToken, testUser!.id, testRole!.id)
            .then((assignment) => {
              testUserRole = assignment;
            });
        });

        cy.then(() => {
          loginAsUser(username, TEST_PASSWORD);
        });
      } else {
        loginWithPermissions("minimal");
      }

      // User should see Home
      cy.getByTestId("Home-nav-link").should("be.visible");

      // System inventory should not be accessible
      cy.get("body").then(($body) => {
        if ($body.find('[data-testid="Data inventory-nav-group"]').length > 0) {
          cy.getByTestId("Data inventory-nav-group").click();
          cy.getByTestId("System inventory-nav-link").should("not.exist");
        }
      });
    });
  });

  describe("Mixed Permissions", () => {
    it("user with mixed permissions sees appropriate UI", () => {
      if (USE_REAL_API) {
        const testId = uniqueId();
        const roleName = `${TEST_ROLE_PREFIX}_mixed_${testId}`;
        const username = `${TEST_USER_PREFIX}_${testId}`;

        rbacApi
          .createRole(adminToken, roleName, "Test role with mixed permissions")
          .then((role) => {
            testRole = role;
            return rbacApi.updateRolePermissions(adminToken, role.id, [
              "system:read",
              "connection:read",
              "connection_type:read",
              "privacy-request:read",
              "privacy-request:review",
              "policy:read",
            ]);
          });

        cy.then(() => {
          return rbacApi
            .createUser(adminToken, username, TEST_PASSWORD)
            .then((user) => {
              testUser = user;
            });
        });

        cy.then(() => {
          return rbacApi
            .assignRoleToUser(adminToken, testUser!.id, testRole!.id)
            .then((assignment) => {
              testUserRole = assignment;
            });
        });

        cy.then(() => {
          loginAsUser(username, TEST_PASSWORD);
        });
      } else {
        loginWithPermissions("mixed");
      }

      // Can see Systems
      cy.getByTestId("Data inventory-nav-group").click();
      cy.getByTestId("System inventory-nav-link").should("be.visible");

      // Cannot see Add systems
      cy.getByTestId("Add systems-nav-link").should("not.exist");

      // Can navigate to systems
      cy.getByTestId("System inventory-nav-link").click();
      cy.url().should("include", "/systems");
      cy.url().should("not.include", "/login");

      // Can see Privacy requests
      cy.getByTestId("Privacy requests-nav-group").click();
      cy.getByTestId("Request manager-nav-link").should("be.visible");
    });
  });
});
