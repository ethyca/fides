import {
  stubPlus,
  stubSystemCrud,
  stubTaxonomyEntities,
} from "cypress/support/stubs";

import {
  LegacyAllowedTypes,
  LegacyResourceTypes,
} from "~/features/common/custom-fields/types";
import { REPORTING_DATAMAP_ROUTE } from "~/features/common/nav/routes";
import { CustomFieldDefinition, ReportType } from "~/types/api";

const mockCustomField = (overrides?: Partial<CustomFieldDefinition>) => {
  const base = {
    name: "Prime number",
    description: null,
    field_type: "string",
    allow_list_id: "id-allow-list-prime-numbers",
    resource_type: "system",
    field_definition: null,
    active: true,
    id: "id-custom-field-definition-prime-number",
  };
  if (overrides) {
    return { ...base, ...overrides };
  }
  return base;
};

describe("Data map report table", () => {
  beforeEach(() => {
    cy.login();
    stubPlus(true);
    stubSystemCrud();
    stubTaxonomyEntities();
    cy.intercept("GET", "/api/v1/plus/datamap/minimal*", {
      fixture: "datamap/minimal.json",
    }).as("getDatamapMinimal");
    cy.intercept(
      "GET",
      "/api/v1/plus/custom-metadata/custom-field-definition",
      {
        body: [
          mockCustomField({ name: "Starter pokemon" }),
          mockCustomField({
            name: "Pokemon party",
            field_type: LegacyAllowedTypes.STRING_ARRAY,
          }),
          mockCustomField({
            name: "Color",
            resource_type: LegacyResourceTypes.DATA_USE,
          }),
        ],
      },
    ).as("getCustomFieldDefinitions");
    cy.intercept("GET", "/api/v1/plus/custom-report/minimal*", {
      fixture: "custom-reports/minimal.json",
    }).as("getCustomReportsMinimal");
    cy.visit(REPORTING_DATAMAP_ROUTE);
  });

  it("can render custom fields", () => {
    cy.wait("@getCustomFieldDefinitions");
    // Should render the custom fields as columns
    cy.getByTestId("column-system_starter_pokemon").contains("Starter pokemon");
    cy.getByTestId("column-system_pokemon_party").contains("Pokemon party");
    cy.getByTestId("column-privacy_declaration_color").contains("Color");

    // Pokemon party is multi-select, so we should have a menu to allow expanding/collapsing all
    cy.getByTestId("row-0-col-system_pokemon_party").contains("3");
    cy.getByTestId("system_pokemon_party-header-menu").click();
    cy.getAntDropdownOverlay("system_pokemon_party-header-menu-list").within(
      () => {
        cy.selectAntDropdownOption("Expand all");
      },
    );
    ["eevee", "pikachu", "articuno"].forEach((pokemon) => {
      cy.getByTestId("row-0-col-system_pokemon_party").contains(pokemon);
    });
  });

  it("can render empty datamap report", () => {
    cy.intercept("GET", "/api/v1/plus/datamap/minimal*", {
      fixture: "empty-pagination.json",
    }).as("getDatamapMinimalEmpty");
    cy.getByTestId("datamap-report-heading").should("be.visible");
  });

  it("can group by data use", () => {
    cy.getByTestId("group-by-menu").should("contain.text", "Group by system");
    cy.getByTestId("group-by-menu").click();
    cy.selectAntDropdownOption("Data use");
    cy.wait("@getDatamapMinimal");
    cy.getByTestId("group-by-menu").should("contain.text", "Group by data use");

    // should persist the grouping when navigating away
    cy.reload();
    cy.getByTestId("group-by-menu").should("contain.text", "Group by data use");
  });

  describe("Undeclared data category columns", () => {
    it("should have the undeclared data columns disabled by default", () => {
      cy.getByTestId("row-0-col-system_undeclared_data_categories").should(
        "not.exist",
      );
      cy.getByTestId("row-0-col-data_use_undeclared_data_categories").should(
        "not.exist",
      );
    });

    it("should show undeclared data columns when enabled", () => {
      cy.getByTestId("more-menu").click();
      cy.selectAntDropdownOption("Edit columns");
      cy.contains("div", "System undeclared data categories").click();
      cy.contains("div", "Data use undeclared data categories").click();
      cy.getByTestId("save-button").click();

      cy.getByTestId("row-0-col-system_undeclared_data_categories").contains(
        "User Contact Email",
      );
      cy.getByTestId("row-0-col-system_undeclared_data_categories").contains(
        "Cookie ID",
      );
      cy.getByTestId("row-0-col-data_use_undeclared_data_categories").contains(
        "User Contact Email",
      );
      cy.getByTestId("row-0-col-data_use_undeclared_data_categories").contains(
        "Cookie ID",
      );
    });
  });

  describe("Column customization", () => {
    it("should show/hide columns", () => {
      // hide
      cy.getByTestId("more-menu").click();
      cy.selectAntDropdownOption("Edit columns");
      cy.getByTestId("column-list-item-legal_name").within(() => {
        cy.get("button#legal_name").should("have.attr", "aria-checked", "true");
        cy.get("button#legal_name").click();
        cy.get("button#legal_name").should(
          "have.attr",
          "aria-checked",
          "false",
        );
      });
      cy.getByTestId("save-button").click();
      cy.getByTestId("column-legal_name").should("not.exist");

      // should persist the hidden column when navigating away
      cy.reload();
      cy.getByTestId("column-legal_name").should("not.exist");

      // show
      cy.getByTestId("more-menu").click();
      cy.selectAntDropdownOption("Edit columns");
      cy.getByTestId("column-list-item-legal_name").within(() => {
        cy.get("button#legal_name").should(
          "have.attr",
          "aria-checked",
          "false",
        );
        cy.get("button#legal_name").click();
        cy.get("button#legal_name").should("have.attr", "aria-checked", "true");
      });
      cy.getByTestId("save-button").click();
      cy.getByTestId("column-legal_name").should("exist");
    });

    it("should reorder columns", () => {
      cy.getByTestId("more-menu").click();
      cy.selectAntDropdownOption("Edit columns");
      cy.getAntDropdownOverlay("more-menu-list").should("not.be.visible");
      const dataTransfer = new DataTransfer();
      cy.getByTestId("column-dragger-legal_name").trigger("dragstart");
      cy.getByTestId("column-dragger-data_categories").trigger("drop");
      cy.getByTestId("save-button").click();

      // Verify the new order
      cy.getByTestId("fidesTable").within(() => {
        cy.get("thead th").eq(2).should("contain.text", "Legal name");
        cy.get("thead th").eq(3).should("contain.text", "Data categories");
      });

      // Reload and verify the order persists
      cy.reload();
      cy.getByTestId("fidesTable").within(() => {
        cy.get("thead th").eq(2).should("contain.text", "Legal name");
        cy.get("thead th").eq(3).should("contain.text", "Data categories");
      });
    });

    it("should expand/collapse columns", () => {
      cy.getByTestId("more-menu").click();
      cy.selectAntDropdownOption("Edit columns");
      cy.getByTestId(
        "column-list-item-system_undeclared_data_categories",
      ).within(() => {
        cy.get("button#system_undeclared_data_categories").click();
      });
      cy.getByTestId(
        "column-list-item-data_use_undeclared_data_categories",
      ).within(() => {
        cy.get("button#data_use_undeclared_data_categories").click();
      });
      cy.getByTestId("save-button").click();

      cy.getByTestId("system_undeclared_data_categories-header-menu")
        .should("exist")
        .click();
      cy.getAntDropdownOverlay(
        "system_undeclared_data_categories-header-menu-list",
      ).within(() => {
        cy.selectAntDropdownOption("Expand all");
      });
      ["User Contact Email", "Cookie ID"].forEach((pokemon) => {
        cy.getByTestId("row-0-col-system_undeclared_data_categories").contains(
          pokemon,
        );
      });

      cy.getByTestId("data_use_undeclared_data_categories-header-menu").click();
      cy.getAntDropdownOverlay(
        "data_use_undeclared_data_categories-header-menu-list",
      ).within(() => {
        cy.selectAntDropdownOption("Expand all");
      });
      ["User Contact Email", "Cookie ID"].forEach((pokemon) => {
        cy.getByTestId(
          "row-0-col-data_use_undeclared_data_categories",
        ).contains(pokemon);
      });

      // should persist the expanded columns when navigating away
      cy.reload();
      ["User Contact Email", "Cookie ID"].forEach((pokemon) => {
        cy.getByTestId("row-0-col-system_undeclared_data_categories").contains(
          pokemon,
        );
        cy.getByTestId(
          "row-0-col-data_use_undeclared_data_categories",
        ).contains(pokemon);
      });
    });

    describe("Column renaming", () => {
      it("should rename columns", () => {
        cy.getByTestId("more-menu").click();
        cy.selectAntDropdownOption("Rename columns");
        cy.getByTestId("rename-columns-reset-btn").should("exist");
        cy.getByTestId("rename-columns-cancel-btn").should("exist");
        cy.getByTestId("rename-columns-apply-btn").should("exist");
        cy.getByTestId("column-data_categories-input")
          .eq(0)
          .should("be.visible")
          .clear()
          .then(() => {
            cy.getByTestId("column-data_categories-input")
              .eq(0)
              .type("Custom Title");
          });
        cy.getByTestId("rename-columns-apply-btn").click({ force: true });
        cy.getByTestId("rename-columns-reset-btn").should("not.exist");
        cy.getByTestId("rename-columns-cancel-btn").should("not.exist");
        cy.getByTestId("rename-columns-apply-btn").should("not.exist");
        cy.getByTestId("column-data_categories").should(
          "contain.text",
          "Custom Title",
        );

        // check edit columns modal
        cy.getByTestId("more-menu").click();
        cy.selectAntDropdownOption("Edit columns");
        cy.getByTestId("column-list-item-data_categories").within(() => {
          cy.get("label[for='data_categories']").should(
            "have.text",
            "Custom Title",
          );
        });
        cy.getAntModalClose().click();

        // check filter modal
        cy.getByTestId("filter-multiple-systems-btn").click();
        cy.getByTestId("datamap-report-filter-modal").should("be.visible");
        cy.getByTestId("filter-modal-accordion-button")
          .eq(1)
          .should("have.text", "Custom Title");

        // should persist the naming when navigating away
        cy.reload();
        cy.getByTestId("column-data_categories").should(
          "contain.text",
          "Custom Title",
        );
      });
      it("should cancel renaming columns", () => {
        cy.getByTestId("more-menu").click();
        cy.selectAntDropdownOption("Rename columns");
        cy.getByTestId("column-data_uses-input")
          .eq(0)
          .clear()
          .then(() => {
            cy.getByTestId("column-data_uses-input").eq(0).type("Custom Title");
          });
        cy.getByTestId("rename-columns-cancel-btn").click({ force: true });
        cy.getByTestId("rename-columns-reset-btn").should("not.exist");
        cy.getByTestId("rename-columns-cancel-btn").should("not.exist");
        cy.getByTestId("rename-columns-apply-btn").should("not.exist");
        cy.getByTestId("column-data_uses").should("contain.text", "Data use");
      });
      it("should reset columns", () => {
        cy.getByTestId("more-menu").click();
        cy.selectAntDropdownOption("Rename columns");
        cy.getByTestId("column-data_uses-input")
          .eq(0)
          .clear()
          .then(() => {
            cy.getByTestId("column-data_uses-input").eq(0).type("Custom Title");
          });
        cy.getByTestId("rename-columns-apply-btn").click({ force: true });
        cy.getByTestId("more-menu").click();
        cy.selectAntDropdownOption("Rename columns");
        cy.getByTestId("rename-columns-reset-btn").click({ force: true });
        cy.getByTestId("column-data_uses").should("contain.text", "Data use");
      });
      it("should support pressing the Enter key to apply renamed columns", () => {
        cy.getByTestId("more-menu").click();
        cy.selectAntDropdownOption("Rename columns");
        cy.getByTestId("column-data_uses-input")
          .eq(0)
          .type("Custom Title{enter}");
        cy.getByTestId("column-data_uses").should(
          "contain.text",
          "Custom Title",
        );
      });
    });
  });

  describe("Filtering", () => {
    it("should filter the table by making a selection", () => {
      cy.getByTestId("filter-multiple-systems-btn").click();
      cy.getByTestId("datamap-report-filter-modal").should("be.visible");
      cy.getByTestId("filter-modal-accordion-button")
        .eq(0)
        .should("have.text", "Data use");
      cy.getByTestId("filter-modal-accordion-button")
        .eq(1)
        .should("have.text", "Data categories");
      cy.getByTestId("filter-modal-accordion-button")
        .eq(2)
        .should("have.text", "Data subject");
      cy.getByTestId("filter-modal-accordion-button").eq(1).click();
      cy.getByTestId("filter-modal-checkbox-tree-categories").should(
        "be.visible",
      );
      cy.getByTestId("filter-modal-checkbox-tree-categories")
        .find("input")
        .first()
        .click({ force: true });
      cy.getByTestId("datamap-report-filter-modal")
        .contains("button", "Done")
        .click();
      cy.get("@getDatamapMinimal")
        .its("request.url")
        .should("include", "data_categories=custom");
      cy.getByTestId("datamap-report-filter-modal").should("not.exist");

      // should clear the filters
      cy.getByTestId("filter-multiple-systems-btn").click();
      cy.getByTestId("datamap-report-filter-modal")
        .contains("button", "Reset filters")
        .click();
      cy.getByTestId("datamap-report-filter-modal").should("not.exist");
      cy.wait("@getDatamapMinimal")
        .its("request.url")
        .should("not.include", "data_categories=custom");
    });
  });

  describe("Custom report templates", () => {
    beforeEach(() => {
      cy.intercept("GET", "/api/v1/plus/custom-report/plu_*", {
        fixture: "custom-reports/custom-report.json",
      }).as("getCustomReportById");
      cy.intercept("POST", "/api/v1/plus/custom-report", {
        fixture: "custom-reports/custom-report.json",
      }).as("createCustomReport");
      cy.intercept("DELETE", "/api/v1/plus/custom-report/*", "").as(
        "deleteCustomReport",
      );
    });
    it("should show an empty state when no custom reports are available", () => {
      cy.intercept("GET", "/api/v1/plus/custom-report/minimal*", {
        fixture: "empty-pagination.json",
      }).as("getEmptyCustomReports");
      cy.getByTestId("custom-reports-trigger").click();
      cy.getByTestId("custom-reports-popover").should("be.visible");
      cy.getByTestId("custom-reports-empty-state").should("be.visible");
    });
    it("should list the available reports in the popover", () => {
      cy.getByTestId("custom-reports-trigger").click();
      cy.getByTestId("custom-reports-popover").should("be.visible");
      cy.wait("@getCustomReportsMinimal");
      cy.getByTestId("custom-reports-popover").within(() => {
        cy.getByTestId("custom-report-item").should("have.length", 2);
      });
    });
    it("should allow the user to select a report", () => {
      cy.wait("@getCustomReportsMinimal");
      cy.getByTestId("custom-reports-trigger")
        .should("contain.text", "Reports")
        .click();
      cy.getByTestId("custom-reports-popover").within(() => {
        cy.getByTestId("custom-report-item").first().click();
      });
      cy.wait("@getCustomReportById");
      cy.getByTestId("apply-report-button").click();
      cy.getByTestId("custom-reports-popover").should("not.be.visible");
      cy.shouldShowMessage("success", "Report applied successfully.");
      cy.getByTestId("custom-reports-trigger").should(
        "contain.text",
        "My Custom Report",
      );
      cy.getByTestId("fidesTable").within(() => {
        // reordering applied to report
        cy.get("thead th").eq(2).should("contain.text", "Legal name");
        // column visibility applied to report
        cy.getByTestId("column-data_subjects").should("not.exist");
      });
      cy.getByTestId("group-by-menu").should(
        "contain.text",
        "Group by data use",
      );
      cy.getByTestId("more-menu").click();
      cy.selectAntDropdownOption("Edit columns");
      cy.get("button#data_subjects").should(
        "have.attr",
        "aria-checked",
        "false",
      );
      cy.getAntModalClose().click();
      cy.getByTestId("filter-multiple-systems-btn").click();
      cy.getByTestId("datamap-report-filter-modal")
        .should("be.visible")
        .within(() => {
          cy.getByTestId("filter-modal-accordion-button").eq(0).click();
          cy.getByTestId("checkbox-Analytics").within(() => {
            cy.get("[data-checked]").should("exist");
          });
          cy.get(".ant-modal-close").click();
        });
      cy.getByTestId("column-data_categories").should(
        "contain.text",
        "My Data Category Map",
      );
    });
    it("should allow the user to reset a report", () => {
      cy.wait("@getCustomReportsMinimal");
      cy.getByTestId("custom-reports-trigger")
        .should("contain.text", "Reports")
        .click();
      cy.getByTestId("custom-reports-popover").within(() => {
        cy.getByTestId("custom-report-item").first().click();
      });
      cy.wait("@getCustomReportById");
      cy.getByTestId("apply-report-button").click();
      cy.getByTestId("custom-reports-popover").should("not.be.visible");
      cy.getByTestId("custom-reports-trigger")
        .should("contain.text", "My Custom Report")
        .click();
      cy.getByTestId("custom-reports-reset-button").click();
      cy.getByTestId("apply-report-button").click();
      cy.getByTestId("custom-reports-popover").should("not.be.visible");

      cy.getByTestId("custom-reports-trigger").should(
        "contain.text",
        "Reports",
      );
      cy.getByTestId("fidesTable").within(() => {
        // reordering reverted
        cy.get("thead th").eq(2).should("contain.text", "Data categories");
        // column visibility restored
        cy.getByTestId("column-data_subjects").should("exist");
      });
      cy.getByTestId("group-by-menu").should("contain.text", "Group by system");
      cy.getByTestId("more-menu").click();
      cy.selectAntDropdownOption("Edit columns");
      cy.get("button#data_subjects").should(
        "have.attr",
        "aria-checked",
        "true",
      );
      cy.getAntModalClose().click();
      cy.getByTestId("filter-multiple-systems-btn").click();
      cy.getByTestId("datamap-report-filter-modal")
        .should("be.visible")
        .within(() => {
          cy.getByTestId("filter-modal-accordion-button").eq(0).click();
          cy.getByTestId("checkbox-Analytics").within(() => {
            cy.get("[data-checked]").should("not.exist");
          });
          cy.get(".ant-modal-close").click();
        });
    });
    it("should allow the user cancel a report selection", () => {
      cy.wait("@getCustomReportsMinimal");
      cy.getByTestId("custom-reports-trigger")
        .should("contain.text", "Reports")
        .click();
      cy.getByTestId("custom-reports-popover").within(() => {
        cy.getByTestId("custom-report-item").first().click();
      });
      cy.wait("@getCustomReportById");
      cy.getByTestId("custom-report-popover-cancel").click();
      cy.getByTestId("custom-reports-popover").should("not.be.visible");
      cy.get(".ant-message-success").should("not.exist");
    });
    it("should not be affected by the user's custom column settings", () => {
      cy.wait("@getCustomReportsMinimal");
      cy.getByTestId("custom-reports-trigger")
        .should("contain.text", "Reports")
        .click();
      cy.getByTestId("custom-reports-popover").within(() => {
        cy.getByTestId("custom-report-item").first().click();
      });
      cy.wait("@getCustomReportById");
      cy.getByTestId("apply-report-button").click();
      cy.getByTestId("data_categories-header-menu").click();
      cy.getAntDropdownOverlay("data_categories-header-menu-list").within(
        () => {
          cy.selectAntDropdownOption("Expand all");
        },
      );
      cy.getByTestId("custom-reports-trigger").should(
        "contain.text",
        "My Custom Report",
      );
    });
    it("should show an error if the report fails to load", () => {
      cy.intercept("GET", "/api/v1/plus/custom-report/plu_*", {
        statusCode: 500,
        body: "Internal Server Error",
      }).as("getCustomReportById500");
      cy.getByTestId("custom-reports-trigger").click();
      cy.wait("@getCustomReportsMinimal");
      cy.getByTestId("custom-reports-popover").within(() => {
        cy.getByTestId("custom-report-item").first().click();
      });
      cy.wait("@getCustomReportById500");
      cy.shouldShowMessage("error");
    });
    it("should allow an authorized user to create a new report", () => {
      cy.getByTestId("custom-reports-trigger").click();
      cy.wait("@getCustomReportsMinimal");
      cy.getByTestId("custom-reports-popover").should("be.visible");
      cy.getByTestId("custom-reports-popover").within(() => {
        cy.getByTestId("create-report-button").click();
      });
      cy.getByTestId("custom-report-form").should("be.visible");
      cy.getByTestId("custom-report-form").within(() => {
        cy.get("#reportName").type("My Custom Report").blur();
        cy.getByTestId("error-reportName").should("exist");
        cy.get("#reportName").clear();
      });
      cy.getByTestId("custom-report-form").should("be.visible");
      cy.getByTestId("custom-report-form").within(() => {
        cy.get("#reportName").type("My new report");
        cy.getByTestId("error-reportName").should("not.exist");
        cy.getByTestId("custom-report-form-submit").click();
      });
      cy.wait("@createCustomReport").then((interception) => {
        expect(interception.request.body.name).to.equal("My new report");
        expect(interception.request.body.type).to.equal(ReportType.DATAMAP);
        expect(interception.request.body.config).to.not.be.empty;
      });
      cy.wait(["@getDatamapMinimal", "@getDatamapMinimal"]);
      cy.getByTestId("custom-reports-popover").should("be.visible");
    });
    it("should allow an authorized user to delete a report", () => {
      cy.getByTestId("custom-reports-trigger").click();
      cy.wait("@getCustomReportsMinimal");
      cy.getByTestId("custom-reports-popover").within(() => {
        cy.getByTestId("delete-report-button").first().click();
      });
      cy.getByTestId("confirmation-modal").should("be.visible");
      cy.getByTestId("confirmation-modal").within(() => {
        cy.getByTestId("continue-btn").click();
      });
      cy.wait("@deleteCustomReport")
        .its("request.url")
        .should("include", "1234");
    });
  });

  describe("Exporting", () => {
    it("should open the export modal", () => {
      cy.getByTestId("export-btn").click();
      cy.getByTestId("export-modal").should("be.visible");
      cy.getByTestId("export-format-select").should("be.visible");
      cy.getByTestId("export-modal")
        .contains("button", "Download")
        .should("be.visible");
      cy.getByTestId("export-modal").contains("button", "Cancel").click();
      cy.getByTestId("export-modal").should("not.exist");
    });

    // ideally we should test the downloads, but it's a bit complex and time consuming so deferring for now
    it.skip("should download the export file", () => {});
  });

  describe("System preview drawer", () => {
    it("should open the system preview drawer", () => {
      cy.getByTestId("row-0-col-system_name").within(() => {
        cy.getByTestId("interactive-text-cell").click();
      });
      cy.getByTestId("datamap-drawer").should("be.visible");
      cy.getAntDrawerClose().click({ force: true });
      cy.getByTestId("datamap-drawer").should("not.exist");
    });
    it("should open the system preview drawer when grouped by data use", () => {
      cy.getByTestId("group-by-menu").click();
      cy.selectAntDropdownOption("Data use");
      cy.wait("@getDatamapMinimal");
      cy.getByTestId("row-0-col-system_name").within(() => {
        cy.getByTestId("interactive-text-cell").click();
      });
      cy.getByTestId("datamap-drawer").should("be.visible");
      cy.getAntDrawerClose().click({ force: true });
      cy.getByTestId("datamap-drawer").should("not.exist");
    });
  });
});
