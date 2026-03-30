/**
 * Root User Access Tests
 *
 * These tests verify that the root user (fidesadmin) has full access to all
 * navigation elements and features.
 *
 * This is a critical regression test to ensure root user access is never broken.
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
} from "cypress/support/stubs";

import { STORAGE_ROOT_KEY } from "~/constants";

// Check if we should use real API (local development with backend)
// Set CYPRESS_REAL_API=true when running locally with a backend
const USE_REAL_API = Cypress.env("REAL_API") === true;

// OAuth client credentials for root user (used in real API mode)
const ROOT_USER_ID = "fidesadmin";
const ROOT_USER_SECRET = "fidesadminsecret";
const API_URL = Cypress.env("API_URL") || "http://localhost:8080";

/**
 * Get OAuth access token for root user using client_credentials flow
 * Only used when USE_REAL_API is true
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
 * Setup auth state for root user in localStorage
 */
const setupRootUserAuth = (token: string) => {
  const authState = {
    user: {
      id: ROOT_USER_ID,
      username: ROOT_USER_ID,
      created_at: new Date().toISOString(),
    },
    token,
  };
  cy.window().then((win) => {
    win.localStorage.setItem(
      STORAGE_ROOT_KEY,
      JSON.stringify({
        auth: JSON.stringify(authState),
      }),
    );
  });
};

/**
 * Login as root user - handles both mocked and real API modes
 */
const loginAsRootUser = () => {
  if (USE_REAL_API) {
    // Real API mode: get actual OAuth token
    getRootUserToken().then((token) => {
      setupRootUserAuth(token);
      cy.visit("/");
      cy.url().should("not.include", "/login", { timeout: 10000 });
    });
  } else {
    // Mock mode: use a fake token and set up auth state
    setupRootUserAuth("mock-root-user-token");
    cy.visit("/");
    cy.url().should("not.include", "/login", { timeout: 10000 });
  }
};

describe("Root User Access", () => {
  beforeEach(() => {
    if (USE_REAL_API) {
      // Real API mode: let requests through to backend
      cy.intercept("/api/v1/**", (req) => {
        req.continue();
      }).as("realApiRequest");
    } else {
      // Mock mode: use standard stubs
      stubHomePage();
      stubSystemCrud();
      stubPlus(true); // Enable plus features
      stubTaxonomyEntities();

      // Stub permissions endpoint with full access
      cy.intercept("/api/v1/user/*/permission", {
        fixture: "user-management/permissions.json",
      }).as("getPermissions");

      // Stub other endpoints needed for navigation
      cy.intercept("GET", "/api/v1/privacy-request*", {
        body: { items: [], total: 0, page: 1, size: 25, pages: 1 },
      }).as("getPrivacyRequests");

      cy.intercept("GET", "/api/v1/plus/custom-asset/logo", {
        statusCode: 404,
      }).as("getLogo");
    }
  });

  describe("Authentication", () => {
    it("root user can authenticate and access the app", () => {
      loginAsRootUser();

      // Should be on home page after login
      cy.getByTestId("Home").should("exist");
      cy.url().should("eq", Cypress.config().baseUrl + "/");
    });

    if (USE_REAL_API) {
      it("root user receives full permissions from API", () => {
        getRootUserToken().then((token) => {
          cy.request({
            method: "GET",
            url: `${API_URL}/api/v1/user/${ROOT_USER_ID}/permission`,
            headers: { Authorization: `Bearer ${token}` },
            failOnStatusCode: false,
          }).then((response) => {
            expect(response.status).to.eq(200);
            const { total_scopes } = response.body;
            expect(total_scopes).to.be.an("array");
            expect(total_scopes.length).to.be.greaterThan(0);
            expect(total_scopes).to.include("user:read");
            expect(total_scopes).to.include("system:read");
            expect(total_scopes).to.include("privacy-request:read");
          });
        });
      });
    }
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

    it("can see Settings nav group with Taxonomy", () => {
      cy.getByTestId("Settings-nav-group").should("be.visible").click();
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
      cy.url().should("not.include", "/login");
    });

    it("can navigate to Add systems page", () => {
      cy.getByTestId("Data inventory-nav-group").click();
      cy.getByTestId("Add systems-nav-link").click();
      cy.url().should("include", "/add-systems");
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
      cy.url().should("not.include", "/login");
    });

    it("can navigate to Taxonomy page", () => {
      cy.getByTestId("Settings-nav-group").click();
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
