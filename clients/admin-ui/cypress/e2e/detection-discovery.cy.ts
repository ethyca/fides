import { stubPlus } from "cypress/support/stubs";

import { DATA_DISCOVERY_MONITORS_ROUTE } from "~/features/common/nav/v2/routes";

describe("Data discovery", () => {
  beforeEach(() => {
    cy.login();
    cy.intercept("GET", "/api/v1/plus/discovery-monitor?*", {
      fixture: "detection-discovery/monitors/list.json",
    }).as("getMonitors");
    cy.intercept("GET", "/api/v1/plus/discovery-monitor/*/results?*", {
      fixture: "detection-discovery/results/database-list.json",
    }).as("getMonitorResults");
    stubPlus(true);
  });

  describe("monitor table", () => {
    beforeEach(() => {
      cy.visit(DATA_DISCOVERY_MONITORS_ROUTE);
    });

    it("should show a monitors table", () => {
      cy.getByTestId("fidesTable").should("exist");
      cy.getByTestId("row-0").should("exist");
    });

    it("should drill down into results by clicking rows", () => {
      cy.getByTestId("row-0").click();
      cy.wait("@getMonitorResults");
      cy.getByTestId("results-breadcrumb").should("contain", "{test}");
      cy.getByTestId("row-0").click();
      cy.wait("@getMonitorResults");
      cy.getByTestId("results-breadcrumb").should(
        "contain",
        "prj-bigquery-000000"
      );
      cy.url().should("contain", "prj-bigquery-000000");
    });

    it("should show appropriate columns for the resource type", () => {});
  });
});
