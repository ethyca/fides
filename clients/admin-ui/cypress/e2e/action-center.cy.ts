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

      // table headers
      cy.findByRole("columnheader", { name: "System" }).should("exist");
      cy.findByRole("columnheader", { name: "Assets" }).should("exist");
      cy.findByRole("columnheader", { name: "Categories of consent" }).should(
        "exist",
      );
      cy.findByRole("columnheader", { name: "Locations" }).should("exist");
      cy.findByRole("columnheader", { name: "Domains" }).should("exist");
      cy.findByRole("columnheader", { name: "Actions" }).should("exist");

      cy.getAntTableRow("[undefined]").within(() => {
        cy.getByTestId("change-icon").should("exist");
        cy.contains("Uncategorized assets").should("exist");
      });
      cy.getAntTableRow(rowIds[3]).within(() => {
        cy.getByTestId("change-icon").should("exist"); // new system
      });
      // data use column should be empty for uncategorized assets
      cy.getAntTableRow("[undefined]").within(() => {
        cy.getByTestId("tag-expandable-cell-empty").should("exist");
      });
      // cy.getByTestId("row-1-col-system_name").within(() => {
      //   cy.getByTestId("change-icon").should("not.exist"); // existing result
      //   cy.contains("Google Tag Manager").should("exist");
      // });
      // data use column should not be empty for other assets
      cy.getAntTableRow(rowIds[1]).within(() => {
        cy.getByTestId("tag-expandable-cell")
          .first()
          .children()
          .should("have.length", 1);
      });

      // multiple locations
      cy.getAntTableRow(rowIds[2]).within(() => {
        cy.getByTestId("tag-expandable-cell")
          .last()
          .should("contain", "United States")
          .and("contain", "Canada");
      });
      // single location
      cy.getAntTableRow(rowIds[3]).within(() => {
        cy.getByTestId("tag-expandable-cell")
          .last()
          .should("contain", "United States");
      });

      // multiple domains
      cy.getAntTableRow("[undefined]").within(() => {
        cy.getByTestId("list-expandable-cell")
          .should("contain", "29 domains")
          .within(() => {
            cy.get("button").click({ force: true });
            cy.get("li").should("have.length", 29);
          });
      });
      // single domain
      cy.getAntTableRow(rowIds[3]).within(() => {
        cy.getByTestId("list-expandable-cell-single").should(
          "contain",
          "analytics.google.com",
        );
      });
      cy.getAntTableRow("[undefined]").within(() => {
        cy.getByTestId("add-btn").should("be.disabled");
      });
    });
    it("should ignore all assets in an uncategorized system", () => {
      cy.getAntTableRow("[undefined]").within(() => {
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
      cy.getAntTableRow(rowIds[1]).within(() => {
        cy.getByTestId("add-btn").click({ force: true });
      });
      cy.wait("@addMonitorResultSystem");
      cy.getByTestId("toast-success-msg").should(
        "contain",
        "10 assets from Google Tag Manager have been added to the system inventory.",
      );
    });
    it("should ignore all assets in a categorized system", () => {
      cy.getAntTableRow(rowIds[1]).within(() => {
        cy.getByTestId("ignore-btn").click({ force: true });
      });
      cy.wait("@ignoreMonitorResultSystem");
      cy.getByTestId("toast-success-msg").should(
        "contain",
        "10 assets from Google Tag Manager have been ignored and will not appear in future scans.",
      );
    });
    it("shouldn't allow bulk add when uncategorized system is selected", () => {
      cy.getAntTableRow("[undefined]").findByRole("checkbox").click();
      cy.getByTestId("selected-count").should("contain", "1 selected");
      cy.getByTestId("bulk-actions-menu").click();
      cy.get(".ant-dropdown-menu-item")
        .first()
        .should("have.class", "ant-dropdown-menu-item-disabled");
    });
    it("should bulk add results from categorized systems", () => {
      cy.getByTestId("bulk-actions-menu").should("be.disabled");
      cy.getAntTableRow(rowIds[1]).findByRole("checkbox").click();
      cy.getAntTableRow(rowIds[2]).findByRole("checkbox").click();
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
      cy.getAntTableRow("[undefined]").findByRole("checkbox").click();
      cy.getAntTableRow(rowIds[1]).findByRole("checkbox").click();
      cy.getAntTableRow(rowIds[2]).findByRole("checkbox").click();
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
      cy.getAntTableRow(rowIds[1]).within(() => {
        cy.getByTestId("system-name-link").click();
      });
      cy.url().should(
        "contain",
        "system_key-8fe42cdb-af2e-4b9e-9b38-f75673180b88",
      );
      cy.getByTestId("page-breadcrumb").should("contain", "Google Tag Manager");
    });

    describe("tab navigation", () => {
      it("updates URL hash when switching tabs", () => {
        cy.visit(`${ACTION_CENTER_ROUTE}/${webMonitorKey}#attention-required`);
        cy.location("hash").should("eq", "#attention-required");

        cy.getAntTab("Recent activity").click({ force: true });
        cy.location("hash").should("eq", "#recent-activity");

        // "recent activity" tab should be read-only
        cy.getByTestId("bulk-actions-menu").should("be.disabled");
        cy.get("thead tr")
          .should("be.visible")
          .within(() => {
            cy.get("th [aria-label='Select all']").should("exist");
            cy.contains("Actions").should("not.exist");
          });

        // eslint-disable-next-line cypress/no-unnecessary-waiting
        cy.wait(300); // route is not immediately updated
        cy.getAntTab("Ignored").click({ force: true });
        cy.location("hash").should("eq", "#ignored");

        // "ignore" option should not show in bulk actions menu
        cy.getAntTableRow("[undefined]").findByRole("checkbox").click();
        cy.getAntTableRow(rowIds[2]).findByRole("checkbox").click();
        cy.getAntTableRow(rowIds[3]).findByRole("checkbox").click();
        cy.getByTestId("bulk-actions-menu").click();
        cy.getByTestId("bulk-ignore").should("not.exist");
      });

      it("maintains hash when clicking on a row", () => {
        // no hash
        cy.visit(`${ACTION_CENTER_ROUTE}/${webMonitorKey}`);

        cy.getAntTableRow("[undefined]").within(() => {
          cy.getByTestId("system-name-link").should(
            "have.attr",
            "href",
            `${ACTION_CENTER_ROUTE}/${webMonitorKey}/[undefined]`,
          );
        });

        cy.get("[role='tab']").contains("Recent activity").click();
        cy.getAntTableRow("[undefined]").within(() => {
          cy.getByTestId("system-name-link").should(
            "have.attr",
            "href",
            `${ACTION_CENTER_ROUTE}/${webMonitorKey}/[undefined]#recent-activity`,
          );
        });

        // eslint-disable-next-line cypress/no-unnecessary-waiting
        cy.wait(300); // route is not immediately updated

        cy.get("[role='tab']").contains("Ignored").click();
        cy.getAntTableRow("[undefined]").within(() => {
          cy.getByTestId("system-name-link").should(
            "have.attr",
            "href",
            `${ACTION_CENTER_ROUTE}/${webMonitorKey}/[undefined]#ignored`,
          );
        });

        // eslint-disable-next-line cypress/no-unnecessary-waiting
        cy.wait(300); // route is not immediately updated

        cy.get("[role='tab']").contains("Attention required").click();
        cy.getAntTableRow("[undefined]").within(() => {
          cy.getByTestId("system-name-link")
            .should(
              "have.attr",
              "href",
              `${ACTION_CENTER_ROUTE}/${webMonitorKey}/[undefined]#attention-required`,
            )
            .click();
        });
        cy.location("hash").should("eq", "#attention-required");
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
      cy.getByTestId("bulk-actions-menu").should("be.disabled");
      cy.getByTestId("add-all").should("be.disabled");

      // table columns
      cy.get("thead tr").within(() => {
        cy.get("th [aria-label='Select all']").should("exist");
        cy.contains("Asset").should("exist");
        cy.contains("Type").should("exist");
        cy.contains("System").should("exist");
        cy.contains("Categories of consent").should("exist");
        cy.contains("Locations").should("exist");
        cy.contains("Domain").should("exist");
        cy.contains("Detected on").should("exist");
        cy.contains("Discovery").should("exist");
        cy.contains("Actions").should("exist");
      });

      cy.getAntTableRow(firstRowUrn).within(() => {
        cy.getByTestId("add-btn").should("be.disabled");
        cy.getByTestId("ignore-btn").should("not.be.disabled");
      });
    });
    it("should allow adding a system on uncategorized assets", () => {
      cy.getAntTableRow(firstRowUrn).within(() => {
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
      cy.getByTestId("bulk-actions-menu").should("be.disabled");
      cy.getByTestId("add-all").should("exist");

      // table columns
      cy.get("thead tr").within(() => {
        cy.get("th [aria-label='Select all']").should("exist");
        cy.contains("Asset").should("exist");
        cy.contains("Type").should("exist");
        cy.contains("System").should("exist");
        cy.contains("Categories of consent").should("exist");
        cy.contains("Locations").should("exist");
        cy.contains("Domain").should("exist");
        cy.contains("Detected on").should("exist");
        cy.contains("Discovery").should("exist");
        cy.contains("Actions").should("exist");
      });

      cy.getAntTableRow(rowUrns[0]).within(() => {
        cy.get("[data-testid='list-expandable-cell-single']").should(
          "contain",
          "single_page",
        );
      });
      cy.getAntTableRow(rowUrns[1]).within(() => {
        cy.get("[data-testid='list-expandable-cell']").within(() => {
          cy.get("span").should("contain", "3 pages");
          cy.get("button").click({ force: true });
          cy.get("li").should("have.length", 3);
        });
      });
      cy.getAntTableRow(rowUrns[2]).within(() => {
        cy.get("[data-testid='list-expandable-cell']").should("not.exist");
      });
      cy.getAntTableRow(rowUrns[3]).within(() => {
        cy.get("[data-testid='list-expandable-cell']").should("not.exist");
      });
      cy.getAntTableRow(rowUrns[4]).within(() => {
        cy.getByTestId("add-btn").should("exist");
        cy.getByTestId("ignore-btn").should("exist");
      });
    });
    it("should allow editing a system on categorized assets", () => {
      cy.getAntTableRow(rowUrns[3]).within(() => {
        cy.getByTestId("system-badge").click({ force: true });
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
      cy.getAntTableRow(rowUrns[2]).within(() => {
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
      cy.getAntTableRow(rowUrns[4]).within(() => {
        cy.getByTestId("system-badge").click({ force: true });
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
      cy.getAntTableRow(rowUrns[0]).within(() => {
        cy.getByTestId("add-btn").click({ force: true });
      });
      cy.wait("@addAssets");
      cy.getByTestId("toast-success-msg").should(
        "contain",
        'Browser request "11020051272" has been added to the system inventory.',
      );
    });
    it("should ignore individual assets", () => {
      cy.getAntTableRow(rowUrns[0]).within(() => {
        cy.getByTestId("ignore-btn").click({ force: true });
      });
      cy.wait("@ignoreAssets");
      cy.getByTestId("toast-success-msg").should(
        "contain",
        'Browser request "11020051272" has been ignored and will not appear in future scans.',
      );
    });

    it("should restore individual ignored assets", () => {
      cy.getAntTableRow(rowUrns[1]).within(() => {
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
      cy.getAntTableRow(rowUrns[0]).findByRole("checkbox").click();
      cy.getAntTableRow(rowUrns[2]).findByRole("checkbox").click();
      cy.getAntTableRow(rowUrns[3]).findByRole("checkbox").click();
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
      cy.getAntTableRow(rowUrns[0]).findByRole("checkbox").click();
      cy.getAntTableRow(rowUrns[2]).findByRole("checkbox").click();
      cy.getAntTableRow(rowUrns[3]).findByRole("checkbox").click();
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
      cy.getAntTableRow(rowUrns[0]).findByRole("checkbox").click();
      cy.getAntTableRow(rowUrns[2]).findByRole("checkbox").click();
      cy.getByTestId("selected-count").should("contain", "2 selected");
      cy.getByTestId("bulk-actions-menu").should("not.be.disabled");
      cy.getByTestId("bulk-actions-menu").click();
      cy.findByRole("menuitem", { name: "Restore" }).click();
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
      cy.getAntTableRow(rowUrns[0]).findByRole("checkbox").click();
      cy.getAntTableRow(rowUrns[2]).findByRole("checkbox").click();
      cy.getAntTableRow(rowUrns[3]).findByRole("checkbox").click();
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
      cy.getAntTableRow(rowUrns[0]).findByRole("checkbox").click();
      cy.getAntTableRow(rowUrns[2]).findByRole("checkbox").click();
      cy.getAntTableRow(rowUrns[3]).findByRole("checkbox").click();
      cy.getByTestId("selected-count").should("contain", "3 selected");
      cy.getByTestId("bulk-actions-menu").should("not.be.disabled");
      cy.getByTestId("bulk-actions-menu").click();
      cy.findByRole("menuitem", { name: "Add consent category" }).click();
      cy.getByTestId("taxonomy-select").antSelect("essential");
      cy.getByTestId("save-btn").click({ force: true });
      cy.wait("@patchAssets");
      cy.getByTestId("toast-success-msg").should(
        "contain",
        "Consent categories added to 3 assets from Google Tag Manager.",
      );
      cy.getAntTableRow(rowUrns[0]).within(() => {
        cy.findByRole("checkbox").should("be.checked");
      });
      cy.getAntTableRow(rowUrns[2]).within(() => {
        cy.findByRole("checkbox").should("be.checked");
      });
      cy.getAntTableRow(rowUrns[3]).within(() => {
        cy.findByRole("checkbox").should("be.checked");
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
        cy.wait(300); // route is not immediately updated
        cy.getAntTab("Recent activity").click({ force: true });
        cy.location("hash").should("eq", "#recent-activity");

        // "recent activity" tab should be read-only
        cy.getByTestId("bulk-actions-menu").should("be.disabled");
        cy.getAntTableRow(rowUrns[0]).within(() => {
          cy.getByTestId("system-badge")
            .should("exist")
            .should("not.have.attr", "onClick");
          cy.getByTestId("add-system-btn").should("not.exist");
        });
        cy.getAntTableRow(rowUrns[0]).within(() => {
          cy.getByTestId("taxonomy-add-btn").should("not.exist");
        });
        cy.findByRole("columnheader", { name: "Select all" }).should(
          "not.exist",
        );
        cy.findByRole("columnheader", { name: "Actions" }).should("not.exist");

        // eslint-disable-next-line cypress/no-unnecessary-waiting
        cy.wait(300); // route is not immediately updated
        cy.getAntTab("Ignored").click({ force: true });
        cy.location("hash").should("eq", "#ignored");
        // "ignore" option should not show in bulk actions menu
        cy.getAntTableRow(rowUrns[0]).findByRole("checkbox").click();
        cy.getAntTableRow(rowUrns[2]).findByRole("checkbox").click();
        cy.getAntTableRow(rowUrns[3]).findByRole("checkbox").click();
        cy.getByTestId("bulk-actions-menu").click();
        cy.findByRole("menuitem", { name: "Ignore" }).should("not.exist");
      });
    });
  });

  describe("Action center consent status functionality", () => {
    const webMonitorKey = "my_web_monitor_1";
    const systemId = "system_key-8fe42cdb-af2e-4b9e-9b38-f75673180b88";
    const rowUrns = [
      "my_web_monitor_1.GET.td.doubleclick.net.https://td.doubleclick.net/td/rul/11020051272",
      "my_web_monitor_1.GET.td.doubleclick.net.https://td.doubleclick.net/td/rul/697301175",
      "my_web_monitor_1.POST.www.google.com.https://www.google.com/ccm/collect",
    ];

    beforeEach(() => {
      cy.login();
      stubPlus(true);
      cy.intercept("GET", "/api/v1/plus/discovery-monitor/*/results*", {
        fixture:
          "detection-discovery/activity-center/system-asset-results-with-consent",
      }).as("getSystemAssetResultsWithConsent");
    });

    describe("Monitor list consent warnings", () => {
      beforeEach(() => {
        cy.visit(ACTION_CENTER_ROUTE);
        cy.wait("@getMonitorResults");
      });

      it("should display consent warning icons on monitors with consent issues", () => {
        // Check that monitors with consent issues show warning icon
        cy.getByTestId("monitor-result-my_web_monitor_2").within(() => {
          cy.getByTestId("discovery-status-icon-alert").should("exist");
          cy.getByTestId("discovery-status-icon-alert").realHover();
        });
        cy.get(".ant-tooltip-inner").should(
          "contain",
          "One or more assets were detected without consent",
        );

        cy.getByTestId("monitor-result-my_web_monitor_1").within(() => {
          cy.getByTestId("discovery-status-icon-alert").should("exist");
        });

        // Monitor without consent issues should not show warning icon
        cy.getByTestId("monitor-result-My_New_BQ_Monitor").within(() => {
          cy.getByTestId("discovery-status-icon-alert").should("not.exist");
        });
      });
    });

    describe("Discovery column in assets table", () => {
      beforeEach(() => {
        cy.visit(`${ACTION_CENTER_ROUTE}/${webMonitorKey}/${systemId}`);
        cy.wait("@getSystemAssetResultsWithConsent");
      });

      it("should display discovery column with consent status badges", () => {
        cy.get("thead tr").within(() => {
          cy.contains("Discovery").should("exist");
        });

        // Check "Without consent" badge
        cy.getAntTableRow(rowUrns[0]).within(() => {
          cy.contains("Without consent").should("exist");
          cy.getByTestId("status-badge_without-consent").should(
            "have.attr",
            "data-color",
            "error",
          );
        });

        // Check "With consent" badge
        cy.getAntTableRow(rowUrns[1]).within(() => {
          cy.contains("With consent").should("exist");
          cy.getByTestId("status-badge_with-consent").should(
            "have.attr",
            "data-color",
            "success",
          );
        });

        // Check "Without consent" badge for another asset
        cy.getAntTableRow(rowUrns[2]).within(() => {
          cy.contains("Without consent").should("exist");
          cy.getByTestId("status-badge_without-consent").should(
            "have.attr",
            "data-color",
            "error",
          );
        });
      });

      it("should show warning icon in discovery column header when there are assets without consent", () => {
        cy.findByRole("columnheader", { name: "Discovery" }).within(() => {
          cy.getByTestId("discovery-status-icon-alert")
            .should("exist")
            .scrollIntoView();
          cy.getByTestId("discovery-status-icon-alert").realHover();
        });
        cy.findByRole("tooltip")
          .should("be.visible")
          .should(
            "contain",
            "One or more assets were detected without consent",
          );
      });

      it("should open consent breakdown modal when clicking 'Without consent' badge", () => {
        cy.getAntTableRow(rowUrns[0]).within(() => {
          cy.getByTestId("status-badge_without-consent")
            .scrollIntoView()
            .within(() => {
              cy.findByRole("button").click();
            });
        });

        cy.wait("@getConsentBreakdown");

        // Check modal is open
        cy.getByTestId("consent-breakdown-modal").should("exist");
        cy.contains("Consent discovery").should("exist");

        // Check modal content
        cy.getByTestId("consent-breakdown-modal-content").within(() => {
          cy.contains(
            "View all instances where this asset was detected without consent",
          ).should("exist");
          cy.contains("Asset name:").should("exist");
          cy.contains("System:").should("exist");
          cy.contains("Domain:").should("exist");

          // Check table headers
          cy.findByRole("columnheader", { name: "Location" }).should("exist");
          cy.findByRole("columnheader", { name: "Page" }).should("exist");

          // Check table data
          cy.getByTestId("consent-breakdown-modal-table")
            .should("be.visible")
            .within(() => {
              cy.get("tr[data-row-key]").should("have.length", 3);
              cy.get("tr[data-row-key]")
                .first()
                .within(() => {
                  cy.contains("United States").should("exist");
                  cy.get("a[href='https://example.com/page1']").should("exist");
                });
            });
        });

        // Check modal footer buttons
        cy.get(".ant-modal-footer").within(() => {
          cy.contains("Cancel").should("exist");
          // TODO: uncomment when onDownload is implemented in `DiscoveryStatusBadgeCell.tsx`
          // cy.contains("Download").should("exist");
        });

        // Close modal
        cy.contains("Cancel").click();
        cy.getByTestId("consent-breakdown-modal").should("not.exist");
      });

      it("should open external links in new tab from consent breakdown modal", () => {
        cy.getAntTableRow(rowUrns[0]).within(() => {
          cy.getByTestId("status-badge_without-consent")
            .scrollIntoView()
            .within(() => {
              cy.findByRole("button").click({ force: true });
            });
        });

        cy.wait("@getConsentBreakdown");

        cy.getByTestId("consent-breakdown-modal-content").within(() => {
          cy.get("a[href='https://example.com/page1']")
            .should("have.attr", "target", "_blank")
            .should("have.attr", "rel", "noopener noreferrer");
        });

        cy.findByRole("button", { name: "Cancel" }).click();
      });
    });

    describe("System aggregate view consent status", () => {
      beforeEach(() => {
        cy.visit(`${ACTION_CENTER_ROUTE}/${webMonitorKey}`);
        cy.wait("@getSystemAggregateResults");
      });

      it("should show consent warning icon in system column header", () => {
        cy.findByRole("columnheader", { name: "System" }).within(() => {
          cy.getByTestId("discovery-status-icon-alert").should("exist");
          cy.getByTestId("discovery-status-icon-alert").realHover();
        });
        cy.get(".ant-tooltip-inner").should(
          "contain",
          "One or more assets were detected without consent",
        );
      });
    });
  });
});
