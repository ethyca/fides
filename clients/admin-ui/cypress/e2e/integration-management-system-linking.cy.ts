import {
  stubIntegrationManagement,
  stubPlus,
  stubSystemCrud,
} from "cypress/support/stubs";

import { INTEGRATION_MANAGEMENT_ROUTE } from "~/features/common/nav/routes";

const INTEGRATION_DETAIL_URL = `${INTEGRATION_MANAGEMENT_ROUTE}/bq_integration`;
const LINKED_SYSTEMS_TAB_URL = `${INTEGRATION_DETAIL_URL}#linked-systems`;

describe("Integration management system linking", () => {
  beforeEach(() => {
    cy.login();
    stubPlus(true);
    stubIntegrationManagement();
    stubSystemCrud();

    cy.intercept("GET", "/api/v1/connection/*/test", {
      statusCode: 200,
      body: { test_status: "succeeded" },
    }).as("testConnection");
  });

  describe("Linked system tab", () => {
    beforeEach(() => {
      cy.intercept("GET", "/api/v1/connection/*/system-links", {
        fixture: "integration-management/system-links/empty.json",
      }).as("getSystemLinks");
      cy.visit(LINKED_SYSTEMS_TAB_URL);
      cy.wait("@getSystemLinks");
    });

    it("shows the linked systems tab content when navigating via hash", () => {
      cy.contains("h5", "Linked systems").should("exist");
      cy.contains(
        "Link a system to automatically surface discovered assets and enable DSR execution within the system you manage.",
      ).should("exist");
      cy.getByTestId("link-system-button").should("exist").and("be.enabled");
      cy.getByTestId("linked-systems-list").should("exist");
      cy.getByTestId("no-systems-linked-text").should("exist");
    });

    it("opens the link-system modal when clicking Link system", () => {
      cy.getByTestId("link-system-button").click();
      cy.getByTestId("link-system-modal").should("be.visible");
      cy.getByTestId("link-system-search").should("exist");
      cy.getByTestId("cancel-link-system-button").should("exist");
      cy.wait("@getSystemsPaginated");
      cy.getByTestId("link-system-modal").within(() => {
        cy.get("li").should("have.length.greaterThan", 0);
      });
    });

    it("can link a system and shows it in the list", () => {
      cy.intercept("PUT", "/api/v1/connection/*/system-links", {
        statusCode: 200,
        body: {
          system_fides_key: "demo_analytics_system",
          system_name: "Demo Analytics System",
          created_at: "2024-05-24T13:35:57.509826+00:00",
        },
      }).as("setSystemLinks");
      cy.intercept("GET", "/api/v1/connection/*/system-links", {
        fixture: "integration-management/system-links/one-link.json",
      }).as("getSystemLinksAfterLink");

      cy.getByTestId("link-system-button").click();
      cy.wait("@getSystemsPaginated");
      cy.getByTestId("link-system-option-demo_analytics_system").click();
      cy.wait("@setSystemLinks");
      cy.wait("@getSystemLinksAfterLink");

      cy.contains("System linked successfully").should("exist");
      cy.getByTestId("linked-systems-list").within(() => {
        cy.contains("Demo Analytics System").should("exist");
        cy.getByTestId("unlink-demo_analytics_system").should("exist");
      });
    });
  });

  describe("when an integration has a linked system", () => {
    beforeEach(() => {
      cy.intercept("GET", "/api/v1/connection/*/system-links", {
        fixture: "integration-management/system-links/one-link.json",
      }).as("getSystemLinks");
      cy.visit(LINKED_SYSTEMS_TAB_URL);
      cy.wait("@getSystemLinks");
    });

    it("can unlink a system after confirming", () => {
      cy.intercept("DELETE", "/api/v1/connection/*/system-links/*", {
        statusCode: 204,
      }).as("deleteSystemLink");
      cy.intercept("GET", "/api/v1/connection/*/system-links", {
        fixture: "integration-management/system-links/empty.json",
      }).as("getSystemLinksAfterUnlink");

      cy.getByTestId("unlink-demo_analytics_system").click();
      cy.contains("Unlink system").should("exist");
      cy.get(".ant-modal-content").within(() => {
        cy.contains("button", "Unlink").click({ force: true });
      });
      cy.wait("@deleteSystemLink");
      cy.wait("@getSystemLinksAfterUnlink");

      cy.contains("System unlinked successfully").should("exist");
      cy.getByTestId("no-systems-linked-text").should("exist");
      cy.getByTestId("link-system-button").should("be.enabled");
    });
  });

  describe("link-system modal search", () => {
    beforeEach(() => {
      cy.intercept("GET", "/api/v1/connection/*/system-links", {
        fixture: "integration-management/system-links/empty.json",
      }).as("getSystemLinks");
      cy.visit(LINKED_SYSTEMS_TAB_URL);
      cy.wait("@getSystemLinks");
      cy.getByTestId("link-system-button").click();
      cy.wait("@getSystemsPaginated");
    });

    it("shows empty message when search has no matches", () => {
      cy.intercept(
        {
          method: "GET",
          pathname: "/api/v1/system",
          query: { page: "1", size: "25", search: "nonexistent" },
        },
        { body: { items: [], total: 0, page: 1, size: 25, pages: 0 } },
      ).as("getSystemsSearch");
      cy.getByTestId("link-system-search").type("nonexistent");
      cy.wait("@getSystemsSearch");
      cy.contains("No matching systems. Try a different search.").should(
        "exist",
      );
    });
  });
});
