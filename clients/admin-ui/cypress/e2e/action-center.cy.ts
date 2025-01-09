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

  describe("Action center monitor aggregate results", () => {
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
          .contains("assets detected")
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
    it.skip("Should paginate results", () => {
      // TODO: mock pagination and also test skeleton loading state
    });
  });

  describe("Action center system aggregate results", () => {
    const webMonitorKey = "my_web_monitor_1";
    beforeEach(() => {
      cy.visit(`${ACTION_CENTER_ROUTE}/${webMonitorKey}`);
    });
    it("should display a breadcrumb", () => {
      cy.getByTestId("page-breadcrumb").within(() => {
        cy.get("a.ant-breadcrumb-link")
          .should("contain", "All activity")
          .should("have.attr", "href", ACTION_CENTER_ROUTE);
        cy.contains("my_web_monitor_1").should("exist");
      });
    });
    it("should render the aggregated system results in a table", () => {
      cy.wait("@getSystemAggregateResults");
      cy.getByTestId("column-system_name").should("exist");
      cy.getByTestId("column-total_updates").should("exist");
      cy.getByTestId("column-data_use").should("exist");
      cy.getByTestId("column-locations").should("exist");
      cy.getByTestId("column-domains").should("exist");
      cy.getByTestId("column-actions").should("exist");
      cy.getByTestId("search-bar").should("exist");
      cy.getByTestId("pagination-btn").should("exist");
      cy.getByTestId("row-0-col-system_name").within(() => {
        cy.getByTestId("change-icon").should("exist"); // new result
        cy.contains("Uncategorized assets").should("exist");
      });
      // data use column should be empty for uncategorized assets
      cy.getByTestId("row-0-col-data_use").children().should("have.length", 0);
      cy.getByTestId("row-1-col-system_name").within(() => {
        cy.getByTestId("change-icon").should("not.exist"); // existing result
        cy.contains("Google Tag Manager").should("exist");
      });
      // TODO: data use column should not be empty for other assets
      // cy.getByTestId("row-1-col-data_use").children().should("not.have.length", 0);

      // multiple locations
      cy.getByTestId("row-2-col-locations").should("contain", "2 locations");
      // single location
      cy.getByTestId("row-3-col-locations").should("contain", "USA");

      // multiple domains
      cy.getByTestId("row-0-col-domains").should("contain", "29 domains");
      // single domain
      cy.getByTestId("row-3-col-domains").should(
        "contain",
        "analytics.google.com",
      );
    });
    // it("should navigate to table view on row click", () => {
    //   cy.getByTestId("row-1").click();
    //   cy.url().should("contain", "fds.1046");
    //   cy.getByTestId("page-breadcrumb").should("contain", "fds.1046");
    // });
  });
});
