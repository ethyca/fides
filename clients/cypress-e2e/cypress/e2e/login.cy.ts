import { CREDENTIALS } from "../support/constants";

describe("Log in", () => {
  it("can log in and be redirected to the home page", () => {
    cy.visit("localhost:3000");
    cy.getByTestId("input-username").type(CREDENTIALS.username);
    cy.getByTestId("input-password").type(CREDENTIALS.password);
    cy.getByTestId("sign-in-btn").click();
    cy.getByTestId("Home");
  });
});
