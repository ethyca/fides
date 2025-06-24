import {
  stubPlus,
  stubSystemVendors,
  stubTaxonomyEntities,
  stubVendorList,
  stubWebsiteMonitor,
} from "cypress/support/stubs";

import {
  ACTION_CENTER_ROUTE,
  INTEGRATION_MANAGEMENT_ROUTE,
  UNCATEGORIZED_SEGMENT,
} from "~/features/common/nav/routes";

describe("Action center", () => {
  beforeEach(() => {
    cy.login();
    stubPlus(true);
    stubWebsiteMonitor();
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
        "92 Browser requests, 5 Cookies detected.",
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
    const rowIds = [
      UNCATEGORIZED_SEGMENT,
      "system_key-8fe42cdb-af2e-4b9e-9b38-f75673180b88",
      "system_key-652c8984-ade7-470b-bce4-7e184621be9d",
      "fds.1047",
    ];

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
      cy.getByTestId(`row-${rowIds[0]}-col-system_name`).within(() => {
        cy.getByTestId("change-icon").should("exist");
        cy.contains("Uncategorized assets").should("exist");
      });
      cy.getByTestId(`row-${rowIds[3]}-col-system_name`).within(() => {
        cy.getByTestId("change-icon").should("exist"); // new system
      });
      // data use column should be empty for uncategorized assets
      cy.getByTestId(`row-${rowIds[0]}-col-data_use`).should("be.empty");
      // cy.getByTestId("row-1-col-system_name").within(() => {
      //   cy.getByTestId("change-icon").should("not.exist"); // existing result
      //   cy.contains("Google Tag Manager").should("exist");
      // });
      // data use column should not be empty for other assets
      cy.getByTestId(`row-${rowIds[1]}-col-data_use`)
        .children()
        .should("have.length", 1);

      // multiple locations
      cy.getByTestId(`row-${rowIds[2]}-col-locations`)
        .should("contain", "United States")
        .and("contain", "Canada");
      // single location
      cy.getByTestId(`row-${rowIds[3]}-col-locations`).should(
        "contain",
        "United States",
      );

      // multiple domains
      cy.getByTestId(`row-${rowIds[0]}-col-domains`)
        .should("contain", "29 domains")
        .within(() => {
          cy.get("button").click({ force: true });
          cy.get("li").should("have.length", 29);
        });
      // single domain
      cy.getByTestId(`row-${rowIds[3]}-col-domains`).should(
        "contain",
        "analytics.google.com",
      );
      cy.getByTestId(`row-${rowIds[0]}-col-actions`).within(() => {
        cy.getByTestId("add-btn").should("be.disabled");
      });
    });
    it("should ignore all assets in an uncategorized system", () => {
      cy.getByTestId(`row-${rowIds[0]}-col-actions`).within(() => {
        cy.getByTestId("ignore-btn").click({ force: true });
      });
      cy.wait("@ignoreMonitorResultSystem").then((interception) => {
        expect(interception.request.url).to.contain("[undefined]");
      });
      cy.getByTestId("toast-success-msg").should(
        "contain",
        "108 uncategorized assets have been ignored and will not appear in future scans.",
      );
    });
    it("should add all assets in a categorized system", () => {
      cy.getByTestId(`row-${rowIds[1]}-col-actions`).within(() => {
        cy.getByTestId("add-btn").click({ force: true });
      });
      cy.wait("@addMonitorResultSystem");
      cy.getByTestId("toast-success-msg").should(
        "contain",
        "10 assets from Google Tag Manager have been added to the system inventory.",
      );
    });
    it("should ignore all assets in a categorized system", () => {
      cy.getByTestId(`row-${rowIds[1]}-col-actions`).within(() => {
        cy.getByTestId("ignore-btn").click({ force: true });
      });
      cy.wait("@ignoreMonitorResultSystem");
      cy.getByTestId("toast-success-msg").should(
        "contain",
        "10 assets from Google Tag Manager have been ignored and will not appear in future scans.",
      );
    });
    it("shouldn't allow bulk add when uncategorized system is selected", () => {
      cy.getByTestId(`row-${rowIds[0]}-col-select`).find("label").click();
      cy.getByTestId("selected-count").should("contain", "1 selected");
      cy.getByTestId("bulk-actions-menu").click();
      cy.get(".ant-dropdown-menu-item")
        .first()
        .should("have.class", "ant-dropdown-menu-item-disabled");
    });
    it("should bulk add results from categorized systems", () => {
      cy.getByTestId("bulk-actions-menu").should("be.disabled");
      cy.getByTestId(`row-${rowIds[1]}-col-select`).find("label").click();
      cy.getByTestId(`row-${rowIds[2]}-col-select`).find("label").click();
      cy.getByTestId("selected-count").should("contain", "2 selected");
      cy.getByTestId("bulk-actions-menu").should("not.be.disabled");
      cy.getByTestId("bulk-actions-menu").click();
      cy.get(".ant-dropdown-menu-item").contains("Add").click();
      cy.wait("@addMonitorResultSystem");
      cy.getByTestId("toast-success-msg").should(
        "contain",
        "16 assets have been added to the system inventory.",
      );
    });
    it("should bulk ignore results from all systems", () => {
      cy.getByTestId(`row-${rowIds[0]}-col-select`).find("label").click();
      cy.getByTestId(`row-${rowIds[1]}-col-select`).find("label").click();
      cy.getByTestId(`row-${rowIds[2]}-col-select`).find("label").click();
      cy.getByTestId("selected-count").should("contain", "3 selected");
      cy.getByTestId("bulk-actions-menu").should("not.be.disabled");
      cy.getByTestId("bulk-actions-menu").click();
      cy.get(".ant-dropdown-menu-item").contains("Ignore").click();
      cy.wait("@ignoreMonitorResultSystem");
      cy.getByTestId("toast-success-msg").should(
        "contain",
        "124 assets have been ignored and will not appear in future scans.",
      );
    });
    it("should navigate to table view on row click", () => {
      cy.getByTestId(`row-${rowIds[1]}-col-system_name`).click();
      cy.url().should(
        "contain",
        "system_key-8fe42cdb-af2e-4b9e-9b38-f75673180b88",
      );
      cy.getByTestId("page-breadcrumb").should(
        "contain",
        "system_key-8fe42cdb-af2e-4b9e-9b38-f75673180b88",
      );
    });

    describe("tab navigation", () => {
      it("updates URL hash when switching tabs", () => {
        cy.visit(`${ACTION_CENTER_ROUTE}/${webMonitorKey}#attention-required`);
        cy.location("hash").should("eq", "#attention-required");

        // eslint-disable-next-line cypress/no-unnecessary-waiting
        cy.wait(500);
        cy.getAntTab("Recent activity").click({ force: true });
        cy.location("hash").should("eq", "#recent-activity");

        // "recent activity" tab should be read-only
        cy.getByTestId("bulk-actions-menu").should("be.disabled");
        cy.getByTestId(`row-${rowIds[0]}-col-select`).should("not.exist");
        cy.getByTestId(`row-${rowIds[0]}-col-actions`).should("not.exist");

        // eslint-disable-next-line cypress/no-unnecessary-waiting
        cy.wait(500);
        cy.getAntTab("Ignored").click({ force: true });
        cy.location("hash").should("eq", "#ignored");
        // "ignore" option should not show in bulk actions menu
        cy.getByTestId(`row-${rowIds[0]}-col-select`).find("label").click();
        cy.getByTestId(`row-${rowIds[2]}-col-select`).find("label").click();
        cy.getByTestId(`row-${rowIds[3]}-col-select`).find("label").click();
        cy.getByTestId("bulk-actions-menu").click();
        cy.getByTestId("bulk-ignore").should("not.exist");
      });

      it("maintains hash when clicking on a row", () => {
        // no hash
        cy.visit(`${ACTION_CENTER_ROUTE}/${webMonitorKey}`);
        cy.getByTestId(`row-${rowIds[0]}-col-system_name`).click();
        cy.location("hash").should("eq", "");

        // eslint-disable-next-line cypress/no-unnecessary-waiting
        cy.wait(500);
        cy.visit(`${ACTION_CENTER_ROUTE}/${webMonitorKey}#attention-required`);
        cy.getByTestId(`row-${rowIds[0]}-col-system_name`).click();
        cy.location("hash").should("eq", "#attention-required");

        // eslint-disable-next-line cypress/no-unnecessary-waiting
        cy.wait(500);
        cy.visit(`${ACTION_CENTER_ROUTE}/${webMonitorKey}#recent-activity`);
        cy.getByTestId(`row-${rowIds[0]}-col-system_name`).click();
        cy.location("hash").should("eq", "#recent-activity");

        // eslint-disable-next-line cypress/no-unnecessary-waiting
        cy.wait(500);
        cy.visit(`${ACTION_CENTER_ROUTE}/${webMonitorKey}#ignored`);
        cy.getByTestId(`row-${rowIds[0]}-col-system_name`).click();
        cy.location("hash").should("eq", "#ignored");
      });
    });
  });

  describe("Action center assets uncategorized results", () => {
    const webMonitorKey = "my_web_monitor_1";
    const systemId = "[undefined]";
    const firstRowUrn =
      "my_web_monitor_1.forms.hubspot.com.https://forms.hubspot.com/submissions-validation/v1/validate/7252764/0d22c925-3a81-4f10-bfdc-69a5d67e93bc";
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
      cy.getByTestId("column-data_use").should("exist");
      cy.getByTestId("column-locations").should("exist");
      cy.getByTestId("column-domain").should("exist");
      // TODO: [HJ-344] uncomment when Discovery column is implemented
      /* cy.getByTestId("column-with_consent").should("exist");
      cy.getByTestId("row-4-col-with_consent")
        .contains("Without consent")
        .realHover();
      cy.get(".ant-tooltip-inner").should("contain", "January"); */
      cy.getByTestId("column-actions").should("exist");
      cy.getByTestId(`row-${firstRowUrn}-col-actions`).within(() => {
        cy.getByTestId("add-btn").should("be.disabled");
        cy.getByTestId("ignore-btn").should("exist");
      });
    });
    it("should allow adding a system on uncategorized assets", () => {
      cy.getByTestId(`row-${firstRowUrn}-col-system`).within(() => {
        cy.getByTestId("add-system-btn").click();
      });
      cy.wait("@getSystemsPaginated");
      cy.getByTestId("system-select").antSelect("Fidesctl System");
      cy.wait("@patchAssets");
      cy.getByTestId("system-select").should("not.exist");
      cy.getByTestId("success-alert").should(
        "contain",
        'Browser request "0d22c925-3a81-4f10-bfdc-69a5d67e93bc" has been assigned to Fidesctl System.',
      );
    });
  });

  describe("Action center assets categorized results", () => {
    const webMonitorKey = "my_web_monitor_1";
    const systemId = "system_key-8fe42cdb-af2e-4b9e-9b38-f75673180b88";
    const systemName = "Google Tag Manager";
    const rowUrns = [
      "my_web_monitor_1.GET.td.doubleclick.net.https://td.doubleclick.net/td/rul/11020051272",
      "my_web_monitor_1.GET.td.doubleclick.net.https://td.doubleclick.net/td/rul/697301175",
      "my_web_monitor_1.POST.www.google.com.https://www.google.com/ccm/collect",
      "my_web_monitor_1.GET.www.googletagmanager.com.https://www.googletagmanager.com/gtag/destination",
      "my_web_monitor_1.GET.www.googletagmanager.com.https://www.googletagmanager.com/gtm.js",
    ];

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
      cy.getByTestId("column-data_use").should("exist");
      cy.getByTestId("column-locations").should("exist");
      cy.getByTestId("column-domain").should("exist");
      // TODO: [HJ-344] uncomment when Discovery column is implemented
      /* cy.getByTestId("column-with_consent").should("exist");
      cy.getByTestId("row-4-col-with_consent")
        .contains("Without consent")
        .realHover();
      cy.get(".ant-tooltip-inner").should("contain", "January"); */
      cy.getByTestId("column-page").should("exist");
      cy.getByTestId(`row-${rowUrns[0]}-col-page`).should(
        "contain",
        "single_page",
      );
      cy.getByTestId(`row-${rowUrns[1]}-col-page`).within(() => {
        cy.get("p").should("contain", "3 pages");
        cy.get("button").click({ force: true });
        cy.get("li").should("have.length", 3);
      });
      // show nothing when page field is undefined or []
      cy.getByTestId(`row-${rowUrns[2]}-col-page`).should("be.empty");
      cy.getByTestId(`row-${rowUrns[3]}-col-page`).should("be.empty");
      cy.getByTestId("column-actions").should("exist");
      cy.getByTestId(`row-${rowUrns[0]}-col-actions`).within(() => {
        cy.getByTestId("add-btn").should("exist");
        cy.getByTestId("ignore-btn").should("exist");
      });
    });
    it("should allow editing a system on categorized assets", () => {
      cy.getByTestId(`row-${rowUrns[3]}-col-system`).within(() => {
        cy.getByTestId("system-badge").click();
      });
      cy.wait("@getSystemsPaginated");
      cy.getByTestId("system-select").antSelect("Fidesctl System");
      cy.wait("@patchAssets");
      cy.getByTestId("system-select").should("not.exist");
      cy.getByTestId("success-alert").should(
        "contain",
        'Browser request "destination" has been assigned to Fidesctl System.',
      );

      // Wait for previous UI animations to reset or Cypress chokes on the next part
      // eslint-disable-next-line cypress/no-unnecessary-waiting
      cy.wait(100);

      // Now test with search
      cy.getByTestId(`row-${rowUrns[2]}-col-system`).within(() => {
        cy.getByTestId("system-badge").click({ force: true });
        cy.getByTestId("system-select").find("input").type("demo m");
        cy.wait("@getSystemsWithSearch").then((interception) => {
          expect(interception.request.query.search).to.eq("demo m");
        });
      });
      cy.wait("@getSystemsPaginated");
      cy.getByTestId("system-select").antSelect("Demo Marketing System");
      cy.wait("@patchAssets");
      cy.getByTestId("success-alert").should("exist");
      cy.getByTestId("system-select").should("not.exist");
      cy.getByTestId("success-alert").should(
        "contain",
        'Browser request "collect" has been assigned to Demo Marketing System.',
      );
    });
    it("should allow creating a new system and assigning an asset to it", () => {
      stubVendorList();
      stubSystemVendors();
      cy.getByTestId(`row-${rowUrns[4]}-col-system`).within(() => {
        cy.getByTestId("system-badge").click();
      });
      cy.wait("@getSystemsPaginated");
      cy.getByTestId("add-new-system").click({ force: true });
      cy.getByTestId("add-modal-content").should("exist");
      cy.getByTestId("vendor-name-select").antSelect("Aniview LTD");
      cy.getByTestId("save-btn").click();
      // adds new system
      cy.wait("@postSystemVendors");
      // assigns asset to new system
      cy.wait("@patchAssets");
      cy.getByTestId("success-alert").should(
        "contain",
        'Test System has been added to your system inventory and the Browser request "gtm.js" has been assigned to that system.',
      );
    });
    it("should add individual assets", () => {
      cy.getByTestId(`row-${rowUrns[0]}-col-actions`).within(() => {
        cy.getByTestId("add-btn").click({ force: true });
      });
      cy.wait("@addAssets");
      cy.getByTestId("toast-success-msg").should(
        "contain",
        'Browser request "11020051272" has been added to the system inventory.',
      );
    });
    it("should ignore individual assets", () => {
      cy.getByTestId(`row-${rowUrns[0]}-col-actions`).within(() => {
        cy.getByTestId("ignore-btn").click({ force: true });
      });
      cy.wait("@ignoreAssets");
      cy.getByTestId("toast-success-msg").should(
        "contain",
        'Browser request "11020051272" has been ignored and will not appear in future scans.',
      );
    });

    it("should restore individual ignored assets", () => {
      cy.getByTestId(`row-${rowUrns[1]}-col-actions`).within(() => {
        cy.getByTestId("restore-btn").click({ force: true });
      });
      cy.wait("@restoreAssets");
      cy.getByTestId("toast-success-msg").should(
        "contain",
        'Browser request "697301175" is no longer ignored and will appear in future scans.',
      );
    });
    it("should bulk add assets", () => {
      cy.getByTestId("bulk-actions-menu").should("be.disabled");
      cy.getByTestId(`row-${rowUrns[0]}-col-select`).find("label").click();
      cy.getByTestId(`row-${rowUrns[2]}-col-select`).find("label").click();
      cy.getByTestId(`row-${rowUrns[3]}-col-select`).find("label").click();
      cy.getByTestId("selected-count").should("contain", "3 selected");
      cy.getByTestId("bulk-actions-menu").should("not.be.disabled");
      cy.getByTestId("bulk-actions-menu").click();
      cy.get(".ant-dropdown-menu-item").contains("Add").click();
      cy.wait("@addAssets");
      cy.getByTestId("toast-success-msg").should(
        "contain",
        "3 assets from Google Tag Manager have been added to the system inventory.",
      );
    });
    it("should bulk ignore assets", () => {
      cy.getByTestId("bulk-actions-menu").should("be.disabled");
      cy.getByTestId(`row-${rowUrns[0]}-col-select`).find("label").click();
      cy.getByTestId(`row-${rowUrns[2]}-col-select`).find("label").click();
      cy.getByTestId(`row-${rowUrns[3]}-col-select`).find("label").click();
      cy.getByTestId("selected-count").should("contain", "3 selected");
      cy.getByTestId("bulk-actions-menu").should("not.be.disabled");
      cy.getByTestId("bulk-actions-menu").click();
      cy.get(".ant-dropdown-menu-item").contains("Ignore").click();
      cy.wait("@ignoreAssets");
      cy.getByTestId("toast-success-msg").should(
        "contain",
        "3 assets from Google Tag Manager have been ignored and will not appear in future scans.",
      );
    });

    it("should bulk restore ignored assets", () => {
      cy.getAntTab("Ignored").click({ force: true });
      cy.getByTestId("bulk-actions-menu").should("be.disabled");
      cy.getByTestId(`row-${rowUrns[0]}-col-select`).find("label").click();
      cy.getByTestId(`row-${rowUrns[2]}-col-select`).find("label").click();
      cy.getByTestId("selected-count").should("contain", "2 selected");
      cy.getByTestId("bulk-actions-menu").should("not.be.disabled");
      cy.getByTestId("bulk-actions-menu").click();
      cy.get(".ant-dropdown-menu-item").contains("Restore").click();
      cy.wait("@restoreAssets");
      cy.getByTestId("toast-success-msg").should(
        "contain",
        "2 assets have been restored and will appear in future scans.",
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
      cy.getByTestId("toast-success-msg").should(
        "contain",
        "11 assets from Google Tag Manager have been added to the system inventory.",
      );
    });

    it("should bulk assign assets to a system", () => {
      cy.getByTestId("bulk-actions-menu").should("be.disabled");
      cy.getByTestId(`row-${rowUrns[0]}-col-select`).find("label").click();
      cy.getByTestId(`row-${rowUrns[2]}-col-select`).find("label").click();
      cy.getByTestId(`row-${rowUrns[3]}-col-select`).find("label").click();
      cy.getByTestId("selected-count").should("contain", "3 selected");
      cy.getByTestId("bulk-actions-menu").should("not.be.disabled");
      cy.getByTestId("bulk-actions-menu").click();
      cy.get(".ant-dropdown-menu-item").contains("Assign system").click();
      cy.getByTestId("add-modal-content").should("be.visible");
      cy.getByTestId("system-select").antSelect("Fidesctl System");
      cy.getByTestId("save-btn").click();
      cy.wait("@patchAssets");
      cy.getByTestId("toast-success-msg").should(
        "contain",
        "3 assets have been assigned to Fidesctl System.",
      );
    });

    it("should bulk add data uses to assets", () => {
      stubTaxonomyEntities();
      cy.getByTestId("bulk-actions-menu").should("be.disabled");
      cy.getByTestId(`row-${rowUrns[0]}-col-select`).find("label").click();
      cy.getByTestId(`row-${rowUrns[2]}-col-select`).find("label").click();
      cy.getByTestId(`row-${rowUrns[3]}-col-select`).find("label").click();
      cy.getByTestId("selected-count").should("contain", "3 selected");
      cy.getByTestId("bulk-actions-menu").should("not.be.disabled");
      cy.getByTestId("bulk-actions-menu").click();
      cy.get(".ant-dropdown-menu-item")
        .contains("Add consent category")
        .click();
      cy.getByTestId("taxonomy-select").antSelect("essential");
      cy.getByTestId("save-btn").click({ force: true });
      cy.wait("@patchAssets");
      cy.getByTestId("toast-success-msg").should(
        "contain",
        "Consent categories added to 3 assets from Google Tag Manager.",
      );
      cy.getByTestId(`row-${rowUrns[0]}-col-select`).within(() => {
        cy.get("input").should("have.attr", "checked");
      });
      cy.getByTestId(`row-${rowUrns[2]}-col-select`).within(() => {
        cy.get("input").should("have.attr", "checked");
      });
      cy.getByTestId(`row-${rowUrns[3]}-col-select`).within(() => {
        cy.get("input").should("have.attr", "checked");
      });
      cy.getByTestId("bulk-actions-menu").should("not.be.disabled");
    });

    describe("tab navigation", () => {
      it("updates URL hash when switching tabs", () => {
        cy.visit(
          `${ACTION_CENTER_ROUTE}/${webMonitorKey}/${systemId}#attention-required`,
        );
        cy.location("hash").should("eq", "#attention-required");

        // eslint-disable-next-line cypress/no-unnecessary-waiting
        cy.wait(500);
        cy.getAntTab("Recent activity").click({ force: true });
        cy.location("hash").should("eq", "#recent-activity");

        // "recent activity" tab should be read-only
        cy.getByTestId("bulk-actions-menu").should("be.disabled");
        cy.getByTestId(`row-${rowUrns[0]}-col-system`).within(() => {
          cy.getByTestId("system-badge")
            .should("exist")
            .should("not.have.attr", "onClick");
          cy.getByTestId("add-system-btn").should("not.exist");
        });
        cy.getByTestId(`row-${rowUrns[0]}-col-data_use`).within(() => {
          cy.getByTestId("taxonomy-add-btn").should("not.exist");
        });
        cy.getByTestId(`row-${rowUrns[0]}-col-select`).should("not.exist");
        cy.getByTestId("col-actions").should("not.exist");

        // eslint-disable-next-line cypress/no-unnecessary-waiting
        cy.wait(500);
        cy.getAntTab("Ignored").click({ force: true });
        cy.location("hash").should("eq", "#ignored");
        // "ignore" option should not show in bulk actions menu
        cy.getByTestId(`row-${rowUrns[0]}-col-select`).find("label").click();
        cy.getByTestId(`row-${rowUrns[2]}-col-select`).find("label").click();
        cy.getByTestId(`row-${rowUrns[3]}-col-select`).find("label").click();
        cy.getByTestId("bulk-actions-menu").click();
        cy.get(".ant-dropdown-menu-item")
          .contains("Ignore")
          .should("not.exist");
      });
    });
  });
});
