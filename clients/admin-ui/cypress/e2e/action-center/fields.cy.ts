import { stubPlus, stubTaxonomyEntities } from "cypress/support/stubs";

import { ACTION_CENTER_ROUTE } from "~/features/common/nav/routes";

describe("Action center fields", () => {
  const monitorId = "my_bigquery_monitor";

  describe("error handling", () => {
    beforeEach(() => {
      cy.login();
      stubPlus(true);
      stubTaxonomyEntities();
      cy.intercept(
        "GET",
        `/api/v1/plus/discovery-monitor/${monitorId}/fields*`,
        {
          statusCode: 500,
          body: { detail: "Internal server error" },
        },
      ).as("getMonitorFieldsError");
    });

    it("should display error page when fetching monitor fields fails", () => {
      cy.visit(`${ACTION_CENTER_ROUTE}/datastore/${monitorId}`);
      cy.wait("@getMonitorFieldsError");

      cy.getByTestId("error-page-result").should("exist");
      cy.getByTestId("error-page-result").within(() => {
        cy.contains("Error 500").should("exist");
        cy.contains("Internal server error").should("exist");
        cy.contains("Reload").should("exist");
      });
    });
  });
});
