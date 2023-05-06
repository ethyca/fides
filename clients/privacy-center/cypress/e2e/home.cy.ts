describe("Home", () => {
  it("renders the configured page info", () => {
    cy.visit("/");
    cy.loadConfigFixture("config/config_all.json").then((config) => {
      // DEFER: Test *all* the configurable display options
      // (see https://github.com/ethyca/fides/issues/3216)
      cy.getByTestId("home");

      cy.getByTestId("heading").contains(config.title);
      cy.getByTestId("description").contains(config.description);
      cy.getByTestId("logo").should("have.attr", "src", config.logo_path);

      config.actions.forEach((action) => {
        cy.contains(action.title);
      });
    });
  });

  it("renders an error page if configuration is invalid", () => {
    cy.visit("/");
    cy.loadConfigFixture("config/config_error.json").then(() => {
      cy.contains("an unexpected error occurred");
    });
  });

  it("renders a 404 page for non-existent routes", () => {
    cy.visit("/404", { failOnStatusCode: false });
    cy.contains("Error: 404");
  });
});
