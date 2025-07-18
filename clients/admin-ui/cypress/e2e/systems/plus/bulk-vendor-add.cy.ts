import {
  stubDatasetCrud,
  stubPlus,
  stubSystemCrud,
  stubSystemIntegrations,
  stubSystemVendors,
  stubTaxonomyEntities,
} from "cypress/support/stubs";

import {
  ADD_SYSTEMS_MANUAL_ROUTE,
  ADD_SYSTEMS_MULTIPLE_ROUTE,
  ADD_SYSTEMS_ROUTE,
  DATAMAP_ROUTE,
  INDEX_ROUTE,
} from "~/features/common/nav/routes";

describe("Plus Bulk Vendor Add", () => {
  beforeEach(() => {
    cy.login();
    stubSystemCrud();
    stubTaxonomyEntities();
    stubPlus(true);
    cy.intercept("GET", "/api/v1/system", {
      fixture: "systems/systems.json",
    }).as("getSystems");
    cy.intercept({ method: "POST", url: "/api/v1/system*" }).as(
      "postDictSystem",
    );
    cy.intercept("/api/v1/config?api_set=false", {});
    stubDatasetCrud();
    stubSystemIntegrations();
    stubSystemVendors();
    stubPlus(true);
    stubSystemVendors();
  });

  it("page loads with table and rows", () => {
    cy.visit(ADD_SYSTEMS_MULTIPLE_ROUTE);

    cy.wait("@getSystemVendors");
    cy.getByTestId("fidesTable");
    cy.getByTestId("fidesTable-body")
      .find("tr")
      .should("have.length.greaterThan", 0);
  });

  it("upgrade modal doesn't pop up if compass is enabled", () => {
    cy.visit(ADD_SYSTEMS_ROUTE);
    cy.getByTestId("multiple-btn").click();
    cy.wait("@getSystemVendors");
    cy.getByTestId("fidesTable");
  });

  it("upgrade modal pops up if compass isn't enabled and redirects to manual add", () => {
    stubPlus(true, {
      core_fides_version: "2.2.0",
      fidesplus_server: "healthy",
      system_scanner: {
        enabled: true,
        cluster_health: null,
        cluster_error: null,
      },
      dictionary: {
        enabled: false,
        service_health: null,
        service_error: null,
      },
      tcf: {
        enabled: true,
      },
      fidesplus_version: "",
      fides_cloud: {
        enabled: false,
      },
    });
    cy.visit(ADD_SYSTEMS_ROUTE);
    cy.getByTestId("multiple-btn").click();
    cy.getByTestId("confirmation-modal");
    cy.getByTestId("cancel-btn").click();
    cy.url().should("include", ADD_SYSTEMS_MANUAL_ROUTE);
  });

  it("can add new systems and redirects to datamap", () => {
    cy.visit(ADD_SYSTEMS_MULTIPLE_ROUTE);
    cy.wait("@getSystemVendors");
    cy.get('[type="checkbox"').check({ force: true });
    cy.getByTestId("add-multiple-systems-btn")
      .should("exist")
      .click({ force: true });
    cy.getByTestId("confirmation-modal");
    cy.getByTestId("continue-btn").click({ force: true });
    cy.url().should("include", DATAMAP_ROUTE);
  });

  it("select page checkbox only selects rows on the displayed page", () => {
    cy.visit(ADD_SYSTEMS_MULTIPLE_ROUTE);
    cy.wait("@getSystemVendors");
    cy.wait("@getDict");
    // unreliable test because when dictionary loads it overrides the rows selected
    // adding a .wait to make it more reliable
    // eslint-disable-next-line cypress/no-unnecessary-waiting
    cy.wait(500);
    cy.getByTestId("select-page-checkbox")
      .get("[type='checkbox']")
      .check({ force: true });
    // allow UI to update the selected rows
    // eslint-disable-next-line cypress/no-unnecessary-waiting
    cy.wait(500);
    cy.getByTestId("selected-row-count").contains("6 row(s) selected.");
  });

  it("select all button selects all rows across every page", () => {
    cy.visit(ADD_SYSTEMS_MULTIPLE_ROUTE);
    cy.wait("@getSystemVendors");
    cy.wait("@getDict");
    // unreliable test because when dictionary loads it overrides the rows selected
    // adding a .wait to make it more reliable
    // eslint-disable-next-line cypress/no-unnecessary-waiting
    cy.wait(500);
    cy.getByTestId("select-page-checkbox")
      .get("[type='checkbox']")
      .check({ force: true });
    // allow UI to update the selected rows
    // eslint-disable-next-line cypress/no-unnecessary-waiting
    cy.wait(500);
    cy.getByTestId("select-all-rows-btn").click();
    cy.getByTestId("selected-row-count").contains("8 row(s) selected.");
  });

  it("filter button and sources column are hidden when TCF is disabled", () => {
    stubPlus(true, {
      core_fides_version: "2.2.0",
      fidesplus_server: "healthy",
      system_scanner: {
        enabled: true,
        cluster_health: null,
        cluster_error: null,
      },
      dictionary: {
        enabled: true,
        service_health: null,
        service_error: null,
      },
      tcf: {
        enabled: false,
      },
      fidesplus_version: "",
      fides_cloud: {
        enabled: false,
      },
    });
    cy.visit(ADD_SYSTEMS_MULTIPLE_ROUTE);
    cy.getByTestId("filter-multiple-systems-btn").should("not.exist");
    cy.getByTestId("column-id").should("not.exist");
    cy.getByTestId("column-name").should("not.exist");
  });

  it("filter button and sources column are shown when TCF is enabled", () => {
    cy.visit(ADD_SYSTEMS_MULTIPLE_ROUTE);
    cy.getByTestId("filter-multiple-systems-btn").should("exist");
    cy.getByTestId("column-id").should("exist");
    cy.getByTestId("column-name").should("exist");
  });

  it("filter modal state is persisted after modal is closed", () => {
    cy.visit(ADD_SYSTEMS_MULTIPLE_ROUTE);
    cy.getByTestId("filter-multiple-systems-btn").click();
    cy.get("#checkbox-gvl").check({ force: true });
    cy.getByTestId("filter-done-btn").click();
    cy.getByTestId("filter-multiple-systems-btn").click();
    cy.get("#checkbox-gvl").should("be.checked");
  });

  it("pagination menu updates pagesize", () => {
    cy.visit(ADD_SYSTEMS_MULTIPLE_ROUTE);

    cy.wait("@getSystemVendors");
    cy.getByTestId("fidesTable");
    cy.getByTestId("fidesTable-body").find("tr").should("have.length", 25);
    cy.getByTestId("pagination-btn").click();
    cy.getByTestId("pageSize-50").click();
    cy.getByTestId("fidesTable-body").find("tr").should("have.length", 50);
  });

  it("redirects to index when compass is disabled", () => {
    stubPlus(true, {
      core_fides_version: "2.2.0",
      fidesplus_server: "healthy",
      system_scanner: {
        enabled: true,
        cluster_health: null,
        cluster_error: null,
      },
      dictionary: {
        enabled: false,
        service_health: null,
        service_error: null,
      },
      tcf: {
        enabled: false,
      },
      fidesplus_version: "",
      fides_cloud: {
        enabled: false,
      },
    });
    cy.visit(ADD_SYSTEMS_MULTIPLE_ROUTE);
    cy.location().should((location) => {
      expect(location.pathname).to.eq(INDEX_ROUTE);
    });
  });
});
