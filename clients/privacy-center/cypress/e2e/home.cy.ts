import { config } from "~/constants";

describe("Home", () => {
  it("renders the configured page info", () => {
    cy.visit("/");
    cy.getByTestId("home");

    cy.getByTestId("heading").contains(config.title);
    cy.getByTestId("description").contains(config.description);
    cy.getByTestId("logo").should("have.attr", "src", config.logo_path);

    config.actions.forEach((action) => {
      cy.contains(action.title);
    });
  });
});
