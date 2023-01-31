import { stubPrivacyRequests } from "cypress/support/stubs";

import { PrivacyRequestEntity } from "~/features/privacy-requests/types";

describe("Privacy Requests", () => {
  beforeEach(() => {
    cy.login();
    stubPrivacyRequests();
  });

  describe("The requests table", () => {
    beforeEach(() => {
      cy.visit("/privacy-requests");
      cy.wait("@getPrivacyRequests");

      cy.getByTestIdPrefix("privacy-request-row").as("rows");

      // Annoyingly fancy, I know, but this selects the containing rows that have a badge with the
      // matching status text -- as opposed to just filtering by status which would yield the badge
      // element itself.
      const selectByStatus = (status: string) =>
        cy
          .get("@rows")
          .getByTestId("request-status-badge")
          .filter(`:contains('${status}')`)
          .closest("[data-testid^='privacy-request-row']");

      selectByStatus("New").as("rowsNew");
      selectByStatus("Completed").as("rowsCompleted");
      selectByStatus("Error").as("rowsError");
    });

    // TODO: add multi-page stubs to test the pagination controls.
    it("shows the first page of results", () => {
      cy.get("@rowsNew").should("have.length", 4);
      cy.get("@rowsCompleted").should("have.length", 3);
      cy.get("@rowsError").should("have.length", 1);
    });

    it("allows navigation to the details of request", () => {
      cy.get("@rowsNew")
        .first()
        .within(() => {
          cy.getByTestId("privacy-request-more-btn").click();
        });

      cy.getByTestId("privacy-request-more-menu")
        .contains("View Details")
        .click();

      cy.location("pathname").should("match", /^\/privacy-requests\/pri.+/);
    });
  });

  describe("The request details page", () => {
    beforeEach(() => {
      cy.get<PrivacyRequestEntity>("@privacyRequest").then((privacyRequest) => {
        cy.visit(`/privacy-requests/${privacyRequest.id}`);
      });
      cy.wait("@getPrivacyRequest");
    });

    it("shows the request details", () => {
      cy.getByTestId("privacy-request-details").within(() => {
        cy.contains("Request ID").parent().contains(/pri_/);
        cy.getByTestId("request-status-badge").contains("New");
      });
    });
  });
});
