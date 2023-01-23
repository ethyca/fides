import { stubHomePage } from "cypress/support/stubs";

describe("Home", () => {
  beforeEach(() => {
    cy.login();
    cy.visit("/");
    cy.location("pathname").should("eq", "/");
  });

  it("User has connections and systems", () => {
    stubHomePage(true, true);
    cy.getByTestId("configure-privacy-requests-card").should("be.visible");
    cy.getByTestId("review-privacy-requests-card").should("be.visible");
    cy.getByTestId("add-systems-card").should("be.visible");
    cy.getByTestId("manage-systems-card").should("be.visible");
  });

  it("User has connections and but no systems", () => {
    stubHomePage(true, false);
    cy.getByTestId("configure-privacy-requests-card").should("be.visible");
    cy.getByTestId("review-privacy-requests-card").should("be.visible");
    cy.getByTestId("add-systems-card").should("be.visible");
    cy.getByTestId("manage-systems-card").should("not.exist");
  });

  it("User has no connections and but has systems", () => {
    stubHomePage(false, true);
    cy.getByTestId("configure-privacy-requests-card").should("be.visible");
    cy.getByTestId("review-privacy-requests-card").should("not.exist");
    cy.getByTestId("add-systems-card").should("be.visible");
    cy.getByTestId("manage-systems-card").should("be.visible");
  });

  it("User has no connections and no systems", () => {
    stubHomePage(false, false);
    cy.getByTestId("configure-privacy-requests-card").should("be.visible");
    cy.getByTestId("review-privacy-requests-card").should("not.exist");
    cy.getByTestId("add-systems-card").should("be.visible");
    cy.getByTestId("manage-systems-card").should("not.exist");
  });
});
