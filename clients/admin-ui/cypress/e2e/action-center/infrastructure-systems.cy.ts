import { stubPlus, stubTaxonomyEntities } from "cypress/support/stubs";

import { ACTION_CENTER_ROUTE } from "~/features/common/nav/routes";

describe("Action center infrastructure systems", () => {
  const monitorId = "my_infrastructure_monitor_1";

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
});
