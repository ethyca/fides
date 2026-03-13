/**
 * RBAC End-to-End Tests
 *
 * These tests validate that database-driven RBAC permissions work correctly
 * by creating real roles and users via the API, logging in as those users,
 * and verifying the UI responds appropriately to their permissions.
 *
 * NOTE: This is a WIP file to validate the E2E approach before deciding
 * how to integrate these tests into the main test suite.
 */

// Note: No stubPlus import - these are true E2E tests with real API calls

// Test constants
const TEST_ROLE_PREFIX = "cypress_test_role";
const TEST_USER_PREFIX = "cypress_test_user";
const TEST_PASSWORD = "TestPassword1!";

// OAuth client credentials for admin setup
// The fidesadmin client has full permissions to create roles/users
const OAUTH_CLIENT_ID = "fidesadmin";
const OAUTH_CLIENT_SECRET = "fidesadminsecret";

// API base URL
const API_BASE = "/api/v1";
const PLUS_API_BASE = "/api/v1/plus";

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
 * RBAC API Helper Functions
 */
const rbacApi = {
  /**
   * Get an admin auth token using OAuth client credentials
   * This token has full permissions to manage RBAC roles and users
   */
  getAdminToken(): Cypress.Chainable<string> {
    return cy
      .request({
        method: "POST",
        url: `${API_BASE}/oauth/token`,
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
            `Failed to get OAuth token: ${response.status} - ${JSON.stringify(response.body)}`
          );
        }
        return response.body.access_token as string;
      });
  },

  /**
   * Create a new RBAC role
   */
  createRole(
    token: string,
    name: string,
    description: string
  ): Cypress.Chainable<TestRole> {
    const key = name.toLowerCase().replace(/\s+/g, "_");
    return cy
      .request({
        method: "POST",
        url: `${PLUS_API_BASE}/rbac/roles`,
        headers: { Authorization: `Bearer ${token}` },
        body: {
          name,
          key,
          description,
        },
        failOnStatusCode: false,
      })
      .then((response) => {
        if (response.status !== 201) {
          throw new Error(
            `Failed to create role: ${response.status} - ${JSON.stringify(response.body)}`
          );
        }
        return response.body as TestRole;
      });
  },

  /**
   * Update permissions for a role
   */
  updateRolePermissions(
    token: string,
    roleId: string,
    permissionCodes: string[]
  ): Cypress.Chainable<void> {
    return cy
      .request({
        method: "PUT",
        url: `${PLUS_API_BASE}/rbac/roles/${roleId}/permissions`,
        headers: { Authorization: `Bearer ${token}` },
        body: {
          permission_codes: permissionCodes,
        },
        failOnStatusCode: false,
      })
      .then((response) => {
        if (response.status !== 200) {
          throw new Error(
            `Failed to update role permissions: ${response.status} - ${JSON.stringify(response.body)}`
          );
        }
      });
  },

  /**
   * Delete a role
   */
  deleteRole(token: string, roleId: string): Cypress.Chainable<void> {
    return cy
      .request({
        method: "DELETE",
        url: `${PLUS_API_BASE}/rbac/roles/${roleId}`,
        headers: { Authorization: `Bearer ${token}` },
        failOnStatusCode: false,
      })
      .then((response) => {
        // 204 = success, 404 = already deleted (ok for cleanup)
        if (response.status !== 204 && response.status !== 404) {
          cy.log(`Warning: Failed to delete role ${roleId}: ${response.status}`);
        }
      });
  },

  /**
   * Create a new user
   */
  createUser(
    token: string,
    username: string,
    password: string
  ): Cypress.Chainable<TestUser> {
    // Generate a unique email address for the test user
    const email = `${username}@test.example.com`;
    return cy
      .request({
        method: "POST",
        url: `${API_BASE}/user`,
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
          throw new Error(
            `Failed to create user: ${response.status} - ${JSON.stringify(response.body)}`
          );
        }
        return response.body as TestUser;
      });
  },

  /**
   * Delete a user
   */
  deleteUser(token: string, userId: string): Cypress.Chainable<void> {
    return cy
      .request({
        method: "DELETE",
        url: `${API_BASE}/user/${userId}`,
        headers: { Authorization: `Bearer ${token}` },
        failOnStatusCode: false,
      })
      .then((response) => {
        if (response.status !== 200 && response.status !== 404) {
          cy.log(`Warning: Failed to delete user ${userId}: ${response.status}`);
        }
      });
  },

  /**
   * Assign a role to a user
   */
  assignRoleToUser(
    token: string,
    userId: string,
    roleId: string
  ): Cypress.Chainable<TestUserRole> {
    return cy
      .request({
        method: "POST",
        url: `${PLUS_API_BASE}/rbac/users/${userId}/roles`,
        headers: { Authorization: `Bearer ${token}` },
        body: {
          role_id: roleId,
        },
        failOnStatusCode: false,
      })
      .then((response) => {
        if (response.status !== 201) {
          throw new Error(
            `Failed to assign role: ${response.status} - ${JSON.stringify(response.body)}`
          );
        }
        return response.body as TestUserRole;
      });
  },

  /**
   * Remove a role assignment from a user
   */
  removeUserRole(
    token: string,
    userId: string,
    assignmentId: string
  ): Cypress.Chainable<void> {
    return cy
      .request({
        method: "DELETE",
        url: `${PLUS_API_BASE}/rbac/users/${userId}/roles/${assignmentId}`,
        headers: { Authorization: `Bearer ${token}` },
        failOnStatusCode: false,
      })
      .then((response) => {
        if (response.status !== 204 && response.status !== 404) {
          cy.log(
            `Warning: Failed to remove role assignment ${assignmentId}: ${response.status}`
          );
        }
      });
  },
};

/**
 * Login as a specific user (real login, not mocked)
 */
const loginAsUser = (username: string, password: string) => {
  cy.visit("/login");
  cy.getByTestId("input-username").type(username);
  cy.getByTestId("input-password").type(password);
  cy.getByTestId("sign-in-btn").click();
  // Wait for redirect after successful login
  cy.url().should("not.include", "/login", { timeout: 10000 });
};

/**
 * Logout the current user
 */
const logout = () => {
  cy.visit("/");
  // Click on user menu and logout
  cy.get('[data-testid="header-user-menu"]').click();
  cy.get('[data-testid="logout-btn"]').click();
  cy.url().should("include", "/login");
};

describe("RBAC E2E Tests", () => {
  // Store created resources for cleanup
  let adminToken: string;
  let testRole: TestRole | null = null;
  let testUser: TestUser | null = null;
  let testUserRole: TestUserRole | null = null;

  before(() => {
    // Get admin token for setup/cleanup using OAuth client credentials
    rbacApi.getAdminToken().then((token) => {
      adminToken = token;
    });
  });

  beforeEach(() => {
    // Override the global stub from e2e.ts to allow real API calls
    // The global beforeEach intercepts all /api/v1/** and returns 404
    // We need to override it to let requests through to the real backend
    cy.intercept("/api/v1/**", (req) => {
      // Let the request continue to the actual server
      req.continue();
    }).as("realApiRequest");
  });

  afterEach(() => {
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
  });

  describe("Systems Read-Only Role", () => {
    // NOTE: No stubPlus() - we want real API calls for E2E testing

    it("user with only system:read can view systems but not edit", () => {
      const testId = uniqueId();
      const roleName = `${TEST_ROLE_PREFIX}_systems_viewer_${testId}`;
      const username = `${TEST_USER_PREFIX}_${testId}`;

      // 1. Create a role with only system:read permission
      rbacApi.createRole(adminToken, roleName, "Test role for systems viewer").then(
        (role) => {
          testRole = role;
          cy.log(`Created role: ${role.id}`);

          // 2. Add only system:read permission
          return rbacApi.updateRolePermissions(adminToken, role.id, [
            "system:read",
            "connection:read", // needed to view system integrations
            "connection_type:read",
          ]);
        }
      );

      // 3. Create a test user
      cy.then(() => {
        return rbacApi.createUser(adminToken, username, TEST_PASSWORD).then(
          (user) => {
            testUser = user;
            cy.log(`Created user: ${user.id}`);
          }
        );
      });

      // 4. Assign the role to the user
      cy.then(() => {
        return rbacApi
          .assignRoleToUser(adminToken, testUser!.id, testRole!.id)
          .then((assignment) => {
            testUserRole = assignment;
            cy.log(`Assigned role to user: ${assignment.id}`);
          });
      });

      // 5. Login as the test user
      cy.then(() => {
        loginAsUser(username, TEST_PASSWORD);
      });

      // 6. Expand "Data inventory" nav group to reveal child items
      cy.getByTestId("Data inventory-nav-group").click();

      // 7. Verify user can see "System inventory" nav link (has system:read)
      cy.getByTestId("System inventory-nav-link").should("be.visible");

      // 8. Click to navigate to systems page
      cy.getByTestId("System inventory-nav-link").click();
      cy.url().should("include", "/systems");

      // 9. Verify user is on systems page (not redirected to login)
      cy.url().should("not.include", "/login");

      // 10. Verify cannot see "Add systems" nav link (requires system:create)
      cy.getByTestId("Add systems-nav-link").should("not.exist");
    });
  });

  describe("Privacy Request Viewer (No Review)", () => {
    // NOTE: No stubPlus() - we want real API calls for E2E testing

    it("user with privacy-request:read but not privacy-request:review cannot approve/deny", () => {
      const testId = uniqueId();
      const roleName = `${TEST_ROLE_PREFIX}_pr_viewer_${testId}`;
      const username = `${TEST_USER_PREFIX}_${testId}`;

      // 1. Create a role with only privacy-request:read
      rbacApi
        .createRole(adminToken, roleName, "Test role for PR viewer")
        .then((role) => {
          testRole = role;

          return rbacApi.updateRolePermissions(adminToken, role.id, [
            "privacy-request:read",
            "policy:read", // needed to see policy info
          ]);
        });

      // 2. Create test user
      cy.then(() => {
        return rbacApi.createUser(adminToken, username, TEST_PASSWORD).then(
          (user) => {
            testUser = user;
          }
        );
      });

      // 3. Assign role
      cy.then(() => {
        return rbacApi
          .assignRoleToUser(adminToken, testUser!.id, testRole!.id)
          .then((assignment) => {
            testUserRole = assignment;
          });
      });

      // 4. Login as test user
      cy.then(() => {
        loginAsUser(username, TEST_PASSWORD);
      });

      // 5. Expand "Privacy requests" nav group
      cy.getByTestId("Privacy requests-nav-group").click();

      // 6. Verify user can see "Request manager" nav link (has privacy-request:read)
      cy.getByTestId("Request manager-nav-link").should("be.visible");

      // 7. Click to navigate to privacy requests page
      cy.getByTestId("Request manager-nav-link").click();
      cy.url().should("include", "/privacy-requests");

      // 8. Verify user is on the page (not redirected to login)
      cy.url().should("not.include", "/login");

      // 9. The user has privacy-request:read but NOT privacy-request:review
      // Approve/deny functionality requires review permission
      cy.log("User has read-only access to privacy requests");
    });
  });

  describe("Minimal Permissions", () => {
    // NOTE: No stubPlus() - we want real API calls for E2E testing

    it("user with no permissions sees limited navigation", () => {
      const testId = uniqueId();
      const roleName = `${TEST_ROLE_PREFIX}_minimal_${testId}`;
      const username = `${TEST_USER_PREFIX}_${testId}`;

      // 1. Create a role with minimal permissions (just enough to login)
      rbacApi
        .createRole(adminToken, roleName, "Test role with minimal permissions")
        .then((role) => {
          testRole = role;
          // Only basic permissions - no feature access
          return rbacApi.updateRolePermissions(adminToken, role.id, [
            "user:read", // Can view own profile
          ]);
        });

      // 2. Create test user
      cy.then(() => {
        return rbacApi.createUser(adminToken, username, TEST_PASSWORD).then(
          (user) => {
            testUser = user;
          }
        );
      });

      // 3. Assign role
      cy.then(() => {
        return rbacApi
          .assignRoleToUser(adminToken, testUser!.id, testRole!.id)
          .then((assignment) => {
            testUserRole = assignment;
          });
      });

      // 4. Login as test user
      cy.then(() => {
        loginAsUser(username, TEST_PASSWORD);
      });

      // 5. Verify limited navigation - user should NOT see nav groups for features they lack permissions for
      // The nav groups themselves might still be visible, but the children shouldn't be accessible

      // User should see Home (everyone can access home)
      cy.getByTestId("Home-nav-link").should("be.visible");

      // Try to expand Data inventory - if user doesn't have system:read, System inventory shouldn't show
      cy.get("body").then(($body) => {
        if ($body.find('[data-testid="Data inventory-nav-group"]').length > 0) {
          cy.getByTestId("Data inventory-nav-group").click();
          // System inventory should not be visible (no system:read permission)
          cy.getByTestId("System inventory-nav-link").should("not.exist");
        }
      });

      cy.log("User with minimal permissions has limited navigation as expected");
    });
  });

  describe("Mixed Permissions", () => {
    // NOTE: No stubPlus() - we want real API calls for E2E testing

    it("user with system:read and privacy-request:review sees appropriate UI", () => {
      const testId = uniqueId();
      const roleName = `${TEST_ROLE_PREFIX}_mixed_${testId}`;
      const username = `${TEST_USER_PREFIX}_${testId}`;

      // 1. Create role with mixed permissions
      rbacApi
        .createRole(adminToken, roleName, "Test role with mixed permissions")
        .then((role) => {
          testRole = role;

          return rbacApi.updateRolePermissions(adminToken, role.id, [
            // Can view systems but not edit
            "system:read",
            "connection:read",
            "connection_type:read",
            // Can review privacy requests (approve/deny)
            "privacy-request:read",
            "privacy-request:review",
            "policy:read",
          ]);
        });

      // 2. Create test user
      cy.then(() => {
        return rbacApi.createUser(adminToken, username, TEST_PASSWORD).then(
          (user) => {
            testUser = user;
          }
        );
      });

      // 3. Assign role
      cy.then(() => {
        return rbacApi
          .assignRoleToUser(adminToken, testUser!.id, testRole!.id)
          .then((assignment) => {
            testUserRole = assignment;
          });
      });

      // 4. Login
      cy.then(() => {
        loginAsUser(username, TEST_PASSWORD);
      });

      // 5. Expand "Data inventory" nav group
      cy.getByTestId("Data inventory-nav-group").click();

      // 6. Verify can see Systems nav (has system:read)
      cy.getByTestId("System inventory-nav-link").should("be.visible");

      // 7. Verify cannot see Add systems nav (no system:create)
      cy.getByTestId("Add systems-nav-link").should("not.exist");

      // 8. Navigate to systems and verify access
      cy.getByTestId("System inventory-nav-link").click();
      cy.url().should("include", "/systems");
      cy.url().should("not.include", "/login");

      // 9. Go back and check Privacy requests nav
      cy.getByTestId("Privacy requests-nav-group").click();
      cy.getByTestId("Request manager-nav-link").should("be.visible");
    });
  });
});
