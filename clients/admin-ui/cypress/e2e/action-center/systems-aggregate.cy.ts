import {
  stubPlus,
  stubSystemVendors,
  stubTaxonomyEntities,
  stubVendorList,
  stubWebsiteMonitor,
} from "cypress/support/stubs";

import {
  ACTION_CENTER_ROUTE,
  UNCATEGORIZED_SEGMENT,
} from "~/features/common/nav/routes";

describe("Action center system aggregate results", () => {
  const webMonitorKey = "my_web_monitor_1";
  const rowIds = [
    UNCATEGORIZED_SEGMENT,
    "system_key-8fe42cdb-af2e-4b9e-9b38-f75673180b88",
    "system_key-652c8984-ade7-470b-bce4-7e184621be9d",
    "fds.1047",
  ];
  beforeEach(() => {
    cy.login();
    stubPlus(true);
    stubWebsiteMonitor();
    stubTaxonomyEntities();
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

      cy.getAntTab("Recent activity").click();
      cy.location("hash").should("eq", "#recent-activity");

      // "recent activity" tab should be read-only
      cy.getByTestId("bulk-actions-menu").should("be.disabled");
      cy.get("thead tr")
        .should("be.visible")
        .within(() => {
          cy.get("th [aria-label='Select all']").should("exist");
          cy.contains("Actions").should("not.exist");
        });

      cy.get(".ant-spin-spinning").should("not.exist");

      cy.getAntTab("Ignored").click();
      cy.location("hash").should("eq", "#ignored");

      // "ignore" option should not show in bulk actions menu
      cy.getAntTableRow("[undefined]").findByRole("checkbox").click();
      cy.getAntTableRow(rowIds[2]).findByRole("checkbox").click();
      cy.getAntTableRow(rowIds[3]).findByRole("checkbox").click();
      cy.getByTestId("bulk-actions-menu").click();
      cy.getByTestId("bulk-ignore").should("not.exist");
    });

    it("maintains hash when clicking on a row", () => {
      // no hash (default tab)
      cy.visit(`${ACTION_CENTER_ROUTE}/${webMonitorKey}`);

      cy.getAntTableRow("[undefined]").within(() => {
        cy.getByTestId("system-name-link").should(
          "have.attr",
          "href",
          `${ACTION_CENTER_ROUTE}/${webMonitorKey}/[undefined]#attention-required`,
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

      cy.get("[role='tab']").contains("Ignored").click();
      cy.getAntTableRow("[undefined]").within(() => {
        cy.getByTestId("system-name-link").should(
          "have.attr",
          "href",
          `${ACTION_CENTER_ROUTE}/${webMonitorKey}/[undefined]#ignored`,
        );
      });

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
