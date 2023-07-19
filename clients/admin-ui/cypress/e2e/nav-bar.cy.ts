describe("Nav Bar", () => {
  beforeEach(() => {
    cy.login();
  });

  it("renders all navigation links", () => {
    cy.visit("/");

    cy.get("nav a").should("have.length", 3);
    cy.contains("nav a", "Home");
    cy.contains("nav a", "Data map");
    cy.contains("nav a", "Privacy requests");
  });

  it("styles the active navigation link based on the current route", () => {
    const ACTIVE_COLOR = "rgb(17, 20, 57)";
    // Start on the Home page
    cy.visit("/");

    // The nav should reflect the active page.
    cy.contains("nav a", "Home")
      .should("have.css", "background-color")
      .should("eql", ACTIVE_COLOR);
    cy.contains("nav a", "Data map")
      .should("have.css", "background-color")
      .should("not.eql", ACTIVE_COLOR);

    // Navigate by clicking a nav link.
    cy.contains("nav a", "Data map").click();

    // The nav should update which page is active.
    cy.contains("nav a", "Home")
      .should("have.css", "background-color")
      .should("not.eql", ACTIVE_COLOR);
    cy.contains("nav a", "Data map")
      .should("have.css", "background-color")
      .should("eql", ACTIVE_COLOR);
  });
});
