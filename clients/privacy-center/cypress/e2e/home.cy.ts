describe("Home", () => {
  it("renders the configured page info", () => {
    cy.visit("/");
    cy.getByTestId("home");
    cy.loadConfigFixture("config/config_all.json").then((config) => {
      // DEFER: Test *all* the configurable display options
      // (see https://github.com/ethyca/fides/issues/3216)

      cy.getByTestId("heading").contains(config.title);
      cy.getByTestId("description").contains(config.description);
      cy.getByTestId("logo").should("have.attr", "src", config.logo_path);

      config.actions.forEach((action) => {
        cy.contains(action.title);
      });
    });
  });

  it("supports custom styles", () => {
    cy.visit("/");
    cy.getByTestId("home");

    // Check the before/after background-color
    // NOTE: rgb(255, 99, 71) === "tomato" 🍅
    cy.get("body").should(
      "not.have.css",
      "background-color",
      "rgb(255, 99, 71)"
    );
    const styles = "body { background-color: tomato !important; }";
    cy.dispatch({ type: "styles/loadStyles", payload: styles });
    cy.get("body").should("have.css", "background-color", "rgb(255, 99, 71)");
  });

  describe("when handling errors", () => {
    // Allow uncaught exceptions to occur without failing the test
    beforeEach(() => {
      cy.on("uncaught:exception", () => false);
    });

    it("renders an error page if configuration is missing", () => {
      cy.visit("/");
      cy.getByTestId("home");
      cy.dispatch({ type: "config/loadConfig", payload: undefined });
      cy.contains("an unexpected error occurred");
    });

    it("renders an error page if configuration is invalid", () => {
      cy.visit("/");
      cy.getByTestId("home");
      cy.loadConfigFixture("config/config_error.json").then(() => {
        cy.contains("an unexpected error occurred");
      });
    });

    it("renders a 404 page for non-existent routes", () => {
      cy.visit("/404", { failOnStatusCode: false });
      cy.contains("Error: 404");
    });
  });
});
