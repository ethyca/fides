/**
 * Root User Access Tests
 *
 * These tests verify that the root user (fidesadmin) has full access to all
 * navigation elements and features.
 *
 * This is a critical regression test to ensure root user access is never broken.
 *
 * Note: The root user (fidesadmin) is an OAuth client, not a FidesUser, so it
 * authenticates via client_credentials OAuth flow rather than username/password.
 */

import { STORAGE_ROOT_KEY } from "~/constants";

// OAuth client credentials for root user
const ROOT_USER_ID = "fidesadmin";
const ROOT_USER_SECRET = "fidesadminsecret";

// Backend API URL (bypassing Next.js proxy for OAuth)
const API_URL = Cypress.env("API_URL") || "http://localhost:8080";

/**
 * Get OAuth access token for root user using client_credentials flow
 */
const getRootUserToken = (): Cypress.Chainable<string> => {
  return cy
    .request({
      method: "POST",
      url: `${API_URL}/api/v1/oauth/token`,
      form: true,
      body: {
        grant_type: "client_credentials",
        client_id: ROOT_USER_ID,
        client_secret: ROOT_USER_SECRET,
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
};

/**
 * Authenticate as the root user by setting up auth state in localStorage
 */
const authenticateAsRootUser = () => {
  getRootUserToken().then((token) => {
    cy.window().then((win) => {
      const authState = {
        user: {
          id: ROOT_USER_ID,
          username: ROOT_USER_ID,
          created_at: new Date().toISOString(),
        },
        token,
      };
      win.localStorage.setItem(
        STORAGE_ROOT_KEY,
        JSON.stringify({
          auth: JSON.stringify(authState),
        }),
      );
    });
  });
};

/**
 * Login as the root user - sets up auth state and navigates to home
 */
const loginAsRootUser = () => {
  authenticateAsRootUser();
  cy.visit("/");
  // Wait for page to load and not redirect to login
  cy.url().should("not.include", "/login", { timeout: 10000 });
};

describe("Root User Access", () => {
  beforeEach(() => {
    // Override the global stub to allow real API calls
    cy.intercept("/api/v1/**", (req) => {
      req.continue();
    }).as("realApiRequest");
  });

  describe("Authentication", () => {
    it("root user can authenticate via OAuth and access the app", () => {
      loginAsRootUser();

      // Should be on home page after login
      cy.getByTestId("Home").should("exist");
      cy.url().should("eq", Cypress.config().baseUrl + "/");
    });

    it("root user receives full permissions from API", () => {
      getRootUserToken().then((token) => {
        // The permissions endpoint should return all scopes for root user
        cy.request({
          method: "GET",
          url: `${API_URL}/api/v1/user/${ROOT_USER_ID}/permission`,
          headers: { Authorization: `Bearer ${token}` },
          failOnStatusCode: false,
        }).then((response) => {
          expect(response.status).to.eq(200);

          // Root user should have total_scopes populated
          const { total_scopes } = response.body;
          expect(total_scopes).to.be.an("array");
          expect(total_scopes.length).to.be.greaterThan(0);

          // Verify some critical scopes are present
          expect(total_scopes).to.include("user:read");
          expect(total_scopes).to.include("system:read");
          expect(total_scopes).to.include("privacy-request:read");
        });
      });
    });
  });

  describe("Full Navigation Access", () => {
    beforeEach(() => {
      loginAsRootUser();
    });

    it("can see and expand Overview nav group", () => {
      cy.getByTestId("Overview-nav-group").should("be.visible").click();
      cy.getByTestId("Home-nav-link").should("be.visible");
    });

    it("can see and expand Data inventory nav group with all links", () => {
      cy.getByTestId("Data inventory-nav-group").should("be.visible").click();

      // Root user should see all data inventory links
      cy.getByTestId("System inventory-nav-link").should("be.visible");
      cy.getByTestId("Add systems-nav-link").should("be.visible");
      cy.getByTestId("Manage datasets-nav-link").should("be.visible");
    });

    it("can see and expand Privacy requests nav group", () => {
      cy.getByTestId("Privacy requests-nav-group").should("be.visible").click();
      cy.getByTestId("Request manager-nav-link").should("be.visible");
    });

    it("can see and expand Settings nav group with all links", () => {
      cy.getByTestId("Settings-nav-group").should("be.visible").click();

      cy.getByTestId("Privacy requests-nav-link").should("be.visible");
      cy.getByTestId("Users-nav-link").should("be.visible");
      cy.getByTestId("Organization-nav-link").should("be.visible");
      cy.getByTestId("About Fides-nav-link").should("be.visible");
    });

    it("can see Core configuration nav group", () => {
      cy.getByTestId("Core configuration-nav-group")
        .should("be.visible")
        .click();
      cy.getByTestId("Taxonomy-nav-link").should("be.visible");
    });
  });

  describe("Full Page Access", () => {
    beforeEach(() => {
      loginAsRootUser();
    });

    it("can navigate to System inventory page", () => {
      cy.getByTestId("Data inventory-nav-group").click();
      cy.getByTestId("System inventory-nav-link").click();
      cy.url().should("include", "/systems");
      // Should see the systems management page, not be redirected
      cy.getByTestId("system-management").should("exist");
    });

    it("can navigate to Add systems page", () => {
      cy.getByTestId("Data inventory-nav-group").click();
      cy.getByTestId("Add systems-nav-link").click();
      cy.url().should("include", "/add-systems");
      // Should not be redirected to login or 403
      cy.url().should("not.include", "/login");
    });

    it("can navigate to Privacy requests page", () => {
      cy.getByTestId("Privacy requests-nav-group").click();
      cy.getByTestId("Request manager-nav-link").click();
      cy.url().should("include", "/privacy-requests");
      cy.url().should("not.include", "/login");
    });

    it("can navigate to User management page", () => {
      cy.getByTestId("Settings-nav-group").click();
      cy.getByTestId("Users-nav-link").click();
      cy.url().should("include", "/user-management");
      cy.getByTestId("User Management").should("exist");
    });

    it("can navigate to Taxonomy page", () => {
      cy.getByTestId("Core configuration-nav-group").click();
      cy.getByTestId("Taxonomy-nav-link").click();
      cy.url().should("include", "/taxonomy");
      cy.url().should("not.include", "/login");
    });

    it("can navigate to Datasets page", () => {
      cy.getByTestId("Data inventory-nav-group").click();
      cy.getByTestId("Manage datasets-nav-link").click();
      cy.url().should("include", "/dataset");
      cy.url().should("not.include", "/login");
    });
  });
});
