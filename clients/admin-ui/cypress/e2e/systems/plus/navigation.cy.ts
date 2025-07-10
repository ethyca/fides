import {
  stubDatasetCrud,
  stubPlus,
  stubSystemCrud,
  stubSystemIntegrations,
  stubSystemVendors,
  stubTaxonomyEntities,
} from "cypress/support/stubs";

import {
  SYSTEM_ROUTE,
} from "~/features/common/nav/routes";

describe("System Navigation", () => {
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
  });

  it("updates URL hash when switching tabs", () => {
    cy.visit(`${SYSTEM_ROUTE}/configure/demo_analytics_system#information`);
    cy.location("hash").should("eq", "#information");

    // eslint-disable-next-line cypress/no-unnecessary-waiting
    cy.wait(500);
    cy.getAntTab("Data uses").click({ force: true });
    cy.location("hash").should("eq", "#data-uses");

    // eslint-disable-next-line cypress/no-unnecessary-waiting
    cy.wait(500);
    cy.getAntTab("Data flow").click({ force: true });
    cy.location("hash").should("eq", "#data-flow");

    // eslint-disable-next-line cypress/no-unnecessary-waiting
    cy.wait(500);
    cy.getAntTab("Integrations").click({ force: true });
    cy.location("hash").should("eq", "#integrations");

    // eslint-disable-next-line cypress/no-unnecessary-waiting
    cy.wait(500);
    cy.getAntTab("Assets").click({ force: true });
    cy.location("hash").should("eq", "#assets");

    // eslint-disable-next-line cypress/no-unnecessary-waiting
    cy.wait(500);
    cy.getAntTab("History").click({ force: true });
    cy.location("hash").should("eq", "#history");
  });

  it("loads correct tab directly based on URL hash", () => {
    // Visit page with specific hash
    cy.visit(`${SYSTEM_ROUTE}/configure/demo_analytics_system#data-uses`);

    // Verify correct tab is active
    cy.getAntTab("Data uses").should("have.attr", "aria-selected", "true");
    cy.location("hash").should("eq", "#data-uses");
  });
});
