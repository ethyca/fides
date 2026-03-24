import { stubPlus } from "cypress/support/stubs";

import { ADD_SYSTEMS_ROUTE } from "~/features/common/nav/routes";

/**
 * Fides+ config wizard. The legacy runtime (Pixie) cluster scanner was removed;
 * AWS and Okta discovery flows are covered in config-wizard.cy.ts.
 */
describe("Config wizard with plus settings", () => {
  beforeEach(() => {
    cy.login();
    cy.intercept("GET", "/api/v1/organization/*", {
      fixture: "organizations/default_organization.json",
    }).as("getOrganization");
    stubPlus(true);
  });

  it("loads add systems when Plus health is available", () => {
    cy.visit(ADD_SYSTEMS_ROUTE);
    cy.wait("@getPlusHealth");
    cy.getByTestId("add-systems");
    cy.getByTestId("aws-btn").should("be.visible");
    cy.getByTestId("okta-btn").should("be.visible");
    cy.getByTestId("manual-options");
    cy.getByTestId("automated-options");
  });
});
