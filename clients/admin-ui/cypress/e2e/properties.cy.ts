import { stubPlus } from "cypress/support/stubs";
import { PROPERTIES_ROUTE } from "~/features/common/nav/v2/routes";

describe("Properties page", () => {
  beforeEach(() => {
    cy.login();
    stubPlus(true);
    cy.visit(PROPERTIES_ROUTE);
  });

  it("Should render properties table", () => {
    cy.intercept("GET", "/api/v1/plus/properties*", {
      fixture: "properties/properties.json",
    }).as("getProperties");
    cy.visit(PROPERTIES_ROUTE);
    cy.getByTestId("fidesTable").should("be.visible");
    cy.getByTestId("fidesTable-body").find("tr").should("have.length", 2);
  });

  it("Should show empty table notice if there are no properties", () => {
    cy.getByTestId("fidesTable").should("be.visible");
    cy.getByTestId("no-results-notice").should("be.visible");
  });
});
