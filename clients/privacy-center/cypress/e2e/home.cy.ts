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
});
