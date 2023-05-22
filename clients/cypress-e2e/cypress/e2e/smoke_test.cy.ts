import {
  ADMIN_UI_URL,
  API_URL,
  PRIVACY_CENTER_URL,
  SAMPLE_APP_URL,
} from "support/constants";

describe("Smoke test", () => {
  it("can submit an access request from the Privacy Center", () => {
    // Watch these routes without changing or stubbing its response
    cy.intercept("PATCH", `${API_URL}/privacy-request/administrate/approve`).as(
      "patchRequest"
    );
    cy.intercept("GET", `${API_URL}/privacy-request*`).as("getRequests");

    // Submit the access request from the privacy center
    cy.visit(PRIVACY_CENTER_URL);
    cy.getByTestId("card").contains("Access your data").click();
    cy.getByTestId("privacy-request-form").within(() => {
      cy.get("input#email").type("jenny@example.com");
      cy.get("button").contains("Continue").click();
    });

    // Approve the request in the admin UI
    cy.visit(ADMIN_UI_URL);
    cy.origin(ADMIN_UI_URL, () => {
      // Makes custom commands available to all subsequent cy.origin() commands
      // https://docs.cypress.io/api/commands/origin#Custom-commands
      Cypress.require("support/commands");
      cy.login();
      cy.get("div").contains("Review privacy requests").click();
      let numCompletedRequests = 0;
      cy.wait("@getRequests").then((interception) => {
        const { items } = interception.response.body;
        numCompletedRequests = items.filter(
          (i) => i.status === "complete"
        ).length;
      });

      cy.getByTestId("privacy-request-row-pending")
        .first()
        .trigger("mouseover")
        .get("button")
        .contains("Approve")
        .click();

      // Go past the confirmation modal
      cy.getByTestId("continue-btn").click();

      cy.wait("@patchRequest");
      cy.wait("@getRequests");

      // Make sure there is one more completed request than originally
      cy.getByTestId("privacy-request-row-complete").then((rows) => {
        expect(rows.length).to.eql(numCompletedRequests + 1);
      });
    });
  });

  it("can access Mongo and Postgres connectors from the Admin UI", () => {
    cy.intercept(`${API_URL}/connection_type`).as("getConnectionType");
    cy.intercept(`${API_URL}/connection*`).as("getConnections");

    cy.visit(ADMIN_UI_URL);
    cy.login();
    cy.get("div").contains("Configure privacy requests").click();
    cy.wait("@getConnections");
    cy.get("a").contains("Connection manager").click();
    cy.wait("@getConnectionType");
    cy.getByTestId("connection-grid-item-MongoDB Connector").within(() => {
      cy.get("button").contains("Test").click();
    });
    cy.getByTestId("connection-grid-item-Postgres Connector").within(() => {
      cy.get("button").contains("Test").click();
    });
  });

  it("can manage consent preferences from the Privacy Center", () => {
    cy.visit(PRIVACY_CENTER_URL);
    cy.getCookie("fides_consent").should("not.exist");
    cy.getByTestId("card").contains("Manage your consent").click();
    cy.getByTestId("consent-request-form").within(() => {
      cy.get("input#email").type("jenny@example.com");
      cy.get("button").contains("Continue").click();
    });

    // Check the defaults for Cookie House are what we expect:
    //  - Data Sales or Sharing => true
    //  - Email Marketing => true
    //  - Product Analytics => true
    cy.getByTestId(`consent-item-advertising`).within(() => {
      cy.contains("Data Sales or Sharing");
      cy.getRadio("true").should("be.checked");
      cy.getRadio("false").should("not.be.checked");
    });
    cy.getByTestId(`consent-item-advertising.first_party`).within(() => {
      cy.contains("Email Marketing");
      cy.getRadio("true").should("be.checked");
      cy.getRadio("false").should("not.be.checked");
    });
    cy.getByTestId(`consent-item-improve`).within(() => {
      cy.contains("Product Analytics");
      cy.getRadio("true").should("be.checked");
      cy.getRadio("false").should("not.be.checked");
    });

    // Opt-out of data sales / sharing
    cy.getByTestId(`consent-item-advertising`).within(() => {
      cy.getRadio("false").check({ force: true });
    });
    cy.contains("Save").click();
    cy.contains("Your consent preferences have been saved");

    // Reload and confirm preferences were saved
    cy.visit(PRIVACY_CENTER_URL);
    cy.reload();
    cy.getByTestId("card").contains("Manage your consent").click();
    cy.getByTestId("consent-request-form").within(() => {
      cy.get("input#email").type("jenny@example.com");
      cy.get("button").contains("Continue").click();
    });
    cy.getByTestId(`consent-item-advertising`).within(() => {
      cy.getRadio("true").should("not.be.checked");
      cy.getRadio("false").should("be.checked");
    });
    cy.getCookie("fides_consent").should("exist");

    // Visit the Cookie House sample app and confirm saved consent preferences are loaded
    cy.visit(SAMPLE_APP_URL);
    cy.origin(SAMPLE_APP_URL, () => {
      cy.getCookie("fides_consent").should("exist");
      cy.window().then((win) => {
        cy.wrap(win).should("to.have.property", "Fides");
        cy.wrap(win)
          .should("to.have.nested.property", "Fides.fides_meta.version")
          .should("eql", "0.9.0");
        cy.wrap(win)
          .should("to.have.nested.property", "Fides.consent")
          .should("eql", {
            data_sales: false,
            tracking: true,
            analytics: true,
          });
        cy.wrap(win).should(
          "to.have.nested.property",
          "Fides.identity.fides_user_device_id"
        );
      });
    });
  });
});
