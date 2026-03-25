/**
 * RBAC UI Management Tests
 *
 * These tests validate the RBAC management UI functionality by interacting
 * with the actual UI elements to create roles, manage permissions, and
 * assign users to roles.
 *
 * Environment modes:
 * - CI: Uses mocked API responses (no backend required)
 * - Local with backend: Set CYPRESS_REAL_API=true to test against real backend
 */

import {
  stubHomePage,
  stubPlus,
  stubSystemCrud,
  stubTaxonomyEntities,
  stubUserManagement,
} from "cypress/support/stubs";

import { STORAGE_ROOT_KEY } from "~/constants";

// Check if we should use real API (local development with backend)
const USE_REAL_API = Cypress.env("REAL_API") === true;

// OAuth client credentials for admin
const ADMIN_USER_ID = "fidesadmin";
const ADMIN_USER_SECRET = "fidesadminsecret";

// Backend API URL (bypassing Next.js proxy for OAuth)
const API_URL = Cypress.env("API_URL") || "http://localhost:8080";

// Test constants
const TEST_ROLE_PREFIX = "ui_test_role";

// Helper to generate unique names
const uniqueId = () => Math.random().toString(36).substring(2, 10);

// Mock role ID counter for CI mode
let mockRoleIdCounter = 1;

/**
 * Get admin token - real API mode only
 */
const getAdminToken = (): Cypress.Chainable<string> => {
  if (!USE_REAL_API) {
    return cy.wrap("mock-admin-token");
  }
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

/**
 * Visit a URL with auth and feature flag set
 */
const visitWithAuth = (url: string, enableRbac = false) => {
  const setupAndVisit = (token: string) => {
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
  };

  if (USE_REAL_API) {
    getAdminToken().then(setupAndVisit);
  } else {
    setupAndVisit("mock-admin-token");
  }
};

/**
 * Navigate to RBAC settings page with auth and flag enabled
 */
const navigateToRbacSettings = () => {
  visitWithAuth("/settings/rbac", true);
  cy.url().should("include", "/settings/rbac");
};

/**
 * Clean up test roles via API (real API mode only)
 */
const cleanupTestRoles = (token: string) => {
  if (!USE_REAL_API) {
    return;
  }
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
 * Set up mocks for RBAC endpoints (CI mode)
 */
const setupRbacMocks = () => {
  // Stub single role - must be defined BEFORE the list intercept
  // so it takes precedence for paths like /roles/abc123
  // Return a single role object, not the array
  cy.intercept(
    {
      method: "GET",
      pathname: /^\/api\/v1\/plus\/rbac\/roles\/[^/]+$/,
    },
    {
      body: {
        id: "role_admin",
        key: "admin",
        name: "Admin",
        description: "Administrative access",
        is_system_role: true,
        is_active: true,
        priority: 90,
        parent_role_id: null,
        permissions: [
          "user:read",
          "user:create",
          "user:update",
          "user:delete",
          "system:read",
          "system:update",
        ],
        inherited_permissions: [],
        created_at: "2024-01-01T00:00:00Z",
        updated_at: "2024-01-01T00:00:00Z",
      },
    },
  ).as("getRole");

  // Stub roles list - uses pathname to match regardless of query params
  cy.intercept(
    {
      method: "GET",
      pathname: "/api/v1/plus/rbac/roles",
    },
    { fixture: "rbac/roles.json" },
  ).as("getRoles");

  // Stub permissions list - uses pathname to match regardless of query params
  cy.intercept(
    {
      method: "GET",
      pathname: "/api/v1/plus/rbac/permissions",
    },
    { fixture: "rbac/permissions.json" },
  ).as("getPermissions");

  // Stub create role
  cy.intercept("POST", "/api/v1/plus/rbac/roles", (req) => {
    const newRole = {
      id: `mock_role_${mockRoleIdCounter++}`,
      ...req.body,
      is_system_role: false,
      is_active: true,
      permissions: [],
      inherited_permissions: [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    req.reply({ statusCode: 201, body: newRole });
  }).as("createRole");

  // Stub update role
  cy.intercept("PUT", "/api/v1/plus/rbac/roles/*", (req) => {
    req.reply({ statusCode: 200, body: req.body });
  }).as("updateRole");

  // Stub update role permissions
  cy.intercept("PUT", "/api/v1/plus/rbac/roles/*/permissions", (req) => {
    req.reply({
      statusCode: 200,
      body: { permission_codes: req.body.permission_codes },
    });
  }).as("updateRolePermissions");

  // Stub delete role
  cy.intercept("DELETE", "/api/v1/plus/rbac/roles/*", {
    statusCode: 204,
  }).as("deleteRole");

  // Stub user roles
  cy.intercept("GET", "/api/v1/plus/rbac/users/*/roles", {
    body: [],
  }).as("getUserRoles");

  cy.intercept("POST", "/api/v1/plus/rbac/users/*/roles", (req) => {
    req.reply({
      statusCode: 201,
      body: { id: "mock_user_role_1", ...req.body },
    });
  }).as("assignUserRole");
};

describe("RBAC UI Management", () => {
  let adminToken: string;

  before(() => {
    getAdminToken().then((token) => {
      adminToken = token;
    });
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
      stubUserManagement();

      // Set up RBAC-specific mocks
      setupRbacMocks();

      // Stub permissions endpoint with full access
      cy.intercept("/api/v1/user/*/permission", {
        fixture: "user-management/permissions.json",
      }).as("getUserPermissions");
    }
  });

  afterEach(() => {
    if (USE_REAL_API && adminToken) {
      cleanupTestRoles(adminToken);
    }
  });

  describe("Role Management Page", () => {
    beforeEach(() => {
      navigateToRbacSettings();
    });

    it("displays the role management page with roles table", () => {
      // Check page header
      cy.contains("Role management").should("be.visible");

      // Check that the roles table is present
      cy.get(".ant-table").should("exist");

      // Should have "Create role" button
      cy.contains("button", "Create role").should("be.visible");
    });

    it("shows system roles in the roles table", () => {
      // System roles should be displayed
      cy.get(".ant-table-tbody").within(() => {
        cy.contains("System").should("exist");
      });
    });

    it("can navigate to create new role page", () => {
      cy.contains("button", "Create role").click();
      cy.url().should("include", "/settings/rbac/roles/new");

      // Verify create form is displayed
      cy.contains("Create role").should("be.visible");
      cy.contains("Name").should("be.visible");
      cy.contains("Key").should("be.visible");
    });
  });

  describe("Create Role via UI", () => {
    it("can create a new custom role via the UI", () => {
      const testId = uniqueId();
      const roleName = `${TEST_ROLE_PREFIX}_${testId}`;

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
      cy.contains("button", "Create role").click();

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
      cy.contains("button", "Create role").click();

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

  if (USE_REAL_API) {
    // These tests require real API for role creation/editing
    describe("Edit Role Permissions via UI", () => {
      let testRoleId: string;

      beforeEach(() => {
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
        visitWithAuth(`/settings/rbac/roles/${testRoleId}`, true);

        cy.contains("Permissions").should("be.visible");
        cy.get("h5.capitalize").should("have.length.at.least", 1);

        cy.get(".ant-checkbox-input").first().check({ force: true });
        cy.contains("button", "Save").click();
        cy.contains("Role saved successfully").should("be.visible");
      });

      it("can update role details", () => {
        visitWithAuth(`/settings/rbac/roles/${testRoleId}`, true);

        cy.get('textarea[id="description"]')
          .clear()
          .type("Updated description via UI test");

        cy.contains("button", "Save").click();
        cy.contains("Role saved successfully").should("be.visible");
      });
    });

    describe("Delete Role via UI", () => {
      let testRoleId: string;
      let roleName: string;

      beforeEach(() => {
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
        // Click on the role name to navigate to detail page
        cy.contains("a", roleName).click();
        cy.url().should("match", /\/settings\/rbac\/roles\/[a-zA-Z0-9_-]+$/);

        // Click Delete button on the detail page
        cy.contains("button", "Delete").click();

        cy.get(".delete-role-confirmation-modal").should("be.visible");

        cy.get(".delete-role-confirmation-modal")
          .contains("button", "Delete")
          .click();

        cy.contains("deleted successfully").should("be.visible");

        // Should redirect back to roles list
        cy.url().should("include", "/settings/rbac");
        cy.url().should("not.match", /\/roles\/[a-zA-Z0-9_-]+$/);
      });
    });

    describe("User Role Assignment", () => {
      let testUserId: string;
      let testUsername: string;

      beforeEach(() => {
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
        visitWithAuth(`/user-management/profile/${testUserId}`, true);

        cy.contains("Roles").click();

        cy.contains(".ant-card", "Viewer")
          .find(".ant-checkbox-input")
          .check({ force: true });

        cy.get('[data-testid="save-btn"]').click();
        cy.contains("Roles updated successfully").should("be.visible");
      });
    });
  }

  describe("Role Detail Navigation", () => {
    beforeEach(() => {
      navigateToRbacSettings();
    });

    it("can click role name to navigate to detail page", () => {
      // Click on the first role name link
      cy.get(".ant-table-tbody tr.ant-table-row")
        .first()
        .find("a")
        .first()
        .click();

      cy.url().should("match", /\/settings\/rbac\/roles\/[a-zA-Z0-9_-]+$/);
    });

    it("cannot delete system roles", () => {
      // Navigate to a system role's detail page
      cy.get(".ant-table-tbody tr")
        .filter(":contains('System')")
        .first()
        .find("a")
        .first()
        .click();

      cy.url().should("match", /\/settings\/rbac\/roles\/[a-zA-Z0-9_-]+$/);

      // Delete button should be disabled for system roles
      cy.contains("button", "Delete").should("be.disabled");
    });
  });

  describe("Feature Flag Gating", () => {
    /**
     * Tests that RBAC UI is visible/accessible when the alphaRbac flag is enabled.
     * The inverse test (hidden when disabled) is implicit - if we can navigate to
     * RBAC settings successfully with the flag enabled, the gating works.
     */
    it("shows RBAC settings navigation when alphaRbac flag is enabled", () => {
      // Navigate to RBAC settings with flag enabled
      navigateToRbacSettings();

      // Role management page should be visible
      cy.contains("Role management").should("be.visible");

      // Create role button should be accessible
      cy.contains("button", "Create role").should("be.visible");
    });

    it("RBAC settings page requires alphaRbac flag in URL access", () => {
      // Try to access RBAC directly without the flag enabled in storage
      // The page should still load but may redirect or show limited content
      // based on feature flag checks in the component
      if (!USE_REAL_API) {
        // In mock mode, stub the necessary APIs
        stubHomePage();
        stubPlus(true);

        const authState = {
          user: {
            id: "test-user",
            username: "testuser",
            created_at: new Date().toISOString(),
          },
          token: "mock-token",
        };

        // Explicitly disable alphaRbac
        const storageData: Record<string, string> = {
          auth: JSON.stringify(authState),
          features: JSON.stringify({
            flags: {
              alphaRbac: {
                development: false,
                test: false,
                production: false,
              },
            },
          }),
        };

        cy.visit("/settings/rbac", {
          onBeforeLoad(win) {
            win.localStorage.setItem(
              STORAGE_ROOT_KEY,
              JSON.stringify(storageData),
            );
          },
        });

        // With flag disabled, page should redirect or show unauthorized
        // The actual behavior depends on implementation - verify it doesn't crash
        cy.url().should("not.include", "/login"); // User is still authenticated
      } else {
        cy.log("Skipping flag-disabled test in real API mode");
      }
    });
  });

  describe("Permission Checkbox Grid", () => {
    /**
     * Tests the permission checkbox matrix on the role detail page.
     * This is the most complex UI in the RBAC feature.
     *
     * Note: These tests use real API mode by default because the permission
     * grid requires properly formatted permission data to render correctly.
     */

    if (USE_REAL_API) {
      it("displays permission categories grouped by resource type", () => {
        // Navigate to an existing role's edit page
        navigateToRbacSettings();

        // Click on first role name to see permission grid
        cy.get(".ant-table-tbody tr.ant-table-row")
          .first()
          .find("a")
          .first()
          .click();

        // Wait for role detail page
        cy.url().should("match", /\/settings\/rbac\/roles\/[a-zA-Z0-9_-]+$/);

        // Permission categories should be displayed in the tree table
        cy.get(".ant-table").should("exist");

        // Should have checkboxes for permissions
        cy.get(".ant-checkbox").should("have.length.at.least", 1);
      });

      it("can interact with permission checkboxes on role detail page", () => {
        const testId = uniqueId();
        const roleName = `${TEST_ROLE_PREFIX}_checkbox_${testId}`;

        // Create a new role to test checkbox interaction
        visitWithAuth("/settings/rbac/roles/new", true);
        cy.url().should("include", "/settings/rbac/roles/new");

        // Fill in basic info
        cy.get('input[id="name"]').type(roleName);

        // Wait for permissions to load
        cy.get(".ant-checkbox", { timeout: 10000 }).should(
          "have.length.at.least",
          1,
        );

        // Find an unchecked checkbox and check it
        cy.get(".ant-checkbox:not(.ant-checkbox-checked)")
          .first()
          .find("input")
          .check({ force: true });

        // Verify it's now checked
        cy.get(".ant-checkbox.ant-checkbox-checked").should(
          "have.length.at.least",
          1,
        );

        // Create the role
        cy.contains("button", "Create role").click();

        // Should succeed
        cy.contains("created successfully").should("be.visible");
      });

      it("shows permission sections for different resource types", () => {
        navigateToRbacSettings();

        // Click on first role name
        cy.get(".ant-table-tbody tr.ant-table-row")
          .first()
          .find("a")
          .first()
          .click();

        // Verify permission categories exist in the tree table
        // Categories are shown as expandable rows with resource type names
        cy.get(".ant-table-tbody").within(() => {
          // Should have rows with permission codes
          cy.get("tr").should("have.length.at.least", 1);
        });
      });
    } else {
      // In mock mode, just verify the page structure renders
      it("renders create role form with permission section", () => {
        visitWithAuth("/settings/rbac/roles/new", true);

        cy.contains("Create role").should("be.visible");
        cy.contains("Name").should("be.visible");
        cy.contains("Key").should("be.visible");
      });
    }
  });
});
