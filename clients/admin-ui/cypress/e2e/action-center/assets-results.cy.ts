import {
  stubPlus,
  stubSystemVendors,
  stubTaxonomyEntities,
  stubVendorList,
  stubWebsiteMonitor,
} from "cypress/support/stubs";

import { ACTION_CENTER_ROUTE } from "~/features/common/nav/routes";

describe("Action center Asset Results", () => {
  beforeEach(() => {
    cy.login();
    stubPlus(true);
    stubWebsiteMonitor();
    stubTaxonomyEntities();
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
      cy.getByTestId("clear-filters").should("exist");
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
        cy.contains("Compliance").should("exist");
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
        cy.contains("Compliance").should("exist");
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
      // eslint-disable-next-line cypress/no-unnecessary-waiting
      cy.wait(500); // wait for the original router to update
      cy.findByRole("menuitem", { name: "Ignored" }).click({ force: true });
      // eslint-disable-next-line cypress/no-unnecessary-waiting
      cy.wait(500); // wait for the router to update
      cy.findByRole("menuitem", { name: "Ignored" }).should(
        "have.className",
        "ant-menu-item-selected",
      );
      cy.getByTestId("bulk-actions-menu").should("be.disabled");
      cy.getAntTableRow(rowUrns[0]).findByRole("checkbox").click();
      cy.getAntTableRow(rowUrns[2]).findByRole("checkbox").click();
      cy.getByTestId("selected-count").should("contain", "2 selected");
      cy.getByTestId("bulk-actions-menu").should("not.be.disabled");
      cy.getByTestId("bulk-actions-menu").click();
      cy.findByRole("menuitem", { name: "Restore" }).click({ force: true });
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

        // wait for router
        // eslint-disable-next-line cypress/no-unnecessary-waiting
        cy.wait(500);
        cy.findByRole("menuitem", { name: "Recent activity" }).click({
          force: true,
        });
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
        cy.findByRole("columnheader", { name: /Select all/ }).should(
          "not.exist",
        );
        cy.findByRole("columnheader", { name: /Actions/ }).should("not.exist");

        // wait for router
        // eslint-disable-next-line cypress/no-unnecessary-waiting
        cy.wait(500);
        cy.findByRole("menuitem", { name: "Ignored" }).click({ force: true });
        cy.location("hash").should("eq", "#ignored");
        // "ignore" option should not show in bulk actions menu
        cy.getAntTableRow(rowUrns[0]).findByRole("checkbox").click();
        cy.getAntTableRow(rowUrns[2]).findByRole("checkbox").click();
        cy.getAntTableRow(rowUrns[3]).findByRole("checkbox").click();
        cy.getByTestId("bulk-actions-menu").click();
        cy.findByRole("menuitem", { name: "Ignore" }).should("not.exist");
      });
    });

    describe("URL sync and table reset behavior", () => {
      beforeEach(() => {
        cy.visit(`${ACTION_CENTER_ROUTE}/${webMonitorKey}/${systemId}`);
        cy.wait("@getSystemAssetResults");
        cy.getByTestId("page-breadcrumb").should("contain", systemName);
      });

      it("syncs search query to URL and resets to page 1", () => {
        // Go to page 2 first so we can verify reset
        cy.getAntPagination().should("exist");
        cy.antPaginateNext();
        cy.location("search").should("contain", "page=2");

        // Type into the search input and verify URL query param updates
        cy.findByPlaceholderText("Search by asset name...")
          .clear()
          .type("collect");
        // Debounce buffer
        // eslint-disable-next-line cypress/no-unnecessary-waiting
        cy.wait(400);
        cy.location("search").should("contain", "search=collect");
        // Should reset to page 1 on search change
        cy.location("search").should("not.contain", "page=");
      });

      it("syncs sorting to URL when sorting by the Asset column", () => {
        cy.findByRole("columnheader", { name: /Asset/ }).click({ force: true });
        // First click should set ascending sort
        cy.location("search").should("contain", "sortKey=name");
        cy.location("search").should("contain", "sortOrder=ascend");
      });

      it("clears filters, sorting, search, and selection with the clear filters button", () => {
        // Select a couple rows so we can verify selection reset
        cy.getAntTableRow(rowUrns[0])
          .findByRole("checkbox")
          .click({ force: true });
        cy.getAntTableRow(rowUrns[2])
          .findByRole("checkbox")
          .click({ force: true });
        cy.getByTestId("selected-count").should("contain", "2 selected");
        cy.getByTestId("bulk-actions-menu").should("not.be.disabled");

        // Apply search and sorting to populate URL
        cy.findByPlaceholderText("Search by asset name...").clear().type("gtm");
        // Debounce buffer
        // eslint-disable-next-line cypress/no-unnecessary-waiting
        cy.wait(400);
        cy.findByRole("columnheader", { name: /Asset/ }).click({ force: true });
        cy.location("search").should("contain", "search=gtm");
        cy.location("search").should("contain", "sortKey=name");

        // Clear
        cy.getByTestId("clear-filters").click({ force: true });
        // URL params cleared/reset
        cy.location("search").should("not.contain", "search=");
        cy.location("search").should("not.contain", "sortKey=");
        cy.location("search").should("not.contain", "sortOrder=");
        cy.location("search").should("not.contain", "page=");

        // Search input field should be cleared
        cy.findByPlaceholderText("Search by asset name...").should(
          "have.value",
          "",
        );

        // Selection reset and menu disabled
        cy.findByTestId("selected-count").should("not.exist");
        cy.getByTestId("bulk-actions-menu").should("be.disabled");
      });

      it("resets table state and selection when switching tabs", () => {
        // Select rows and apply a search so state is non-default
        cy.getAntTableRow(rowUrns[0])
          .findByRole("checkbox")
          .click({ force: true });
        cy.findByPlaceholderText("Search by asset name...")
          .clear()
          .type("collect");
        // Debounce buffer
        // eslint-disable-next-line cypress/no-unnecessary-waiting
        cy.wait(400);
        cy.getByTestId("selected-count").should("contain", "1 selected");
        cy.location("search").should("contain", "search=collect");

        // Switch tab
        cy.findByRole("menuitem", { name: "Ignored" }).click({ force: true });
        // wait for router
        // eslint-disable-next-line cypress/no-unnecessary-waiting
        cy.wait(500);
        cy.location("hash").should("eq", "#ignored");

        // State should be reset
        cy.findByTestId("selected-count").should("not.exist");
        cy.getByTestId("bulk-actions-menu").should("be.disabled");
        cy.location("search").should("not.contain", "search=");
        cy.location("search").should("not.contain", "page=");

        // Search input field should be cleared
        cy.findByPlaceholderText("Search by asset name...").should(
          "have.value",
          "",
        );
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

    describe("Compliance column in assets table", () => {
      beforeEach(() => {
        cy.visit(`${ACTION_CENTER_ROUTE}/${webMonitorKey}/${systemId}`);
        cy.wait("@getSystemAssetResultsWithConsent");
      });

      it("should display compliance column with consent status badges", () => {
        cy.get("thead tr").within(() => {
          cy.contains("Compliance").should("exist");
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

      it("should show warning icon in compliance column header when there are assets without consent", () => {
        cy.findByRole("columnheader", { name: /Compliance/ }).within(() => {
          cy.getByTestId("discovery-status-icon-alert")
            .should("exist")
            .scrollIntoView()
            .should("be.visible");
          cy.getByTestId("discovery-status-icon-alert").realHover();
        });
        cy.findByRole("tooltip", {
          name: "One or more assets were detected without consent",
        }).should("be.visible");
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
          cy.findByRole("columnheader", { name: /Location/ }).should("exist");
          cy.findByRole("columnheader", { name: /Page/ }).should("exist");

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
        cy.findByRole("columnheader", { name: /System/ }).within(() => {
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
