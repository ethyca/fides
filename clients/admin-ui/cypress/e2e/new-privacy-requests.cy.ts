import {
  stubPlus,
  stubPrivacyRequests,
  stubPrivacyRequestsConfigurationCrud,
  stubTCFConfig,
} from "cypress/support/stubs";

import { RoleRegistryEnum } from "~/types/api";

describe("New Privacy Requests", () => {
  beforeEach(() => {
    cy.login();
    stubPrivacyRequests();
    stubPrivacyRequestsConfigurationCrud();
    cy.intercept("/api/v1/config?api_set=false", {});

    // Add intercept for the new search endpoint (POST instead of GET)
    cy.intercept("POST", "/api/v1/privacy-request/search*", {
      fixture: "privacy-requests/list.json",
    }).as("getPrivacyRequests");
  });

  describe("The requests dashboard", () => {
    beforeEach(() => {
      cy.visit("/new-privacy-requests");
      cy.wait("@getPrivacyRequests");
    });

    it("shows list of requests with status badges", () => {
      // Verify requests are displayed
      cy.get('[data-testid="request-status-badge"]').should(
        "have.length.at.least",
        1,
      );

      // Verify different statuses are shown
      cy.get('[data-testid="request-status-badge"]')
        .filter(':contains("New")')
        .should("exist");
      cy.get('[data-testid="request-status-badge"]')
        .filter(':contains("Completed")')
        .should("exist");
      cy.get('[data-testid="request-status-badge"]')
        .filter(':contains("Error")')
        .should("exist");
    });

    it("shows pagination controls", () => {
      cy.get(".ant-pagination").should("exist");
      cy.get(".ant-pagination-item").should("have.length.at.least", 1);
    });

    it("search filter works", () => {
      cy.wait("@getPrivacyRequests");

      // Type in search box
      cy.getByTestId("privacy-request-search").type("test@example.com");

      // Should trigger a new API call with search param in the body
      cy.wait("@getPrivacyRequests").then((interception) => {
        expect(interception.request.body).to.have.property(
          "fuzzy_search_str",
          "test@example.com",
        );
      });
    });

    it("status filter works", () => {
      cy.wait("@getPrivacyRequests");

      // Use the custom antSelect command to select "Completed" status
      cy.getByTestId("request-status-filter").antSelect("Completed");

      // Should trigger a new API call with status filter in body
      cy.wait("@getPrivacyRequests").then((interception) => {
        expect(interception.request.body).to.have.property("status");
        expect(interception.request.body.status).to.include("complete");
      });
    });

    it("reload button refetches data", () => {
      // Click reload button
      cy.getByTestId("reload-btn").click();

      // Should trigger a new API call
      cy.wait("@getPrivacyRequests");
    });

    it("export button triggers download", () => {
      // Intercept the export CSV endpoint (same as search but with download_csv flag)
      cy.intercept("POST", "/api/v1/privacy-request/search", (req) => {
        if (req.body.download_csv) {
          req.reply({
            statusCode: 200,
            body: "id,status\npri_123,complete",
            headers: {
              "content-type": "text/csv",
            },
          });
        }
      }).as("exportCSV");

      // Click export button
      cy.getByTestId("export-btn").click();

      // Should call the export endpoint
      cy.wait("@exportCSV");
    });
  });

  describe("Request list items", () => {
    beforeEach(() => {
      cy.visit("/new-privacy-requests");
      cy.wait("@getPrivacyRequests");
    });

    it("clicking a request navigates to details page", () => {
      // Get the first list item and click on its header/identity
      cy.get(".ant-list-item").first().find("a").first().click();

      // Should navigate to details page
      cy.location("pathname").should("match", /^\/privacy-requests\/pri.+/);
    });

    it("approve action works from list item", () => {
      // Find a "New" request and click its approve button
      cy.get('[data-testid="request-status-badge"]')
        .filter(':contains("New")')
        .first()
        .closest(".ant-list-item")
        .within(() => {
          cy.getByTestId("privacy-request-approve-btn").click();
        });

      // Confirm in modal (old modal with test ID)
      cy.getByTestId("continue-btn").click();

      // Should call the approve API
      cy.wait("@approvePrivacyRequest")
        .its("request.body.request_ids")
        .should("have.length", 1);
    });
  });

  describe("Bulk actions", () => {
    beforeEach(() => {
      cy.visit("/new-privacy-requests");
      cy.wait("@getPrivacyRequests");
    });

    it("can select multiple requests", () => {
      // Select first two checkboxes
      cy.get('input[type="checkbox"]').eq(1).check(); // First request (0 is select-all)
      cy.get('input[type="checkbox"]').eq(2).check(); // Second request

      // Should show selection count
      cy.contains("2 selected").should("exist");
    });

    it("bulk approve works", () => {
      // Wait for results
      cy.get(".ant-list-item").should("have.length.at.least", 1);

      // Couldn't find a better way to wait until the ant checkbox is interactive
      // eslint-disable-next-line cypress/no-unnecessary-waiting
      cy.wait(400);

      // Select all pending requests using select-all checkbox
      cy.get("#select-all").check();

      // Wait for bulk actions button to be visible and enabled
      cy.get('[data-testid="bulk-actions-btn"]').should("be.visible");
      cy.get('[data-testid="bulk-actions-btn"]').should("not.be.disabled");

      // Open bulk actions dropdown
      cy.get('[data-testid="bulk-actions-btn"]').click();

      // Click approve
      cy.contains("Approve").click();

      // Confirm in modal (using the modal confirm buttons pattern)
      cy.get(".ant-modal-confirm-btns").within(() => {
        cy.contains("Continue").click();
      });

      // Should call bulk approve API
      cy.wait("@approvePrivacyRequest")
        .its("request.body.request_ids")
        .should("have.length.at.least", 1);
    });

    it("bulk actions disabled when nothing selected", () => {
      // Ensure nothing is selected
      cy.get("#select-all").should("not.be.checked");

      // Bulk actions button should be disabled
      cy.get('[data-testid="bulk-actions-btn"]').should("be.disabled");
    });
  });

  describe("Tab navigation", () => {
    beforeEach(() => {
      cy.assumeRole(RoleRegistryEnum.OWNER);
      stubPlus(true);
      stubTCFConfig();
      cy.visit("/new-privacy-requests");
      cy.wait("@getPrivacyRequests");
    });

    it("can switch to Manual Tasks tab", () => {
      // Click on Manual tasks tab using the custom command
      cy.clickAntTab("Manual tasks");

      // URL should include tab query param
      cy.location("search").should("include", "tab=manual-tasks");

      // Should show manual tasks table
      cy.get(".ant-table").should("exist");
    });

    it("tab persists in URL", () => {
      // Navigate to manual tasks using the custom command
      cy.clickAntTab("Manual tasks");
      cy.location("search").should("include", "tab=manual-tasks");

      // Reload page
      cy.reload();

      // Should still be on manual tasks tab
      cy.getAntTab("Manual tasks").should(($tab) => {
        const hasActiveClass = $tab.hasClass("ant-menu-item-selected");
        const parentHasActiveClass = $tab
          .parent()
          .hasClass("ant-tabs-tab-active");
        expect(hasActiveClass || parentHasActiveClass).to.be.true;
      });
    });
  });

  describe("Permissions", () => {
    beforeEach(() => {
      stubPlus(true);
    });

    it("submit request button visible for OWNER role", () => {
      cy.assumeRole(RoleRegistryEnum.OWNER);
      cy.visit("/new-privacy-requests");
      cy.wait("@getPrivacyRequests");

      cy.getByTestId("submit-request-btn").should("exist");
    });

    it("submit request button hidden for VIEWER role", () => {
      cy.assumeRole(RoleRegistryEnum.VIEWER);
      cy.visit("/new-privacy-requests");
      cy.wait("@getPrivacyRequests");

      cy.getByTestId("submit-request-btn").should("not.exist");
    });
  });

  describe("privacy request creation", () => {
    describe("showing button depending on role", () => {
      beforeEach(() => {
        stubPlus(true);
      });

      it("shows the option to create when permitted", () => {
        cy.assumeRole(RoleRegistryEnum.OWNER);
        cy.visit("/new-privacy-requests");
        cy.wait("@getPrivacyRequests");
        cy.getByTestId("submit-request-btn").should("exist");
      });

      it("does not show the option to create when not permitted", () => {
        cy.assumeRole(RoleRegistryEnum.VIEWER_AND_APPROVER);
        cy.visit("/new-privacy-requests");
        cy.wait("@getPrivacyRequests");
        cy.getByTestId("submit-request-btn").should("not.exist");
      });

      it("shows the option to create for approver role", () => {
        cy.assumeRole(RoleRegistryEnum.APPROVER);
        cy.visit("/new-privacy-requests");
        cy.wait("@getPrivacyRequests");
        cy.getByTestId("submit-request-btn").should("exist");
      });
    });

    describe("submitting a request", () => {
      beforeEach(() => {
        stubPlus(true);
        cy.visit("/new-privacy-requests");
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
});
