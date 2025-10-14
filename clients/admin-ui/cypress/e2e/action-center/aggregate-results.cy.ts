import {
  stubPlus,
  stubTaxonomyEntities,
  stubWebsiteMonitor,
} from "cypress/support/stubs";

import {
  ACTION_CENTER_ROUTE,
  INTEGRATION_MANAGEMENT_ROUTE,
} from "~/features/common/nav/routes";
import { ConnectionType } from "~/types/api";

describe("Action center", () => {
  beforeEach(() => {
    cy.login();
    stubPlus(true);
    stubWebsiteMonitor();
    stubTaxonomyEntities();
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
      cy.get("[data-testid*='monitor-result-']").should("have.length", 3);
      cy.wait("@getMonitorResults").then((interception) => {
        const results = interception.response.body.items;
        results.forEach((result) => {
          const monitorKey = result.key;
          const monitorType = result.connection_type;
          const isWebMonitor =
            monitorType === ConnectionType.WEBSITE ||
            monitorType === ConnectionType.TEST_WEBSITE;
          cy.getByTestId(`monitor-result-${monitorType}-${monitorKey}`).should(
            "exist",
          );
          cy.getByTestId(`monitor-result-${monitorType}-${monitorKey}`).within(
            () => {
              cy.get(".ant-list-item-meta-avatar").should("exist");
              cy.get("[data-testid='monitor-link']")
                .should("have.text", result.name)
                .should(
                  "have.attr",
                  "href",
                  `${ACTION_CENTER_ROUTE}/${monitorKey}${isWebMonitor ? "" : "/data-explorer"}`,
                );
              cy.get("[data-testid='monitor-date']").should("contain", " ago");
            },
          );
        });
        // description
        cy.getByTestId(
          `monitor-result-${results[0].connection_type}-${results[0].key}`,
        ).should("contain", "92 Browser requests, 5 Cookies detected.");
        cy.getByTestId(
          `monitor-result-${results[2].connection_type}-${results[2].key}`,
        ).should(
          "contain",
          "22 Classifying, 13 In review, 2 Removals, 216 Unlabeled",
        );
        // date tooltip
        cy.getByTestId(
          `monitor-result-${results[0].connection_type}-${results[0].key}`,
        ).within(() => {
          cy.get("[data-testid='monitor-date']").realHover();
        });
        cy.get(".ant-tooltip-inner").should("contain", "December");
      });
    });
    it("should have appropriate actions for monitors", () => {
      // Add button
      // TODO: [HJ-337] uncomment when Add button is implemented
      // cy.getByTestId(`add-button-${webMonitorKey}`).should("exist");
      // Review button
      cy.getByTestId(`review-button-${webMonitorKey}`).should(
        "have.attr",
        "href",
        `${ACTION_CENTER_ROUTE}/${webMonitorKey}`,
      );
      cy.getByTestId(`review-button-${integrationMonitorKey}`).should(
        "have.attr",
        "href",
        `${ACTION_CENTER_ROUTE}/${integrationMonitorKey}/data-explorer`,
      );
    });
    it.skip("Should paginate results", () => {
      // TODO: mock pagination and also test skeleton loading state
    });
  });
});
