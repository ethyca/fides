import {
  stubPrivacyRequests,
  stubPrivacyRequestsConfigurationCrud,
} from "cypress/support/stubs";

import { PrivacyRequestEntity } from "~/features/privacy-requests/types";

describe("Privacy Requests", () => {
  beforeEach(() => {
    cy.login();
    stubPrivacyRequests();
    stubPrivacyRequestsConfigurationCrud();
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

    it("allows approving a new request", () => {
      cy.get("@rowsNew")
        .first()
        .within(() => {
          // The approve button shows up on hover, but there isn't a good way to simulate that in
          // tests. Instead we click on the menu button to make all the controls appear.
          cy.getByTestId("privacy-request-more-btn").click();
          cy.getByTestId("privacy-request-approve-btn").click();
        });

      cy.getByTestId("continue-btn").click();

      cy.wait("@approvePrivacyRequest")
        .its("request.body.request_ids")
        .should("have.length", 1);
    });

    it("allows denying a new request", () => {
      cy.get("@rowsNew")
        .first()
        .within(() => {
          cy.getByTestId("privacy-request-more-btn").click();
          cy.getByTestId("privacy-request-deny-btn").click();
        });

      cy.getByTestId("deny-privacy-request-modal").within(() => {
        cy.getByTestId("input-denialReason").type("test denial");
        cy.getByTestId("deny-privacy-request-modal-btn").click();
      });

      cy.wait("@denyPrivacyRequest")
        .its("request.body.request_ids")
        .should("have.length", 1);
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

    it("allows approving a new request", () => {
      cy.getByTestId("privacy-request-approve-btn").click();
      cy.getByTestId("continue-btn").click();

      cy.wait("@approvePrivacyRequest")
        .its("request.body.request_ids")
        .should("have.length", 1);
    });

    it("allows denying a new request", () => {
      cy.getByTestId("privacy-request-deny-btn").click();

      cy.getByTestId("deny-privacy-request-modal").within(() => {
        cy.getByTestId("input-denialReason").type("test denial");
        cy.getByTestId("deny-privacy-request-modal-btn").click();
      });

      cy.wait("@denyPrivacyRequest")
        .its("request.body.request_ids")
        .should("have.length", 1);
    });
  });

  describe("Messaging Provider Configuration", () => {
    beforeEach(() => {
      cy.visit("/privacy-requests/configure/messaging");
    });

    it("Can configure mailgun email as messaging provider", () => {
      cy.getByTestId("option-mailgun-email").click();
      //   createConfigurationSettings
      //   getMessagingConfigurationDetails
      cy.wait("@createMessagingConfiguration").then((interception) => {
        const { body } = interception.request;
        console.log("body", body);
      });
      //   createMessagingConfigurationSecrets
    });

    it("Can configure twilio email as messaging provider", () => {
      cy.getByTestId("option-twilio-email").click();
      //   createConfigurationSettings
      //   getMessagingConfigurationDetails
      cy.wait("@createMessagingConfiguration").then((interception) => {
        const { body } = interception.request;
        console.log("body", body);
      });
      //   createMessagingConfigurationSecrets
    });

    it("Can configure twilio SMS as messaging provider", () => {
      cy.getByTestId("option-twilio-sms").click();
      //   createConfigurationSettings
      //   getMessagingConfigurationDetails
      cy.wait("@createMessagingConfiguration").then((interception) => {
        const { body } = interception.request;
        console.log("body", body);
      });
    });
  });

  describe("Storage Configuration", () => {
    beforeEach(() => {
      cy.visit("/privacy-requests/configure/storage");
    });

    it("Can configure local storage", () => {
      cy.getByTestId("option-local").click();
      //   createConfigurationSettings
      cy.wait("@createStorage").then((interception) => {
        const { body } = interception.request;
        console.log("body", body);
      });
    });

    it("Can configure S3 storage", () => {
      cy.getByTestId("option-s3").click();
      //   createConfigurationSettings
      //   getStorageDetails
      cy.wait("@createStorage").then((interception) => {
        const { body } = interception.request;
        console.log("body", body);
      });
      //   createStorageSecrets
    });
  });
});
