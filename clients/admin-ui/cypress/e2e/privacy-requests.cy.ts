import {
  stubPlus,
  stubPrivacyRequests,
  stubPrivacyRequestsConfigurationCrud,
} from "cypress/support/stubs";

import { PrivacyRequestEntity } from "~/features/privacy-requests/types";
import { PrivacyRequestStatus, RoleRegistryEnum } from "~/types/api";

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

      cy.get("tr").as("rows");

      // Annoyingly fancy, I know, but this selects the containing rows that have a badge with the
      // matching status text -- as opposed to just filtering by status which would yield the badge
      // element itself.
      const selectByStatus = (status: string) =>
        cy
          .get("@rows")
          .getByTestId("request-status-badge")
          .filter(`:contains('${status}')`)
          .closest("tr");

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
      cy.get("@rowsNew").first().click();
      cy.location("pathname").should("match", /^\/privacy-requests\/pri.+/);
    });

    it("allows approving a new request", () => {
      cy.get("@rowsNew")
        .first()
        .within(() => {
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

    it("allows deleting a new request", () => {
      cy.get("@rowsNew")
        .first()
        .within(() => {
          cy.getByTestId("privacy-request-delete-btn").click();
        });
      cy.getByTestId("confirmation-modal");
      cy.getByTestId("continue-btn").click();

      cy.wait("@softDeletePrivacyRequest");
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
        cy.getByTestId("request-detail-value-id")
          .should("have.prop", "value")
          .should("match", /pri_/);
        cy.getByTestId("request-status-badge").contains("New");
      });
    });

    describe("Activity Timeline", () => {
      beforeEach(() => {
        // Override the privacy request with our fixture that has logs
        cy.intercept("GET", "/api/v1/privacy-request*", {
          fixture: "privacy-requests/with-logs.json",
        }).as("getPrivacyRequestWithLogs");
        cy.visit("/privacy-requests/pri_96bb91d3-cdb9-46c3-9546-0c276eb05a5c");
        cy.wait("@getPrivacyRequestWithLogs");
      });

      it("displays activity timeline entries with logs", () => {
        // Verify timeline entries are visible
        cy.getByTestId("activity-timeline-list").should("exist");
        cy.getByTestId("activity-timeline-item").should(
          "have.length.at.least",
          1,
        );

        // Check first entry details
        cy.getByTestId("activity-timeline-item")
          .first()
          .within(() => {
            cy.getByTestId("activity-timeline-author").should(
              "contain",
              "Fides:",
            );
            cy.getByTestId("activity-timeline-title").should("exist");
            cy.getByTestId("activity-timeline-timestamp").should("exist");
            cy.getByTestId("activity-timeline-type").should(
              "contain",
              "Request update",
            );
          });

        // Check the item with error has View Log
        cy.getByTestId("activity-timeline-item")
          .contains("klavyio_klaviyo_api")
          .parent()
          .within(() => {
            cy.getByTestId("activity-timeline-view-logs").should(
              "contain",
              "View Log",
            );
          });
      });

      it("opens and closes the log details drawer", () => {
        // Click on the item with error to open drawer
        cy.getByTestId("activity-timeline-item")
          .contains("klavyio_klaviyo_api")
          .click();

        // Verify drawer opens with correct content
        cy.get("[data-testid=log-drawer]").should("be.visible");
        cy.get("[data-testid=log-drawer]").should("exist");

        // Close drawer
        cy.getByTestId("log-drawer-close").click();
        cy.get("[data-testid=log-drawer]").should("not.exist");
      });
    });

    it("allows approving a new request", () => {
      cy.getByTestId("privacy-request-actions-dropdown-btn").click();
      cy.getByTestId("privacy-request-approve-btn").click();
      cy.getByTestId("continue-btn").click();

      cy.wait("@approvePrivacyRequest")
        .its("request.body.request_ids")
        .should("have.length", 1);
    });

    it("allows denying a new request", () => {
      cy.getByTestId("privacy-request-actions-dropdown-btn").click();
      cy.getByTestId("privacy-request-deny-btn").click();

      cy.getByTestId("deny-privacy-request-modal").within(() => {
        cy.getByTestId("input-denialReason").type("test denial");
        cy.getByTestId("deny-privacy-request-modal-btn").click();
      });

      cy.wait("@denyPrivacyRequest")
        .its("request.body.request_ids")
        .should("have.length", 1);
    });

    it("shouldn't show the download button for pending requests", () => {
      cy.getByTestId("privacy-request-actions-dropdown-btn").click();
      cy.getByTestId("download-results-btn").should("not.exist");
    });
  });

  describe("downloading access requests", () => {
    beforeEach(() => {
      cy.assumeRole(RoleRegistryEnum.OWNER);
      cy.get<PrivacyRequestEntity>("@privacyRequest").then((privacyRequest) => {
        cy.visit(`/privacy-requests/${privacyRequest.id}`);
      });
    });

    it("can download completed access request results", () => {
      cy.intercept("GET", "/api/v1/privacy-request/*/access-results", {
        body: { access_result_urls: ["https://example.com/"] },
      }).as("getAccessResultURL");
      stubPrivacyRequests(PrivacyRequestStatus.COMPLETE);
      cy.wait("@getAccessResultURL");
      cy.getByTestId("privacy-request-actions-dropdown-btn").click();
      cy.getByTestId("download-results-btn")
        .parents(".ant-dropdown-menu-item")
        .should("not.have.class", "ant-dropdown-menu-item-disabled")
        .should("have.attr", "aria-disabled", "false");
    });

    it("can't download when request info is stored locally", () => {
      cy.intercept("GET", "/api/v1/privacy-request/*/access-results", {
        body: { access_result_urls: ["your local fides_uploads folder"] },
      }).as("getAccessResultURL");
      stubPrivacyRequests(PrivacyRequestStatus.COMPLETE);
      cy.wait("@getAccessResultURL");
      cy.getByTestId("privacy-request-actions-dropdown-btn").click();
      cy.getByTestId("download-results-btn")
        .parents(".ant-dropdown-menu-item")
        .should("have.class", "ant-dropdown-menu-item-disabled")
        .should("have.attr", "aria-disabled", "true");
    });

    it("doesn't show the button for non-access requests", () => {
      stubPrivacyRequests(PrivacyRequestStatus.COMPLETE, {
        name: "test",
        rules: [],
        key: "test",
      });
      cy.wait("@getPrivacyRequest");
      cy.getByTestId("privacy-request-actions-dropdown-btn").click();
      cy.getByTestId("download-results-btn").should("not.exist");
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
          "Mailgun email successfully updated. You can now enter your security key.",
        );
      });
    });

    it("Can configure Twilio email", () => {
      cy.getByTestId("option-twilio-email").click();
      cy.getByTestId("input-email").type("test-email");
      cy.getByTestId("save-btn").click();
      cy.wait("@createMessagingConfiguration").then(() => {
        cy.contains(
          "Twilio email successfully updated. You can now enter your security key.",
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

        cy.getByTestId("controlled-select-policy_key").antSelect(
          "Access your data",
        );
        cy.getByTestId("input-identity.phone").should("not.exist");
        cy.getByTestId("input-identity.email").should("exist");
        cy.getByTestId(
          "input-custom_privacy_request_fields.required_field.value",
        ).should("exist");
        cy.getByTestId(
          "input-custom_privacy_request_fields.hidden_field.value",
        ).should("exist");
        cy.getByTestId(
          "input-custom_privacy_request_fields.field_with_default_value.value",
        ).should("have.value", "The default value");
        cy.getByTestId("submit-btn").should("be.disabled");
      });

      it("can submit a privacy request", () => {
        cy.getByTestId("submit-request-btn").click();
        cy.wait("@getPrivacyCenterConfig");
        cy.getByTestId("controlled-select-policy_key").type("a{enter}");
        cy.getByTestId("input-identity.email").type("email@ethyca.com");
        cy.getByTestId(
          "input-custom_privacy_request_fields.required_field.value",
        ).type("A value for the required field");
        cy.getByTestId(
          "input-custom_privacy_request_fields.hidden_field.value",
        ).type("A value for the hidden but required field");
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

  /**
   * Tests for privacy request attachments functionality
   */
  describe("Request Attachments", () => {
    beforeEach(() => {
      cy.assumeRole(RoleRegistryEnum.OWNER);

      cy.intercept("GET", "/api/v1/storage/default/active", {
        key: "default_storage_config_local",
        type: "local",
      }).as("getActiveStorage");

      cy.intercept("GET", "/api/v1/plus/privacy-request/*/attachment*", {
        statusCode: 200,
        fixture: "privacy-requests/attachments.json",
      }).as("getAttachments");

      cy.get<PrivacyRequestEntity>("@privacyRequest").then((privacyRequest) => {
        cy.visit(`/privacy-requests/${privacyRequest.id}`);
      });

      cy.wait("@getPrivacyRequest");
      cy.wait("@getAttachments");
    });

    it("displays existing attachments", () => {
      cy.get(".ant-upload-list-item-container").should("have.length", 2);

      cy.get(".ant-upload-list-item-container")
        .first()
        .find(".ant-typography")
        .should("contain", "test-document.pdf");

      cy.get(".ant-upload-list-item-container")
        .last()
        .find(".ant-typography")
        .should("contain", "local-document.pdf");
    });

    it("downloads attachment when button is clicked for external links", () => {
      // Stub window.open before intercepting, based on
      // https://glebbahmutov.com/cypress-examples/recipes/window-open.html
      cy.window().then((win) => {
        cy.stub(win, "open").as("windowOpen");
      });

      cy.intercept("GET", "/api/v1/plus/privacy-request/*/attachment/*", {
        statusCode: 200,
        fixture: "privacy-requests/attachment-details-external.json",
      }).as("getAttachmentDetails");

      cy.get(".ant-upload-list-item-container").first().find("button").click();
      cy.wait("@getAttachmentDetails");

      // Confirm the window.open stub was called with expected URL
      cy.get("@windowOpen").should(
        "have.been.calledWith",
        "https://example.com/download/test-document.pdf",
      );
    });

    it("shows info message for local storage attachments", () => {
      cy.intercept("GET", "/api/v1/plus/privacy-request/*/attachment/*", {
        statusCode: 200,
        fixture: "privacy-requests/attachment-details-local.json",
      }).as("getAttachmentDetails");

      cy.get(".ant-upload-list-item-container").last().find("button").click();
      cy.wait("@getAttachmentDetails");

      cy.get(".ant-message-info").should("be.visible");
      cy.get(".ant-message-info").should(
        "contain",
        "Download is not available when using local storage methods",
      );
    });

    it("uploads new attachments", () => {
      cy.intercept("POST", "/api/v1/plus/privacy-request/*/attachment*", {
        statusCode: 200,
      }).as("uploadAttachment");

      cy.get('input[type="file"]').selectFile(
        "cypress/fixtures/privacy-requests/test-upload.pdf",
        { force: true },
      );

      cy.wait("@uploadAttachment").then((interception) => {
        expect(interception.request.headers["content-type"]).to.include(
          "multipart/form-data",
        );
        expect(interception.response.statusCode).to.equal(200);
      });

      cy.get(".ant-message-success").should("be.visible");
      cy.get(".ant-message-success").should(
        "contain",
        "test-upload.pdf file uploaded successfully",
      );
    });
  });

  /**
   * Tests for privacy request comments functionality
   */
  describe("Request Comments", () => {
    beforeEach(() => {
      cy.assumeRole(RoleRegistryEnum.OWNER);

      cy.intercept("GET", "/api/v1/plus/privacy-request/*/comment*", {
        statusCode: 200,
        fixture: "privacy-requests/comments/comments-list.json",
      }).as("getComments");

      cy.intercept("POST", "/api/v1/plus/privacy-request/*/comment", {
        statusCode: 200,
        fixture: "privacy-requests/comments/comment-created.json",
      }).as("createComment");

      cy.intercept("GET", "/api/v1/privacy-request*", {
        fixture: "privacy-requests/with-logs.json",
      }).as("getPrivacyRequestWithLogs");

      cy.visit("/privacy-requests/pri_96bb91d3-cdb9-46c3-9546-0c276eb05a5c");
      cy.wait("@getPrivacyRequestWithLogs");
      cy.wait("@getComments");
    });

    it("displays existing comments in the activity timeline", () => {
      cy.getByTestId("activity-timeline-item")
        .contains("This is a test comment")
        .should("exist");
      cy.contains("Test User:").should("exist");
      cy.getByTestId("activity-timeline-type")
        .contains("Internal comment")
        .should("exist");
    });

    it("allows creating a new comment", () => {
      cy.contains("Add comment").click();
      cy.getByTestId("comment-input").should("exist");
      cy.getByTestId("comment-input").type("New comment from test");
      cy.getByTestId("submit-comment-button").click();

      // Check that the request was made with the correct form data
      cy.wait("@createComment").then((interception) => {
        const requestBody = interception.request.body;
        expect(requestBody).to.include('name="comment_text"');
        expect(requestBody).to.include("New comment from test");
        expect(requestBody).to.include('name="comment_type"');
        expect(requestBody).to.include("note");
      });
    });

    it("allows canceling comment creation", () => {
      cy.contains("Add comment").click();
      cy.getByTestId("comment-input").should("exist");
      cy.getByTestId("comment-input").type("Comment that will be canceled");
      cy.getByTestId("cancel-comment-button").click();
      cy.getByTestId("comment-input").should("not.exist");
    });

    it("shows loading state while fetching comments", () => {
      cy.intercept("GET", "/api/v1/plus/privacy-request/*/comment*", {
        statusCode: 200,
        fixture: "privacy-requests/comments/empty-comments.json",
        delay: 1000,
      }).as("getCommentsDelayed");

      cy.visit("/privacy-requests/pri_96bb91d3-cdb9-46c3-9546-0c276eb05a5c");

      // Check for skeleton loading state before comments load
      cy.get(".ant-skeleton").should("exist");

      cy.wait("@getCommentsDelayed");

      // Verify skeletons are gone after loading
      cy.get(".ant-skeleton").should("not.exist");
    });

    it.only("restricts comment functionality based on user role", () => {
      cy.contains("Add comment").should("exist");

      cy.assumeRole(RoleRegistryEnum.VIEWER);
      cy.reload();
      cy.wait("@getPrivacyRequestWithLogs");
      cy.wait("@getComments");

      cy.contains("Add comment").should("not.exist");
    });
  });
});
