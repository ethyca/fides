import {
  stubActionCenter,
  stubPlus,
  stubSystemVendors,
  stubVendorList,
} from "cypress/support/stubs";

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
      cy.wait("@getMonitorResults");
    });
    it("should render the current monitor results", () => {
      cy.get("[data-testid='Action center']").should("exist");
      cy.get("[data-testid*='monitor-result-']").should("have.length", 3);
      cy.get("[data-testid^='monitor-result-']").each((result) => {
        const monitorKey = result
          .attr("data-testid")
          .replace("monitor-result-", "");
        // property icon
        cy.wrap(result).find(".ant-list-item-meta-avatar").should("exist");
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
      cy.wait("@getSystemAggregateResults");
      cy.getByTestId("page-breadcrumb").should("contain", webMonitorKey); // little hack to make sure the webMonitorKey is available before proceeding
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
      cy.getByTestId("search-bar").should("exist");
      cy.getByTestId("pagination-btn").should("exist");
      cy.getByTestId("column-system_name").should("exist");
      cy.getByTestId("column-total_updates").should("exist");
      cy.getByTestId("column-data_use").should("exist");
      cy.getByTestId("column-locations").should("exist");
      cy.getByTestId("column-domains").should("exist");
      cy.getByTestId("column-actions").should("exist");
      cy.getByTestId("row-0-col-system_name").within(() => {
        cy.getByTestId("change-icon").should("exist");
        cy.contains("Uncategorized assets").should("exist");
      });
      cy.getByTestId("row-3-col-system_name").within(() => {
        cy.getByTestId("change-icon").should("exist"); // new system
      });
      // data use column should be empty for uncategorized assets
      cy.getByTestId("row-0-col-data_use").should("be.empty");
      // cy.getByTestId("row-1-col-system_name").within(() => {
      //   cy.getByTestId("change-icon").should("not.exist"); // existing result
      //   cy.contains("Google Tag Manager").should("exist");
      // });
      // data use column should not be empty for other assets
      cy.getByTestId("row-1-col-data_use").children().should("have.length", 1);

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
      cy.getByTestId("row-0-col-actions").within(() => {
        cy.getByTestId("add-btn").should("be.disabled");
      });
    });
    it("should ignore all assets in an uncategorized system", () => {
      cy.getByTestId("row-0-col-actions").within(() => {
        cy.getByTestId("ignore-btn").click({ force: true });
      });
      cy.wait("@ignoreMonitorResultUncategorizedSystem");
      cy.getByTestId("success-alert").should(
        "contain",
        "108 uncategorized assets have been ignored and will not appear in future scans.",
      );
    });
    it("should add all assets in a categorized system", () => {
      cy.getByTestId("row-1-col-actions").within(() => {
        cy.getByTestId("add-btn").click({ force: true });
      });
      cy.wait("@addMonitorResultSystem");
      cy.getByTestId("success-alert").should(
        "contain",
        "10 assets from Google Tag Manager have been added to the system inventory.",
      );
    });
    it("should ignore all assets in a categorized system", () => {
      cy.getByTestId("row-1-col-actions").within(() => {
        cy.getByTestId("ignore-btn").click({ force: true });
      });
      cy.wait("@ignoreMonitorResultSystem");
      cy.getByTestId("success-alert").should(
        "contain",
        "10 assets from Google Tag Manager have been ignored and will not appear in future scans.",
      );
    });
    it("shouldn't allow bulk add when uncategorized system is selected", () => {
      cy.getByTestId("row-0-col-select").find("label").click();
      cy.getByTestId("selected-count").should("contain", "1 selected");
      cy.getByTestId("bulk-actions-menu").click();
      cy.getByTestId("bulk-add").should("be.disabled");
    });
    it("should bulk add results from categorized systems", () => {
      cy.getByTestId("bulk-actions-menu").should("be.disabled");
      cy.getByTestId("row-1-col-select").find("label").click();
      cy.getByTestId("row-2-col-select").find("label").click();
      cy.getByTestId("selected-count").should("contain", "2 selected");
      cy.getByTestId("bulk-actions-menu").should("not.be.disabled");
      cy.getByTestId("bulk-actions-menu").click();
      cy.getByTestId("bulk-add").click();
      cy.wait("@addMonitorResultSystem");
      cy.getByTestId("success-alert").should(
        "contain",
        "16 assets have been added to the system inventory.",
      );
    });
    it("should bulk ignore results from all systems", () => {
      cy.getByTestId("row-0-col-select").find("label").click();
      cy.getByTestId("row-1-col-select").find("label").click();
      cy.getByTestId("row-2-col-select").find("label").click();
      cy.getByTestId("selected-count").should("contain", "3 selected");
      cy.getByTestId("bulk-actions-menu").should("not.be.disabled");
      cy.getByTestId("bulk-actions-menu").click();
      cy.getByTestId("bulk-ignore").click();
      cy.wait("@ignoreMonitorResultSystem");
      cy.getByTestId("success-alert").should(
        "contain",
        "124 assets have been ignored and will not appear in future scans.",
      );
    });
    it("should navigate to table view on row click", () => {
      cy.getByTestId("row-1-col-system_name").click();
      cy.url().should(
        "contain",
        "system_key-8fe42cdb-af2e-4b9e-9b38-f75673180b88",
      );
      cy.getByTestId("page-breadcrumb").should(
        "contain",
        "system_key-8fe42cdb-af2e-4b9e-9b38-f75673180b88",
      );
    });
  });

  describe("Action center assets uncategorized results", () => {
    const webMonitorKey = "my_web_monitor_1";
    const systemId = "[undefined]";
    beforeEach(() => {
      cy.visit(`${ACTION_CENTER_ROUTE}/${webMonitorKey}/${systemId}`);
      cy.wait("@getSystemAssetsUncategorized");
      cy.getByTestId("page-breadcrumb").should("contain", "Uncategorized");
    });
    it("should render uncategorized asset results view", () => {
      cy.getByTestId("search-bar").should("exist");
      cy.getByTestId("pagination-btn").should("exist");
      cy.getByTestId("bulk-actions-menu").should("be.disabled");
      cy.getByTestId("add-all").should("be.disabled");

      // table columns
      cy.getByTestId("column-select").should("exist");
      cy.getByTestId("column-name").should("exist");
      cy.getByTestId("column-resource_type").should("exist");
      cy.getByTestId("column-system").should("exist");
      // TODO: [HJ-369] uncomment when data use column is implemented
      // cy.getByTestId("column-data_use").should("exist");
      cy.getByTestId("column-locations").should("exist");
      cy.getByTestId("column-domain").should("exist");
      // TODO: [HJ-344] uncomment when Discovery column is implemented
      /* cy.getByTestId("column-with_consent").should("exist");
      cy.getByTestId("row-4-col-with_consent")
        .contains("Without consent")
        .realHover();
      cy.get(".ant-tooltip-inner").should("contain", "January"); */
      cy.getByTestId("column-actions").should("exist");
      cy.getByTestId("row-0-col-actions").within(() => {
        cy.getByTestId("add-btn").should("be.disabled");
        cy.getByTestId("ignore-btn").should("exist");
      });
    });
    it("should allow adding a system on uncategorized assets", () => {
      cy.getByTestId("row-0-col-system").within(() => {
        cy.getByTestId("add-system-btn").click();
      });
      cy.wait("@getSystemsPaginated");
      cy.getByTestId("system-select").antSelect("Fidesctl System");
      cy.wait("@setAssetSystem");
      cy.getByTestId("system-select").should("not.exist");
      cy.getByTestId("success-alert").should(
        "contain",
        'Browser Request "0d22c925-3a81-4f10-bfdc-69a5d67e93bc" has been assigned to Fidesctl System.',
      );
    });
  });

  describe("Action center assets categorized results", () => {
    const webMonitorKey = "my_web_monitor_1";
    const systemId = "system_key-8fe42cdb-af2e-4b9e-9b38-f75673180b88";
    const systemName = "Google Tag Manager";
    beforeEach(() => {
      cy.visit(`${ACTION_CENTER_ROUTE}/${webMonitorKey}/${systemId}`);
      cy.wait("@getSystemAssetResults");
      cy.getByTestId("page-breadcrumb").should("contain", systemName); // little hack to make sure the systemName is available before proceeding
    });
    it("should render asset results view", () => {
      cy.getByTestId("search-bar").should("exist");
      cy.getByTestId("pagination-btn").should("exist");
      cy.getByTestId("bulk-actions-menu").should("be.disabled");
      cy.getByTestId("add-all").should("exist");

      // table columns
      cy.getByTestId("column-select").should("exist");
      cy.getByTestId("column-name").should("exist");
      cy.getByTestId("column-resource_type").should("exist");
      cy.getByTestId("column-system").should("exist");
      // TODO: [HJ-369] uncomment when data use column is implemented
      // cy.getByTestId("column-data_use").should("exist");
      cy.getByTestId("column-locations").should("exist");
      cy.getByTestId("column-domain").should("exist");
      // TODO: [HJ-344] uncomment when Discovery column is implemented
      /* cy.getByTestId("column-with_consent").should("exist");
      cy.getByTestId("row-4-col-with_consent")
        .contains("Without consent")
        .realHover();
      cy.get(".ant-tooltip-inner").should("contain", "January"); */
      cy.getByTestId("column-actions").should("exist");
      cy.getByTestId("row-0-col-actions").within(() => {
        cy.getByTestId("add-btn").should("exist");
        cy.getByTestId("ignore-btn").should("exist");
      });
    });
    it("should allow editing a system on categorized assets", () => {
      cy.getByTestId("row-3-col-system").within(() => {
        cy.getByTestId("system-badge").click();
      });
      cy.wait("@getSystemsPaginated");
      cy.getByTestId("system-select").antSelect("Fidesctl System");
      cy.wait("@setAssetSystem");
      cy.getByTestId("system-select").should("not.exist");
      cy.getByTestId("success-alert").should(
        "contain",
        'Browser Request "destination" has been assigned to Fidesctl System.',
      );

      // Wait for previous UI animations to reset or Cypress chokes on the next part
      // eslint-disable-next-line cypress/no-unnecessary-waiting
      cy.wait(100);

      // Now test with search
      cy.getByTestId("row-2-col-system").within(() => {
        cy.getByTestId("system-badge").click();
        cy.getByTestId("system-select").find("input").type("demo m");
        cy.wait("@getSystemsWithSearch").then((interception) => {
          expect(interception.request.query.search).to.eq("demo m");
        });
      });
      cy.wait("@getSystemsPaginated");
      cy.getByTestId("system-select").antSelect("Demo Marketing System");
      cy.wait("@setAssetSystem");
      cy.getByTestId("success-alert").should("exist");
      cy.getByTestId("system-select").should("not.exist");
      cy.getByTestId("success-alert").should(
        "contain",
        'Browser Request "collect" has been assigned to Demo Marketing System.',
      );
    });
    it("should allow creating a new system and assigning an asset to it", () => {
      stubVendorList();
      stubSystemVendors();
      cy.getByTestId("row-4-col-system").within(() => {
        cy.getByTestId("system-badge").click();
      });
      cy.wait("@getSystemsPaginated");
      cy.getByTestId("add-new-system").click();
      cy.getByTestId("add-modal-content").should("exist");
      cy.getByTestId("vendor-name-select").antSelect("Aniview LTD");
      cy.getByTestId("save-btn").click();
      // adds new system
      cy.wait("@postSystemVendors");
      // assigns asset to new system
      cy.wait("@setAssetSystem");
      cy.getByTestId("success-alert").should(
        "contain",
        'Test System has been added to your system inventory and the Browser Request "gtm.js" has been assigned to that system.',
      );
    });
    it("should add individual assets", () => {
      cy.getByTestId("row-0-col-actions").within(() => {
        cy.getByTestId("add-btn").click({ force: true });
      });
      cy.wait("@addAssets");
      cy.getByTestId("success-alert").should(
        "contain",
        'Browser Request "11020051272" has been added to the system inventory.',
      );
    });
    it("should ignore individual assets", () => {
      cy.getByTestId("row-0-col-actions").within(() => {
        cy.getByTestId("ignore-btn").click({ force: true });
      });
      cy.wait("@ignoreAssets");
      cy.getByTestId("success-alert").should(
        "contain",
        'Browser Request "11020051272" has been ignored and will not appear in future scans.',
      );
    });
    it("should bulk add assets", () => {
      cy.getByTestId("bulk-actions-menu").should("be.disabled");
      cy.getByTestId("row-0-col-select").find("label").click();
      cy.getByTestId("row-2-col-select").find("label").click();
      cy.getByTestId("row-3-col-select").find("label").click();
      cy.getByTestId("selected-count").should("contain", "3 selected");
      cy.getByTestId("bulk-actions-menu").should("not.be.disabled");
      cy.getByTestId("bulk-actions-menu").click();
      cy.getByTestId("bulk-add").click();
      cy.wait("@addAssets");
      cy.getByTestId("success-alert").should(
        "contain",
        "3 assets from Google Tag Manager have been added to the system inventory.",
      );
    });
    it("should bulk ignore assets", () => {
      cy.getByTestId("bulk-actions-menu").should("be.disabled");
      cy.getByTestId("row-0-col-select").find("label").click();
      cy.getByTestId("row-2-col-select").find("label").click();
      cy.getByTestId("row-3-col-select").find("label").click();
      cy.getByTestId("selected-count").should("contain", "3 selected");
      cy.getByTestId("bulk-actions-menu").should("not.be.disabled");
      cy.getByTestId("bulk-actions-menu").click();
      cy.getByTestId("bulk-ignore").click();
      cy.wait("@ignoreAssets");
      cy.getByTestId("success-alert").should(
        "contain",
        "3 assets from Google Tag Manager have been ignored and will not appear in future scans.",
      );
    });
    it("should add all assets", () => {
      cy.intercept(
        "POST",
        "/api/v1/plus/discovery-monitor/*/promote*",
        (req) => {
          req.on("response", (res) => {
            res.setDelay(100); // slight delay allows us to check for the loading state below
          });
        },
      ).as("slowRequest");
      cy.getByTestId("add-all").click();
      cy.getByTestId("add-all").should("have.class", "ant-btn-loading");
      cy.wait("@slowRequest");
      cy.url().should("not.contain", systemId);
      cy.getByTestId("success-alert").should(
        "contain",
        "11 assets from Google Tag Manager have been added to the system inventory.",
      );
    });
    it("should bulk assign assets to a system", () => {
      cy.getByTestId("bulk-actions-menu").should("be.disabled");
      cy.getByTestId("row-0-col-select").find("label").click();
      cy.getByTestId("row-2-col-select").find("label").click();
      cy.getByTestId("row-3-col-select").find("label").click();
      cy.getByTestId("selected-count").should("contain", "3 selected");
      cy.getByTestId("bulk-actions-menu").should("not.be.disabled");
      cy.getByTestId("bulk-actions-menu").click();
      cy.getByTestId("bulk-assign-system").click();
      cy.getByTestId("add-modal-content").should("be.visible");
      cy.getByTestId("system-select").antSelect("Fidesctl System");
      cy.getByTestId("save-btn").click();
      cy.wait("@setAssetSystem");
      cy.getByTestId("success-alert").should(
        "contain",
        "3 assets have been assigned to Fidesctl System.",
      );
    });
  });
});
