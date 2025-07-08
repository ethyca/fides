import {
  stubFeatureFlags,
  stubLogout,
  stubOpenIdProviders,
  stubPlus,
  stubPlusAuth,
} from "cypress/support/stubs";
import { STORAGE_ROOT_KEY } from "~/constants";

describe("Feature Flags", () => {

  it("Persist features through logout", () => {
    // Initial Login
    stubOpenIdProviders();
    stubPlusAuth();
    cy.login();
    stubPlus(true);

    // Navigate to feature flags
    stubFeatureFlags();
    cy.visit("/settings/about");
    cy.wait("@createConfigurationSettings");

    cy.get("#flag-webMonitor").as("flag");

    // Check UI and localStorage state has updated
    cy.get("@flag").click().should("have.attr", "aria-checked", "false");

    // Logout
    stubLogout();
    cy.getByTestId("header-menu-button").click();
    cy.getByTestId("header-menu-sign-out").click({ force: true });
    stubPlus(true);
    cy.location("pathname").should("eq", "/login");
    cy.getByTestId("Login");

    // Login again with retained state
    // Note: the management of localStorage is not ideal but would require a refactor of the way auth is injected in tests.
    cy.window()
      .its("localStorage")
      .invoke("getItem", STORAGE_ROOT_KEY)
      .then((value) => {
        cy.login(JSON.parse(value));
      });
    stubFeatureFlags();

    // Navigate to feature flags
    cy.visit("/settings/about");
    cy.wait("@createConfigurationSettings");

    // Check that both UI and localStorage state remain unchanged
    cy.get("@flag").should("have.attr", "aria-checked", "false");
  });
});
