describe("Nav Bar", () => {
  beforeEach(() => {
    cy.login();
  });

  it("Renders all page links", () => {
    cy.visit("/");

    cy.getByTestId("nav-link-home")
      .should("have.attr", "href", "/")
      .contains("Home");

    cy.getByTestId("nav-link-privacy-requests")
      .should("have.attr", "href", "/privacy-requests")
      .contains("Privacy requests");

    cy.getByTestId("nav-link-data-map")
      .should("have.attr", "href", "/system")
      .contains("Data map");

    cy.getByTestId("nav-link-management")
      .should("have.attr", "href", "/taxonomy")
      .contains("Management");
  });
});
