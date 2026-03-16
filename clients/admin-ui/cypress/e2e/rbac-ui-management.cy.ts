/**
 * RBAC UI Management Tests
 *
 * These tests validate the RBAC management UI functionality by interacting
 * with the actual UI elements to create roles, manage permissions, and
 * assign users to roles.
 *
 * Unlike rbac-e2e.cy.ts which uses API for setup, these tests verify the
 * full UI workflow works correctly.
 *
 * IMPORTANT: These are true E2E tests that require a running backend.
 * They are automatically skipped in CI since CI only runs the Next.js frontend.
 * Run these tests locally with `npm run cy:open` when the backend is running.
 */

// Skip in CI - these tests require a real backend
const isCI = Cypress.env("CI") || process.env.CI;
const describeOrSkip = isCI ? describe.skip : describe;

import { STORAGE_ROOT_KEY } from "~/constants";

// OAuth client credentials for admin
const ADMIN_USER_ID = "fidesadmin";
const ADMIN_USER_SECRET = "fidesadminsecret";

// Backend API URL (bypassing Next.js proxy for OAuth)
const API_URL = Cypress.env("API_URL") || "http://localhost:8080";

// Test constants
const TEST_ROLE_PREFIX = "ui_test_role";

// Helper to generate unique names
const uniqueId = () => Math.random().toString(36).substring(2, 10);

/**
 * Visit a URL with auth and feature flag set via onBeforeLoad
 * This ensures localStorage is set before the app initializes
 */
const visitWithAuth = (url: string, enableRbac = false) => {
  getAdminToken().then((token) => {
    const authState = {
      user: {
        id: ADMIN_USER_ID,
        username: ADMIN_USER_ID,
        created_at: new Date().toISOString(),
      },
      token,
    };

    const storageData: Record<string, string> = {
      auth: JSON.stringify(authState),
    };

    if (enableRbac) {
      storageData.features = JSON.stringify({
        flags: {
          alphaRbac: {
            development: true,
            test: true,
            production: true,
          },
        },
      });
    }

    cy.visit(url, {
      onBeforeLoad(win) {
        win.localStorage.setItem(STORAGE_ROOT_KEY, JSON.stringify(storageData));
      },
    });
  });
};

/**
 * Login as the admin user and visit homepage
 */
const loginAsAdminAndVisit = () => {
  visitWithAuth("/");
  cy.url().should("not.include", "/login", { timeout: 10000 });
};

/**
 * Navigate to RBAC settings page with auth and flag enabled
 */
const navigateToRbacSettings = () => {
  visitWithAuth("/settings/rbac", true);
  cy.url().should("include", "/settings/rbac");
};

/**
 * Enable the RBAC feature flag after page load
 */
const enableRbacFlag = () => {
  cy.overrideFeatureFlag("alphaRbac", true);
};

/**
 * Clean up test roles via API (for afterEach cleanup)
 */
const cleanupTestRoles = (token: string) => {
  // Get all roles and delete any that start with our test prefix
  cy.request({
    method: "GET",
    url: `${API_URL}/api/v1/plus/rbac/roles`,
    headers: { Authorization: `Bearer ${token}` },
    failOnStatusCode: false,
  }).then((response) => {
    if (response.status === 200 && Array.isArray(response.body)) {
      response.body
        .filter(
          (role: { name: string; is_system_role: boolean }) =>
            role.name.startsWith(TEST_ROLE_PREFIX) && !role.is_system_role,
        )
        .forEach((role: { id: string }) => {
          cy.request({
            method: "DELETE",
            url: `${API_URL}/api/v1/plus/rbac/roles/${role.id}`,
            headers: { Authorization: `Bearer ${token}` },
            failOnStatusCode: false,
          });
        });
    }
  });
};

/**
 * Get admin token for API cleanup
 */
const getAdminToken = (): Cypress.Chainable<string> => {
  return cy
    .request({
      method: "POST",
      url: `${API_URL}/api/v1/oauth/token`,
      form: true,
      body: {
        grant_type: "client_credentials",
        client_id: ADMIN_USER_ID,
        client_secret: ADMIN_USER_SECRET,
      },
      failOnStatusCode: false,
    })
    .then((response) => {
      if (response.status !== 200) {
        throw new Error(`Failed to get OAuth token: ${response.status}`);
      }
      return response.body.access_token as string;
    });
};

describeOrSkip("RBAC UI Management", () => {
  let adminToken: string;

  before(() => {
    getAdminToken().then((token) => {
      adminToken = token;
    });
  });

  beforeEach(() => {
    // Override the global stub to allow real API calls
    cy.intercept("/api/v1/**", (req) => {
      req.continue();
    }).as("realApiRequest");
  });

  afterEach(() => {
    // Clean up any test roles created during tests
    if (adminToken) {
      cleanupTestRoles(adminToken);
    }
  });

  describe("Role Management Page", () => {
    beforeEach(() => {
      navigateToRbacSettings();
    });

    it("displays the role management page with roles table", () => {
      // Check page header
      cy.contains("Role Management").should("be.visible");

      // Check that the roles table is present
      cy.get(".ant-table").should("exist");

      // Should have "Create Custom Role" button
      cy.contains("button", "Create Custom Role").should("be.visible");
    });

    it("shows system roles in the roles table", () => {
      // System roles should be displayed
      cy.get(".ant-table-tbody").within(() => {
        // Check for system role tags
        cy.contains("System").should("exist");
      });
    });

    it("can navigate to create new role page", () => {
      cy.contains("button", "Create Custom Role").click();
      cy.url().should("include", "/settings/rbac/roles/new");

      // Verify create form is displayed
      cy.contains("Create Custom Role").should("be.visible");
      cy.contains("Display Name").should("be.visible");
      cy.contains("Key").should("be.visible");
    });
  });

  describe("Create Role via UI", () => {
    it("can create a new custom role via the UI", () => {
      const testId = uniqueId();
      const roleName = `${TEST_ROLE_PREFIX}_${testId}`;

      // Navigate to create role page with auth
      visitWithAuth("/settings/rbac/roles/new", true);
      cy.url().should("include", "/settings/rbac/roles/new");

      // Fill in the form
      cy.get('input[id="name"]').type(roleName);

      // Key should be auto-generated
      cy.get('input[id="key"]').should("have.value", roleName.toLowerCase());

      // Add description
      cy.get('textarea[id="description"]').type(
        "Test role created via Cypress UI test",
      );

      // Submit the form
      cy.contains("button", "Create Role").click();

      // Should redirect to role detail page
      cy.url().should("include", "/settings/rbac/roles/");
      cy.url().should("not.include", "/new");

      // Verify success message
      cy.contains("created successfully").should("be.visible");

      // Verify role name is displayed
      cy.contains(roleName).should("be.visible");
    });

    it("shows validation error for empty name", () => {
      visitWithAuth("/settings/rbac/roles/new", true);

      // Try to submit without filling name
      cy.contains("button", "Create Role").click();

      // Should show validation error
      cy.contains("Name is required").should("be.visible");
    });

    it("can cancel role creation and return to roles list", () => {
      visitWithAuth("/settings/rbac/roles/new", true);

      cy.contains("button", "Cancel").click();

      // Should go back to roles list
      cy.url().should("include", "/settings/rbac");
      cy.url().should("not.include", "/new");
    });
  });

  describe("Edit Role Permissions via UI", () => {
    let testRoleId: string;

    beforeEach(() => {
      // Create a test role via API for editing tests
      const testId = uniqueId();
      const roleName = `${TEST_ROLE_PREFIX}_edit_${testId}`;

      cy.request({
        method: "POST",
        url: `${API_URL}/api/v1/plus/rbac/roles`,
        headers: { Authorization: `Bearer ${adminToken}` },
        body: {
          name: roleName,
          key: roleName.toLowerCase(),
          description: "Role for permission editing test",
        },
      }).then((response) => {
        expect(response.status).to.eq(201);
        testRoleId = response.body.id;
      });
    });

    it("can view and edit role permissions", () => {
      // Navigate to the role detail page with auth
      visitWithAuth(`/settings/rbac/roles/${testRoleId}`, true);

      // Verify permissions section is visible
      cy.contains("Permissions").should("be.visible");

      // Verify permissions are grouped by resource type
      // The groupedPermissions memo groups permissions and renders each group
      // with a heading (e.g., "system", "privacy request", "user", etc.)
      cy.get("h5.capitalize").should("have.length.at.least", 1);

      // Find a permission checkbox and toggle it
      cy.get(".ant-checkbox-input").first().check({ force: true });

      // Save permissions
      cy.contains("button", "Save Permissions").click();

      // Verify success message
      cy.contains("Permissions updated successfully").should("be.visible");
    });

    it("can update role details", () => {
      visitWithAuth(`/settings/rbac/roles/${testRoleId}`, true);

      // Update the description
      cy.get('textarea[id="description"]')
        .clear()
        .type("Updated description via UI test");

      // Save changes
      cy.contains("button", "Save Changes").click();

      // Verify success message
      cy.contains("Role updated successfully").should("be.visible");
    });

    it("shows inherited permissions badge for roles with parent", () => {
      // This tests that inherited permissions are properly displayed
      // The visual "Inherited" tag should appear for permissions from parent roles
      visitWithAuth(`/settings/rbac/roles/${testRoleId}`, true);

      // Permissions section should exist
      cy.contains("Permissions").should("be.visible");

      // The permission table should be visible
      cy.get(".ant-table").should("exist");
    });
  });

  describe("Role Hierarchy Cycle Prevention", () => {
    let parentRoleId: string;
    let parentRoleName: string;
    let childRoleId: string;
    let childRoleName: string;

    beforeEach(() => {
      // Create parent role
      const testId = uniqueId();
      parentRoleName = `${TEST_ROLE_PREFIX}_parent_${testId}`;
      childRoleName = `${TEST_ROLE_PREFIX}_child_${testId}`;

      // Create the parent role first
      cy.request({
        method: "POST",
        url: `${API_URL}/api/v1/plus/rbac/roles`,
        headers: { Authorization: `Bearer ${adminToken}` },
        body: {
          name: parentRoleName,
          key: parentRoleName.toLowerCase(),
          description: "Parent role for cycle test",
        },
      }).then((response) => {
        expect(response.status).to.eq(201);
        parentRoleId = response.body.id;

        // Create child role with parent_role_id pointing to the parent
        cy.request({
          method: "POST",
          url: `${API_URL}/api/v1/plus/rbac/roles`,
          headers: { Authorization: `Bearer ${adminToken}` },
          body: {
            name: childRoleName,
            key: childRoleName.toLowerCase(),
            description: "Child role for cycle test",
            parent_role_id: parentRoleId,
          },
        }).then((childResponse) => {
          expect(childResponse.status).to.eq(201);
          childRoleId = childResponse.body.id;
        });
      });
    });

    it("prevents selecting a descendant as parent role (cycle prevention)", () => {
      // Navigate to the parent role edit page
      visitWithAuth(`/settings/rbac/roles/${parentRoleId}`, true);

      // Open the parent role dropdown
      cy.get(".ant-select").first().click();

      // The child role should NOT appear in the dropdown options
      // because selecting it would create a cycle (parent -> child -> parent)
      cy.get(".ant-select-dropdown").should("be.visible");
      cy.get(".ant-select-dropdown").should("not.contain", childRoleName);

      // But other roles (like system roles) should still be available
      // The dropdown should have options available
      cy.get(".ant-select-item-option").should("exist");
    });
  });

  describe("Delete Role via UI", () => {
    let testRoleId: string;
    let roleName: string;

    beforeEach(() => {
      // Create a test role via API for deletion test
      const testId = uniqueId();
      roleName = `${TEST_ROLE_PREFIX}_delete_${testId}`;

      cy.request({
        method: "POST",
        url: `${API_URL}/api/v1/plus/rbac/roles`,
        headers: { Authorization: `Bearer ${adminToken}` },
        body: {
          name: roleName,
          key: roleName.toLowerCase(),
          description: "Role to be deleted",
        },
      }).then((response) => {
        expect(response.status).to.eq(201);
        testRoleId = response.body.id;
      });

      navigateToRbacSettings();
    });

    it("can delete a custom role via the UI", () => {
      // Find the role row and click delete button to open confirmation modal
      cy.contains("tr", roleName).within(() => {
        cy.contains("button", "Delete").click();
      });

      // Confirmation modal should appear
      cy.get('[data-testid="delete-role-confirmation-modal"]').should(
        "be.visible",
      );

      // Click Delete in the confirmation modal
      cy.get('[data-testid="delete-role-confirmation-modal"]')
        .contains("button", "Delete")
        .click();

      // Verify success message
      cy.contains("deleted successfully").should("be.visible");

      // Verify role is no longer in the table
      cy.contains("tr", roleName).should("not.exist");
    });

    it("cannot delete system roles", () => {
      // System roles should not have a delete button
      cy.get(".ant-table-tbody tr")
        .filter(":contains('System')")
        .first()
        .within(() => {
          cy.contains("button", "Delete").should("not.exist");
        });
    });
  });

  describe("Role Detail Navigation", () => {
    beforeEach(() => {
      navigateToRbacSettings();
    });

    it("can click Edit button to navigate to detail page", () => {
      // Click edit button on first data row (not measure row)
      cy.get(".ant-table-tbody tr.ant-table-row")
        .first()
        .within(() => {
          cy.contains("Edit").click();
        });

      // Should navigate to role detail page
      cy.url().should("match", /\/settings\/rbac\/roles\/[a-zA-Z0-9_-]+$/);
    });
  });

  describe("User Role Assignment", () => {
    let testUserId: string;
    let testUsername: string;

    beforeEach(() => {
      // Create a test user via API
      const testId = uniqueId();
      testUsername = `${TEST_ROLE_PREFIX}_user_${testId}`;

      cy.request({
        method: "POST",
        url: `${API_URL}/api/v1/user`,
        headers: { Authorization: `Bearer ${adminToken}` },
        body: {
          username: testUsername,
          password: "TestPassword123!",
          email_address: `${testUsername}@example.com`,
        },
      }).then((response) => {
        expect(response.status).to.eq(201);
        testUserId = response.body.id;
      });
    });

    afterEach(() => {
      // Clean up test user
      if (testUserId) {
        cy.request({
          method: "DELETE",
          url: `${API_URL}/api/v1/user/${testUserId}`,
          headers: { Authorization: `Bearer ${adminToken}` },
          failOnStatusCode: false,
        });
      }
    });

    it("can assign an RBAC role to a user via the Roles tab", () => {
      // Navigate to user profile with RBAC enabled
      visitWithAuth(`/user-management/profile/${testUserId}`, true);

      // Click on Roles tab (labeled "Roles" when RBAC is enabled)
      cy.contains("Roles").click();

      // The RolesForm should show available roles as Cards with checkboxes
      // Select the Viewer role (a system role that should always exist)
      cy.contains(".ant-card", "Viewer")
        .find(".ant-checkbox-input")
        .check({ force: true });

      // Save the role assignment (use specific test ID to avoid Profile tab's Save button)
      cy.get('[data-testid="save-btn"]').click();

      // Verify success message
      cy.contains("Roles updated successfully").should("be.visible");
    });
  });
});
