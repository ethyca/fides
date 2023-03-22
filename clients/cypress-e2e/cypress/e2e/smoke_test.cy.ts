import {
  ADMIN_UI_URL,
  API_URL,
  PRIVACY_CENTER_URL,
} from "../support/constants";

describe("Smoke test", () => {
  it("can submit an access request from the privacy center", () => {
    // Watch these routes without changing or stubbing its response
    cy.intercept("PATCH", `${API_URL}/privacy-request/administrate/approve`).as(
      "patchRequest"
    );
    cy.intercept("GET", `${API_URL}/privacy-request*`).as("getRequests");

    // Submit the access request from the privacy center
    cy.visit(PRIVACY_CENTER_URL);
    cy.getByTestId("card").contains("Access your data").click();
    cy.getByTestId("privacy-request-form").within(() => {
      cy.get("input#name").type("Jenny");
      cy.get("input#email").type("jenny@example.com");

      cy.get("button").contains("Continue").click();
    });

    // Approve the request in the admin UI
    cy.visit(ADMIN_UI_URL);
    cy.origin(ADMIN_UI_URL, () => {
      // Makes custom commands available to all subsequent cy.origin() commands
      // https://docs.cypress.io/api/commands/origin#Custom-commands
      Cypress.require("../support/commands");
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

  it("can access mongo and postgres connectors", () => {
    cy.intercept(`${API_URL}/connection_type`).as("getConnectionType");
    cy.intercept(`${API_URL}/connection*`).as("getConnections");

    cy.visit(ADMIN_UI_URL);
    cy.login();
    cy.get("div").contains("Configure privacy requests").click();
    cy.wait("@getConnections");
    cy.get("a").contains("Connection manager").click();
    cy.wait("@getConnectionType");
    cy.getByTestId("connection-grid-item-mongodb_connector").within(() => {
      // TODO: UI does not appear to indicate when test fails
      cy.get("button").contains("Test").click();
    });
    cy.getByTestId("connection-grid-item-postgres_connector");
  });
});
