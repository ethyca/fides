import {
  stubDataCatalog,
  stubPlus,
  stubStagedResourceActions,
  stubSystemCrud,
  stubTaxonomyEntities,
} from "cypress/support/stubs";

import { DATA_CATALOG_ROUTE } from "~/features/common/nav/v2/routes";

describe("data catalog", () => {
  beforeEach(() => {
    cy.login();
    stubPlus(true);
    stubDataCatalog();
    stubTaxonomyEntities();
    stubSystemCrud();
  });

  describe("systems table", () => {
    beforeEach(() => {
      cy.visit(DATA_CATALOG_ROUTE);
      cy.wait("@getCatalogSystems");
    });

    it("should display systems table", () => {
      cy.getByTestId("row-bigquery_system-col-name").should(
        "contain",
        "BigQuery System",
      );
    });
    it("should be able to add a data use", () => {
      cy.getByTestId("row-bigquery_system-col-data-uses").within(() => {
        cy.getByTestId("taxonomy-add-btn").click();
        cy.get(".select-wrapper").should("be.visible");
      });
    });

    it("should navigate to database view when clicking a system with projects", () => {
      cy.getByTestId("row-bigquery_system-col-name").click();
      cy.wait("@getAvailableDatabases");
      cy.url().should("include", "/bigquery_system/projects");
    });

    it("should navigate to dataset view when clicking a system without projects", () => {
      cy.intercept("POST", "/api/v1/plus/discovery-monitor/databases*", {
        fixture: "empty-pagination",
      }).as("getEmptyAvailableDatabases");
      cy.getByTestId("row-dynamo_system-col-name").click();
      cy.wait("@getEmptyAvailableDatabases");
      cy.url().should("not.include", "/projects");
    });

    describe("system detail drawer", () => {
      it("should be able to navigate to system details via the detail drawer", () => {
        cy.getByTestId("row-bigquery_system").within(() => {
          cy.getByTestId("system-actions-menu").click();
          cy.getByTestId("view-system-details").click({ force: true });
        });
        cy.getByTestId("system-details").should("be.visible");
        cy.getByTestId("edit-system-btn").click();
        cy.url().should("include", "/systems/configure/bigquery_system");
      });

      it("should be able to add data uses via the detail drawer", () => {
        cy.getByTestId("row-bigquery_system").within(() => {
          cy.getByTestId("system-actions-menu").click();
          cy.getByTestId("view-system-details").click({ force: true });
        });
        cy.getByTestId("system-details").within(() => {
          cy.getByTestId("taxonomy-add-btn").click();
          cy.get(".select-wrapper").should("be.visible");
        });
      });
    });
  });

  describe("projects table", () => {
    beforeEach(() => {
      cy.visit(`${DATA_CATALOG_ROUTE}/bigquery_system/projects`);
      cy.wait("@getCatalogProjects");
    });

    it("should show projects with appropriate statuses", () => {
      cy.getByTestId(
        "row-bigquery_monitor.prj-bigquery-111111-col-status",
      ).should("contain", "Attention required");
      cy.getByTestId(
        "row-bigquery_monitor.prj-bigquery-222222-col-status",
      ).should("contain", "Classifying");
      cy.getByTestId(
        "row-bigquery_monitor.prj-bigquery-333333-col-status",
      ).should("contain", "In review");
      cy.getByTestId(
        "row-bigquery_monitor.prj-bigquery-444444-col-status",
      ).should("contain", "Approved");
    });

    it("should navigate to dataset view on click", () => {
      cy.getByTestId(
        "row-bigquery_monitor.prj-bigquery-111111-col-name",
      ).click();
      cy.url().should(
        "include",
        "/projects/bigquery_monitor.prj-bigquery-111111",
      );
    });

    it("should be able to view details in the drawer", () => {
      cy.getByTestId(
        "row-bigquery_monitor.prj-bigquery-111111-col-actions",
      ).within(() => {
        cy.getByTestId("actions-menu").click();
        cy.getByTestId("view-resource-details").click({ force: true });
      });
      cy.getByTestId("resource-details").should("be.visible");
    });
  });

  describe("resource tables", () => {
    beforeEach(() => {
      stubStagedResourceActions();
      cy.visit(
        `${DATA_CATALOG_ROUTE}/bigquery_system/projects/monitor.project/monitor.project.test_dataset_1`,
      );
    });

    it("should display the table", () => {
      cy.getByTestId("row-monitor.project.dataset.table_1-col-name").should(
        "contain",
        "table_1",
      );
    });

    it("should be able to take actions on resources", () => {
      cy.getByTestId("row-monitor.project.dataset.table_1-col-actions").within(
        () => {
          cy.getByTestId("classify-btn").click();
          cy.wait("@confirmResource");
        },
      );
      cy.getByTestId("row-monitor.project.dataset.table_2-col-actions").within(
        () => {
          cy.getByTestId("actions-menu").click();
          cy.getByTestId("hide-resource").click({ force: true });
          cy.wait("@ignoreResource");
        },
      );
      cy.getByTestId("row-monitor.project.dataset.table_3-col-actions").within(
        () => {
          cy.getByTestId("approve-btn").click();
          cy.wait("@promoteResource");
        },
      );
    });

    describe("resource detail drawer", () => {
      it("should be able to view resource details", () => {
        cy.getByTestId("row-monitor.project.dataset.table_1").within(() => {
          cy.getByTestId("actions-menu").click();
          cy.getByTestId("view-resource-details").click({ force: true });
        });
        cy.getByTestId("resource-details")
          .should("be.visible")
          .within(() => {
            // don't edit categories unless resource has the right status
            cy.getByTestId("edit-category-cell").should("not.exist");
          });
      });
      it("should be able to edit data categories where applicable", () => {
        cy.getByTestId("row-monitor.project.dataset.table_3").within(() => {
          cy.getByTestId("actions-menu").click();
          cy.getByTestId("view-resource-details").click({ force: true });
        });
        cy.getByTestId("resource-details").within(() => {
          cy.getByTestId("user-classification-system").should("exist");
        });
      });
    });
  });
});
