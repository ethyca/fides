import {
  stubInfrastructureSystems,
  stubPlus,
  stubTaxonomyEntities,
} from "cypress/support/stubs";

import { ACTION_CENTER_ROUTE } from "~/features/common/nav/routes";

describe("Action center infrastructure systems", () => {
  const monitorId = "my_infrastructure_monitor_1";
  const testUrn = "urn:okta:app:12345678-1234-1234-1234-123456789012";

  describe("error handling", () => {
    beforeEach(() => {
      cy.login();
      stubPlus(true);
      stubTaxonomyEntities();
      cy.intercept(
        "GET",
        `/api/v1/plus/identity-provider-monitors/${monitorId}/results*`,
        {
          statusCode: 500,
          body: { detail: "Internal server error" },
        },
      ).as("getIdentityProviderMonitorResultsError");
    });

    it("should display error page when fetching infrastructure systems fails", () => {
      cy.visit(`${ACTION_CENTER_ROUTE}/infrastructure/${monitorId}`);
      cy.wait("@getIdentityProviderMonitorResultsError");

      cy.getByTestId("error-page-result").should("exist");
      cy.getByTestId("error-page-result").within(() => {
        cy.contains("Error 500").should("exist");
        cy.contains("Internal server error").should("exist");
        cy.contains("Reload").should("exist");
      });
    });
  });

  describe("data use management", () => {
    beforeEach(() => {
      cy.login();
      stubPlus(true);
      stubTaxonomyEntities();
      stubInfrastructureSystems();
    });

    it("should allow adding a data use to an infrastructure system", () => {
      cy.visit(`${ACTION_CENTER_ROUTE}/infrastructure/${monitorId}`);
      cy.wait("@getInfrastructureSystems");

      cy.get(`[data-classification-select="${testUrn}"]`).within(() => {
        cy.get("button[aria-label='Add data use']").click({ force: true });
      });

      cy.get(`[data-classification-select="${testUrn}"]`).antSelect(0);

      cy.wait("@updateInfrastructureSystemDataUses").then((interception) => {
        expect(interception.request.body).to.deep.equal({
          urn: testUrn,
          user_assigned_data_uses: ["marketing.advertising", "analytics"],
        });
      });
    });

    it("should allow removing a data use from an infrastructure system", () => {
      const slackUrn = "urn:okta:app:another-app";

      cy.intercept(
        "PATCH",
        `/api/v1/plus/identity-provider-monitors/${monitorId}/results/${slackUrn}`,
        {
          statusCode: 200,
          body: {
            urn: slackUrn,
            user_assigned_data_uses: ["marketing.advertising"],
          },
        },
      ).as("updateSlackSystemDataUses");

      cy.visit(`${ACTION_CENTER_ROUTE}/infrastructure/${monitorId}`);
      cy.wait("@getInfrastructureSystems");

      cy.get(`[data-classification-select="${slackUrn}"]`).within(() => {
        cy.get(".ant-tag").filter(":contains('Analytics')").should("exist");
        cy.get(".ant-tag")
          .filter(":contains('Analytics')")
          .within(() => {
            cy.get("button").click({ force: true });
          });
      });

      cy.wait("@updateSlackSystemDataUses").then((interception) => {
        expect(interception.request.body).to.deep.equal({
          urn: slackUrn,
          user_assigned_data_uses: ["marketing.advertising"],
        });
      });
    });

    it("should handle error when updating data uses fails", () => {
      stubInfrastructureSystems({
        patchStatus: 500,
        patchResponse: { detail: "Internal server error" },
      });

      cy.visit(`${ACTION_CENTER_ROUTE}/infrastructure/${monitorId}`);
      cy.wait("@getInfrastructureSystems");

      cy.get(`[data-classification-select="${testUrn}"]`).within(() => {
        cy.get("button[aria-label='Add data use']").click({ force: true });
      });

      cy.get(`[data-classification-select="${testUrn}"]`).antSelect(0);

      cy.wait("@updateInfrastructureSystemDataUses");

      cy.get(".ant-message-error", { timeout: 5000 }).should("exist");
      cy.get(".ant-message-error").should("contain", "Internal server error");
    });

    it("should not add duplicate data uses", () => {
      cy.visit(`${ACTION_CENTER_ROUTE}/infrastructure/${monitorId}`);
      cy.wait("@getInfrastructureSystems");

      // cy.get(`[data-classification-select="${testUrn}"]`).within(() => {
      //   cy.get("button[aria-label='Add data use']").click({ force: true });
      // });

      cy.get(`[data-classification-select="${testUrn}"]`)
        .find("input")
        .focus()
        .type("marketing.advertising");

      cy.get(`[data-classification-select="${testUrn}"]`).antSelect(0);

      cy.get("@updateInfrastructureSystemDataUses.all").should(
        "have.length",
        0,
      );
    });

    it("should allow removing the last data use", () => {
      stubInfrastructureSystems({
        fixture:
          "detection-discovery/results/infrastructure-systems-single-data-use.json",
      });

      cy.visit(`${ACTION_CENTER_ROUTE}/infrastructure/${monitorId}`);
      cy.wait("@getInfrastructureSystems");

      cy.get(`[data-classification-select="${testUrn}"]`).within(() => {
        cy.get(".ant-tag").filter(":contains('Marketing')").should("exist");
        cy.get(".ant-tag")
          .filter(":contains('Marketing')")
          .within(() => {
            cy.get("button").click({ force: true });
          });
      });

      cy.wait("@updateInfrastructureSystemDataUses").then((interception) => {
        expect(interception.request.body).to.deep.equal({
          urn: testUrn,
          user_assigned_data_uses: [],
        });
      });
    });
  });
});
