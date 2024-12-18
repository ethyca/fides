import { stubActionCenter, stubPlus } from "cypress/support/stubs";

import {
  ACTION_CENTER_ROUTE,
  INTEGRATION_MANAGEMENT_ROUTE,
} from "~/features/common/nav/v2/routes";

describe("Action center", () => {
  beforeEach(() => {
    cy.login();
    stubPlus(true);
    stubActionCenter();
  });

  describe("disabled web monitor", () => {
    beforeEach(() => {
      cy.intercept("GET", "/api/v1/config*", {
        body: {
          detection_discovery: {
            website_monitor_enabled: false,
          },
        },
      }).as("getTranslationConfig");
      cy.visit(ACTION_CENTER_ROUTE);
    });
    it("should display a message that the web monitor is disabled", () => {
      cy.wait("@getTranslationConfig");
      cy.contains("currently disabled").should("exist");
    });
  });

  describe("empty action center", () => {
    beforeEach(() => {
      cy.intercept("GET", "/api/v1/plus/discovery-monitor/aggregate-results*", {
        fixture: "empty-pagination.json",
      }).as("getMonitorResults");
      cy.visit(ACTION_CENTER_ROUTE);
    });
    it("should display empty state", () => {
      cy.wait("@getMonitorResults");
      cy.get("[data-testid='search-bar']").should("exist");
      cy.get(`[class*='ant-empty'] [class*='ant-empty-image']`).should("exist");
      cy.get(
        `[class*='ant-empty'] a[href="${INTEGRATION_MANAGEMENT_ROUTE}"]`,
      ).should("exist");
    });
  });

  describe("Action center monitor results", () => {
    const webMonitorKey = "my_web_monitor_2";
    const integrationMonitorKey = "My_New_BQ_Monitor";
    beforeEach(() => {
      cy.visit(ACTION_CENTER_ROUTE);
    });
    it("should render the current monitor results", () => {
      cy.get("[data-testid='Action center']").should("exist");
      cy.wait("@getMonitorResults");
      cy.get("[data-testid*='monitor-result-']").should("have.length", 3);
      cy.get("[data-testid^='monitor-result-']").each((result) => {
        const monitorKey = result
          .attr("data-testid")
          .replace("monitor-result-", "");
        // linked title
        cy.wrap(result)
          .contains("assets detected on")
          .should("have.attr", "href", `${ACTION_CENTER_ROUTE}/${monitorKey}`);
        // last monitored relative date with real date in tooltip
        cy.wrap(result)
          .find("[data-testid='monitor-date']")
          .contains(" ago")
          .realHover();
        cy.get(".ant-tooltip-inner").should("contain", "December");
      });
      // description
      cy.getByTestId(`monitor-result-${webMonitorKey}`).should(
        "contain",
        "92 Browser Requests, 5 Cookies detected.",
      );
      // monitor name
      cy.getByTestId(`monitor-result-${webMonitorKey}`).should(
        "contain",
        "my web monitor 2",
      );
    });
    it("should have appropriate actions for web monitors", () => {
      cy.wait("@getMonitorResults");
      // Add button
      // TODO: [HJ-337] uncomment when Add button is implemented
      // cy.getByTestId(`add-button-${webMonitorKey}`).should("exist");
      // Review button
      cy.getByTestId(`review-button-${webMonitorKey}`).should(
        "have.attr",
        "href",
        `${ACTION_CENTER_ROUTE}/${webMonitorKey}`,
      );
    });
    it.skip("Should have appropriate actions for Integrations monitors", () => {
      cy.wait("@getMonitorResults");
      // Classify button
      cy.getByTestId(`review-button-${integrationMonitorKey}`).should(
        "have.attr",
        "href",
        `${ACTION_CENTER_ROUTE}/${integrationMonitorKey}`,
      );
      // Ignore button
      cy.getByTestId(`ignore-button-${integrationMonitorKey}`).should("exist");
    });
    it.skip("Should have appropriate actions for SSO monitors", () => {
      cy.wait("@getMonitorResults");
      // Add button
      cy.getByTestId(`add-button-${webMonitorKey}`).should("exist");
      // Ignore button
      cy.getByTestId(`ignore-button-${webMonitorKey}`).should("exist");
    });
  });
});
