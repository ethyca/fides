import { ADMIN_UI_URL } from "../support/constants";

describe("Log in", () => {
  it("can log in and be redirected to the home page", () => {
    cy.visit(ADMIN_UI_URL);
    cy.login();
    cy.getByTestId("Home");
  });
});
