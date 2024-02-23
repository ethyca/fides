describe("Nav Bar", () => {
  beforeEach(() => {
    cy.login();
  });

  it("renders all navigation groups with links inside", () => {
    cy.visit("/");

    cy.get("nav button").should("have.length", 7);
    cy.getByTestId("Overview-nav-group").within(() => {
      cy.getByTestId("Home-nav-link");
    });
    cy.getByTestId("Data map-nav-group").within(() => {
      cy.getByTestId("Systems & vendors-nav-link");
      cy.getByTestId("Add systems-nav-link");
      cy.getByTestId("Manage datasets-nav-link");
    });
    cy.getByTestId("Privacy requests-nav-group").within(() => {
      cy.getByTestId("Request manager-nav-link");
      cy.getByTestId("Connection manager-nav-link");
    });
    cy.getByTestId("Management-nav-group").within(() => {
      cy.getByTestId("Users-nav-link");
      cy.getByTestId("Organization-nav-link");
      cy.getByTestId("Taxonomy-nav-link");
      cy.getByTestId("About Fides-nav-link");
    });
  });

  it("styles the active navigation link based on the current route", () => {
    const ACTIVE_COLOR = "rgb(119, 69, 240)";
    // Start on the Home page
    cy.visit("/");

    // The nav should reflect the active page.
    cy.getByTestId("Home-nav-link")
      .should("have.css", "background-color")
      .should("eql", ACTIVE_COLOR);
    cy.getByTestId("Systems & vendors-nav-link")
      .should("have.css", "background-color")
      .should("not.eql", ACTIVE_COLOR);

    // Navigate by clicking a nav link.
    cy.getByTestId("Systems & vendors-nav-link").click();

    // The nav should update which page is active.
    cy.getByTestId("Home-nav-link")
      .should("have.css", "background-color")
      .should("not.eql", ACTIVE_COLOR);
    cy.getByTestId("Systems & vendors-nav-link")
      .should("have.css", "background-color")
      .should("eql", ACTIVE_COLOR);
  });

  it("can collapse nav groups and persist across page views", () => {
    cy.visit("/");
    cy.getByTestId("Request manager-nav-link").should("be.visible");
    cy.getByTestId("Privacy requests-nav-group").within(() => {
      cy.get("button").click();
    });
    cy.getByTestId("Request manager-nav-link").should("not.be.visible");

    // Move to another page
    cy.getByTestId("Systems & vendors-nav-link").click();
    cy.getByTestId("Request manager-nav-link").should("not.be.visible");
  });
});
