describe("Log in", () => {
  it("can log in and be redirected to the home page", () => {
    cy.visit("localhost:3000");
    cy.login();
    cy.getByTestId("Home");
  });
});
