import { stubPlus } from "cypress/support/stubs";

describe("Nav Bar", () => {
  beforeEach(() => {
    cy.login();
  });

  it("renders all navigation groups with links inside", () => {
    cy.visit("/");

    cy.get(".ant-menu-submenu-title").should("have.length", 4);
    cy.getByTestId("Overview-nav-group")
      .click()
      .parents(".ant-menu-submenu")
      .within(() => {
        cy.getByTestId("Home-nav-link");
      });
    cy.getByTestId("Data inventory-nav-group")
      .click()
      .parents(".ant-menu-submenu")
      .within(() => {
        cy.getByTestId("System inventory-nav-link");
        cy.getByTestId("Add systems-nav-link");
        cy.getByTestId("Manage datasets-nav-link");
      });
    cy.getByTestId("Privacy requests-nav-group")
      .click()
      .parents(".ant-menu-submenu")
      .within(() => {
        cy.getByTestId("Request manager-nav-link");
        cy.getByTestId("Connection manager-nav-link");
      });
    cy.getByTestId("Settings-nav-group")
      .click()
      .parents(".ant-menu-submenu")
      .within(() => {
        cy.getByTestId("Users-nav-link");
        cy.getByTestId("Organization-nav-link");
        cy.getByTestId("Taxonomy-nav-link");
        cy.getByTestId("About Fides-nav-link");
      });
  });

  it("renders the Consent and Detection & Discovery navs with Plus", () => {
    stubPlus(true);
    cy.visit("/");

    cy.get(".ant-menu-submenu-title").should("have.length", 6);
    cy.getByTestId("Detection & Discovery-nav-group")
      .click()
      .parents(".ant-menu-submenu")
      .within(() => {
        cy.getByTestId("Activity-nav-link").should("exist");
        cy.getByTestId("Data detection-nav-link").should("exist");
        cy.getByTestId("Data discovery-nav-link").should("exist");
      });
  });

  it("styles the active navigation link based on the current route", () => {
    const ACTIVE_COLOR = "rgb(43, 46, 53)";
    // Start on the Home page
    cy.visit("/");

    // The nav should reflect the active page.
    cy.getByTestId("Overview-nav-group").click();

    cy.getByTestId("Home-nav-link")
      .should("have.css", "color")
      .should("eql", ACTIVE_COLOR);

    cy.getByTestId("Data inventory-nav-group").click();
    cy.getByTestId("System inventory-nav-link")
      .should("have.css", "color")
      .should("not.eql", ACTIVE_COLOR);

    // Navigate by clicking a nav link.
    cy.getByTestId("System inventory-nav-link").click();

    // The nav should update which page is active.
    cy.getByTestId("Home-nav-link")
      .should("have.css", "color")
      .should("not.eql", ACTIVE_COLOR);
    cy.getByTestId("System inventory-nav-link")
      .should("have.css", "color")
      .should("eql", ACTIVE_COLOR);
  });

  it("can collapse nav groups and persist across page views", () => {
    cy.visit("/");
    cy.getByTestId("Privacy requests-nav-group").click();
    cy.getByTestId("Request manager-nav-link").should("be.visible");
    cy.getByTestId("Privacy requests-nav-group").click();
    cy.getByTestId("Request manager-nav-link").should("not.be.visible");

    // Move to another page
    cy.getByTestId("Data inventory-nav-group").click();
    cy.getByTestId("System inventory-nav-link").click();
    cy.getByTestId("Request manager-nav-link").should("not.be.visible");
  });
});
