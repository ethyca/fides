import { stubPlus, stubSystemCrud } from "cypress/support/stubs";

import { INTEGRATION_MANAGEMENT_ROUTE } from "~/features/common/nav/v2/routes";

describe("Integration management for data detection & discovery", () => {
  beforeEach(() => {
    cy.login();
  });

  describe("accessing the page", () => {
    it("can access the integration management page", () => {
      stubPlus(true);
      cy.visit(INTEGRATION_MANAGEMENT_ROUTE);
      cy.getByTestId("integration-tabs").should("exist");
    });

    it("can't access without Plus", () => {
      stubPlus(false);
      cy.visit(INTEGRATION_MANAGEMENT_ROUTE);
      cy.getByTestId("home-content").should("exist");
    });
  });

  describe("main page", () => {
    beforeEach(() => {
      stubPlus(true);
    });

    it("should show an empty state when there are no integrations available", () => {
      cy.intercept("GET", "/api/v1/connection*", {
        fixture: "connectors/empty_list.json",
      }).as("getConnections");
      cy.visit(INTEGRATION_MANAGEMENT_ROUTE);
      cy.wait("@getConnections");
      cy.getByTestId("empty-state").should("exist");
    });

    describe("list view", () => {
      beforeEach(() => {
        cy.intercept("GET", "/api/v1/connection*", {
          fixture: "connectors/bigquery_connection_list.json",
        }).as("getConnections");
        cy.visit(INTEGRATION_MANAGEMENT_ROUTE);
        cy.wait("@getConnections");
      });

      it("should show a list of integrations", () => {
        cy.getByTestId("integration-info-bq_integration").should("exist");
        cy.getByTestId("empty-state").should("not.exist");
      });

      it("should navigate to management page when 'manage' button is clicked", () => {
        cy.getByTestId("integration-info-bq_integration").within(() => {
          cy.getByTestId("configure-btn").click();
          cy.url().should("contain", "/bq_integration");
        });
      });
    });

    describe("adding an integration", () => {
      beforeEach(() => {
        cy.intercept("GET", "/api/v1/connection*", {
          fixture: "connectors/bigquery_connection_list.json",
        }).as("getConnections");
        cy.visit(INTEGRATION_MANAGEMENT_ROUTE);
        cy.wait("@getConnections");
      });

      it("should open modal", () => {
        cy.getByTestId("add-integration-btn").click();
        cy.getByTestId("add-modal-content")
          .should("be.visible")
          .within(() => {
            cy.getByTestId("integration-info-bq_placeholder").should("exist");
          });
      });

      it("should be able to add a new BigQuery integration", () => {
        cy.intercept("PATCH", "/api/v1/connection").as("patchConnection");
        cy.getByTestId("add-integration-btn").click();
        cy.getByTestId("add-modal-content").within(() => {
          cy.getByTestId("configure-btn").click();
        });
        cy.getByTestId("input-name").type("test name");
        cy.getByTestId("input-description").type("test description");
        cy.getByTestId("save-btn").click();
        cy.wait("@patchConnection");
      });

      it("should be able to add a new integration with secrets", () => {
        cy.intercept("PATCH", "/api/v1/connection").as("patchConnection");
        cy.intercept("PUT", "/api/v1/connection/*/secret*").as(
          "putConnectionSecrets"
        );
        cy.getByTestId("add-integration-btn").click();
        cy.getByTestId("add-modal-content").within(() => {
          cy.getByTestId("configure-btn").click();
        });
        cy.getByTestId("input-name").type("test name");
        cy.getByTestId("input-keyfile_creds").type(`{"credentials": "test"}`, {
          parseSpecialCharSequences: false,
        });
        cy.getByTestId("save-btn").click();
        cy.wait("@patchConnection");
        cy.wait("@putConnectionSecrets");
      });

      it("should be able to add a new integration associated with a system", () => {
        stubSystemCrud();
        cy.intercept("PATCH", "/api/v1/system/*/connection").as(
          "patchSystemConnection"
        );
        cy.intercept("GET", "/api/v1/system", {
          fixture: "systems/systems.json",
        }).as("getSystems");
        cy.getByTestId("add-integration-btn").click();
        cy.getByTestId("add-modal-content").within(() => {
          cy.getByTestId("configure-btn").click();
        });
        cy.getByTestId("input-name").type("test name");
        cy.selectOption("input-system_fides_key", "Fidesctl System");
        cy.getByTestId("save-btn").click();
        cy.wait("@patchSystemConnection");
      });
    });
  });

  describe("detail view", () => {
    beforeEach(() => {
      stubPlus(true);
      cy.intercept("GET", "/api/v1/connection/*", {
        fixture: "connectors/bigquery_connection.json",
      }).as("getConnection");
      cy.visit("/integrations/bq_integration");
    });

    it("can edit integration with the modal", () => {
      cy.intercept("PATCH", "/api/v1/connection").as("patchConnection");
      cy.getByTestId("manage-btn").click();
      cy.getByTestId("input-system_fides_key").should("not.exist");
      cy.getByTestId("input-name")
        .should("have.value", "BQ Integration")
        .clear()
        .type("A different name");
      cy.getByTestId("save-btn").click();
      cy.wait("@patchConnection");
    });
  });
});
