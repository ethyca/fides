import {
  stubDatasetCrud,
  stubPlus,
  stubSystemCrud,
  stubSystemIntegrations,
  stubSystemVendors,
  stubTaxonomyEntities,
} from "cypress/support/stubs";

import {
  INTEGRATION_MANAGEMENT_ROUTE,
  SYSTEM_ROUTE,
} from "~/features/common/nav/routes";
import { RoleRegistryEnum } from "~/types/api";

describe("Plus Permissions", () => {
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
    cy.assumeRole(RoleRegistryEnum.VIEWER);
    cy.visit(`${SYSTEM_ROUTE}/configure/demo_analytics_system`);
  });

  it("can view a system page as a viewer", () => {
    cy.getByTestId("input-name").should("exist");
  });

  it("can access integration management page from system edit page", () => {
    cy.getByTestId("integration-page-btn").click();
    cy.url().should("contain", INTEGRATION_MANAGEMENT_ROUTE);
  });
});
