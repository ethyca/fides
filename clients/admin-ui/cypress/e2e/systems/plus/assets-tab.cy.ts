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

import { ADD_SYSTEMS_MANUAL_ROUTE } from "~/features/common/nav/routes";

describe("System Assets Tab", () => {
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

  it("does not allow system assets to be edited when locked", () => {
    cy.getByTestId("vendor-name-select").find("input").type("Aniview");
    cy.getByTestId("vendor-name-select").antSelect("Aniview LTD");
    cy.getByTestId("save-btn").click();
    cy.wait(["@postSystem", "@getSystem", "@getSystems"]);

    cy.getAntTab("Assets").click();

    cy.getByTestId("col-select").should("not.exist");
    cy.getByTestId("col-actions").should("not.exist");
    cy.getByTestId("add-asset-btn").should("not.exist");
    cy.getByTestId("row-0").within(() => {
      cy.getByTestId("system-badge").should("not.have.attr", "onClick");
      cy.getByTestId("taxonomy-add-btn").should("not.exist");
    });
  });
});
