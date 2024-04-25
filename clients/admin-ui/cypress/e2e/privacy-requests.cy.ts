import {
  stubPlus,
  stubPrivacyRequests,
  stubPrivacyRequestsConfigurationCrud,
} from "cypress/support/stubs";

import { PrivacyRequestEntity } from "~/features/privacy-requests/types";
import { RoleRegistryEnum } from "~/types/api";

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
      cy.getByTestId("pii-toggle").click();
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

  describe("Storage Configuration", () => {
    beforeEach(() => {
      cy.visit("/privacy-requests/configure/storage");
    });

    it("Can configure local storage", () => {
      cy.getByTestId("option-local").click();
      cy.wait("@createConfigurationSettings").then((interception) => {
        const { body } = interception.request;
        expect(body.storage.active_default_storage_type).to.eql("local");
      });

      cy.wait("@createStorage").then((interception) => {
        const { body } = interception.request;
        expect(body.type).to.eql("local");
        expect(body.format).to.eql("json");
      });
    });

    it("Can configure S3 storage", () => {
      cy.getByTestId("option-s3").click();
      cy.wait("@createConfigurationSettings").then((interception) => {
        const { body } = interception.request;
        expect(body.storage.active_default_storage_type).to.eql("s3");
      });
      cy.wait("@getStorageDetails");
    });
  });

  describe("Message Configuration", () => {
    beforeEach(() => {
      cy.visit("/privacy-requests/configure/messaging");
    });

    it("Can configure Mailgun email", () => {
      cy.getByTestId("option-mailgun").click();
      cy.getByTestId("input-domain").type("test-domain");
      cy.getByTestId("save-btn").click();
      cy.wait("@createMessagingConfiguration").then((interception) => {
        const { body } = interception.request;
        expect(body.service_type).to.eql("mailgun");
        cy.contains(
          "Mailgun email successfully updated. You can now enter your security key."
        );
      });
    });

    it("Can configure Twilio email", () => {
      cy.getByTestId("option-twilio-email").click();
      cy.getByTestId("input-email").type("test-email");
      cy.getByTestId("save-btn").click();
      cy.wait("@createMessagingConfiguration").then(() => {
        cy.contains(
          "Twilio email successfully updated. You can now enter your security key."
        );
      });
    });

    it("Can configure Twilio SMS", () => {
      cy.getByTestId("option-twilio-sms").click();
      cy.wait("@createMessagingConfiguration").then(() => {
        cy.contains("Messaging provider saved successfully.");
      });
    });
  });

  describe("privacy request creation", () => {
    describe("showing button depending on role", () => {
      beforeEach(() => {
        stubPlus(true);
      });

      it("shows the option to create when permitted", () => {
        cy.assumeRole(RoleRegistryEnum.OWNER);
        cy.visit("/privacy-requests");
        cy.wait("@getPrivacyRequests");
        cy.getByTestId("submit-request-btn").should("exist");
      });

      it("does not show the option to create when not permitted", () => {
        cy.assumeRole(RoleRegistryEnum.VIEWER_AND_APPROVER);
        cy.visit("/privacy-requests");
        cy.wait("@getPrivacyRequests");
        cy.getByTestId("submit-request-btn").should("not.exist");
      });
    });

    describe("submitting a request", () => {
      beforeEach(() => {
        stubPlus(true);
        cy.visit("/privacy-requests");
        cy.wait("@getPrivacyRequests");
      });

      it("opens the modal", () => {
        cy.getByTestId("submit-request-btn").click();
        cy.wait("@getPrivacyCenterConfig");
        cy.getByTestId("submit-request-modal").should("exist");
      });

      it("shows configured fields and values", () => {
        cy.getByTestId("submit-request-btn").click();
        cy.wait("@getPrivacyCenterConfig");
        cy.getSelectValueContainer("input-policy_key").type("a{enter}");
        cy.getByTestId("input-identity.phone").should("not.exist");
        cy.getByTestId("input-identity.email").should("exist");
        cy.getByTestId(
          "input-custom_privacy_request_fields.required_field.value"
        ).should("exist");
        cy.getByTestId(
          "input-custom_privacy_request_fields.hidden_field.value"
        ).should("not.exist");
        cy.getByTestId(
          "input-custom_privacy_request_fields.field_with_default_value.value"
        ).should("have.value", "The default value");
        cy.getByTestId("submit-btn").should("be.disabled");
      });

      it("can submit a privacy request", () => {
        cy.getByTestId("submit-request-btn").click();
        cy.wait("@getPrivacyCenterConfig");
        cy.getSelectValueContainer("input-policy_key").type("a{enter}");
        cy.getByTestId("input-identity.email").type("email@ethyca.com");
        cy.getByTestId(
          "input-custom_privacy_request_fields.required_field.value"
        ).type("A value for the required field");
        cy.getByTestId("input-is_verified").click();
        cy.intercept("POST", "/api/v1/privacy-request/authenticated", {
          statusCode: 200,
          body: {
            succeeded: [
              {
                policy_key: "default_access_policy",
                identity: {
                  email: "email@ethyca.com",
                },
                custom_privacy_request_fields: {
                  required_field: {
                    label: "Required example field",
                    value: "A value for the required field",
                  },
                  field_with_default_value: {
                    label: "Example field with default value",
                    value: "The default value",
                  },
                },
              },
            ],
          },
        }).as("postPrivacyRequest");
        cy.getByTestId("submit-btn").click();
        cy.getByTestId("toast-success-msg").should("exist");
        cy.wait("@postPrivacyRequest");
        cy.wait("@getPrivacyRequests");
      });
    });
  });
});
