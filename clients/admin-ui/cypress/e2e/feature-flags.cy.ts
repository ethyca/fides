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
    cy.get("@flag").should("have.attr", "aria-checked", "true");

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

  it("Override feature flags programmatically via Cypress command", () => {
    // Initial Login
    stubOpenIdProviders();
    stubPlusAuth();
    cy.login();
    stubPlus(true);

    // Set flags BEFORE visiting the page - this is the ideal pattern
    cy.overrideFeatureFlag("webMonitor", false);
    cy.overrideFeatureFlag("dataCatalog", false);

    // Navigate to feature flags
    stubFeatureFlags();
    cy.visit("/settings/about");
    cy.wait("@createConfigurationSettings");

    // Verify the flags were set correctly on initial load
    cy.get("#flag-webMonitor").should("have.attr", "aria-checked", "false");
    cy.get("#flag-dataCatalog").should("have.attr", "aria-checked", "false");

    // Can also override after the page loads and it updates automatically
    cy.overrideFeatureFlag("webMonitor", true);
    cy.get("#flag-webMonitor").should("have.attr", "aria-checked", "true");
  });

  it("Set flags before visiting any page for feature-specific tests", () => {
    stubOpenIdProviders();
    stubPlusAuth();
    cy.login();
    stubPlus(true);

    // This pattern is useful when testing features behind flags
    // Set the flag before navigating to test the enabled state
    cy.overrideFeatureFlag("dataCatalog", false);

    // Now visit a page that uses this flag
    cy.visit("/data-catalog");
    // The feature will be disabled from the start
    cy.getByTestId("Data catalog").should("not.exist");
  });
});
