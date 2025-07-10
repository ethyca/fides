import {
  stubDatasetCrud,
  stubPlus,
  stubSystemAssets,
  stubSystemCrud,
  stubSystemIntegrations,
  stubSystemVendors,
  stubTaxonomyEntities,
  stubVendorList,
} from "cypress/support/stubs";

import {
  ADD_SYSTEMS_MANUAL_ROUTE,
} from "~/features/common/nav/routes";

describe("System Data Uses Tab", () => {
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
    stubVendorList();
    stubSystemAssets();
    cy.visit(`${ADD_SYSTEMS_MANUAL_ROUTE}`);
    cy.wait(["@getDictionaryEntries", "@getSystems"]);
  });

  it("allowed changes to data uses for GVL vendors", () => {
    // TODO: create reusable GVL vendor
    cy.getByTestId("vendor-name-select").find("input").type("Aniview");
    cy.getByTestId("vendor-name-select").antSelect("Aniview LTD");
    cy.getByTestId("save-btn").click();
    cy.wait(["@postSystem", "@getSystem", "@getSystems"]);

    cy.getAntTab("Data uses").click();

    // Check crud actions
    cy.getByTestId("add-btn");
    cy.getByTestId("delete-btn");
    cy.getByTestId("row-functional.service.improve").click();

    // Check state of available inputs
    cy.getByTestId("controlled-select-data_categories")
      .find("input")
      .should("be.disabled");
    cy.getByTestId("controlled-select-data_subjects")
      .find("input")
      .should("not.be.disabled");
    cy.getByTestId("input-impact_assessment_location").should("not.be.disabled");
    cy.getByTestId("input-processes_special_category_data").should("not.be.disabled");
    cy.getByTestId("controlled-select-dataset_references").find("input").should("not.be.disabled");
    cy.getByTestId("input-data_shared_with_third_parties").click()
    cy.getByTestId("input-third_parties").should("not.be.disabled")

  });

  it("allowed changes to data uses for non-GVL vendors", () => {
    // TODO: create reusable non-GVL vendor 
    cy.getByTestId("vendor-name-select").find("input").type("L");
    cy.antSelectDropdownVisible();
    cy.getByTestId("vendor-name-select").realPress("Enter");
    cy.getByTestId("save-btn").click();
    cy.wait(["@postSystem", "@getSystem", "@getSystems"]);

    cy.getAntTab("Data uses").click();

    // Check crud actions
    cy.getByTestId("add-btn");
    cy.getByTestId("delete-btn");
    cy.getByTestId("row-functional.service.improve").click();

    // Check state of available inputs   
    cy.getByTestId("controlled-select-data_categories")
      .find("input")
      .should("not.be.disabled");
    cy.getByTestId("controlled-select-data_subjects")
      .find("input")
      .should("not.be.disabled");
    cy.getByTestId("input-impact_assessment_location").should("not.be.disabled");
    cy.getByTestId("input-processes_special_category_data").should("not.be.disabled");
    cy.getByTestId("controlled-select-dataset_references").find("input").should("not.be.disabled");
    cy.getByTestId("input-data_shared_with_third_parties").click()
    cy.getByTestId("input-third_parties").should("not.be.disabled")
  });

  it("don't allow editing declaration name after creation", () => {
    cy.getByTestId("vendor-name-select").find("input").type("L{enter}");
    cy.getByTestId("save-btn").click();
    cy.wait(["@postSystem", "@getSystem", "@getSystems"]);

    cy.getAntTab("Data uses").click();

    cy.getByTestId("row-functional.service.improve").click();
    cy.getByTestId("input-name").should("be.disabled");
  });

  it("don't allow editing data uses after creation", () => {
    cy.getByTestId("vendor-name-select").find("input").type("L");
    cy.antSelectDropdownVisible();
    cy.getByTestId("vendor-name-select").realPress("Enter");
    cy.getByTestId("save-btn").click();
    cy.wait(["@postSystem", "@getSystem", "@getSystems"]);

    cy.getAntTab("Data uses").click();

    cy.getByTestId("row-functional.service.improve").click();
    cy.getByTestId("controlled-select-data_use")
      .find("input")
      .should("be.disabled");
  });
});
