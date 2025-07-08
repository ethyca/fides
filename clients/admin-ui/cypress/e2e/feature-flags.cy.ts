import {
  stubFeatureFlags,
  stubLogout,
  stubOpenIdProviders,
  stubPlus,
  stubPlusAuth,
} from "cypress/support/stubs";

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
    cy.window()
      .its("localStorage")
      .invoke("getItem", "persist:root")
      .then((value) => {
        const { features } = JSON.parse(value);
        expect(features).to.equal(
          '{"flags":{"webMonitor":{"development":false,"test":true,"production":false}},"showNotificationBanner":true}',
        );
      });

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
      .invoke("getItem", "persist:root")
      .then((value) => {
        cy.login(JSON.parse(value));
      });
    stubFeatureFlags();

    // Navigate to feature flags
    cy.visit("/settings/about");
    cy.wait("@createConfigurationSettings");

    // Check that both UI and localStorage state remain unchanged
    cy.window()
      .its("localStorage")
      .invoke("getItem", "persist:root")
      .then((value) => {
        const { features } = JSON.parse(value);
        expect(features).to.equal(
          '{"flags":{"webMonitor":{"development":false,"test":true,"production":false}},"showNotificationBanner":true}',
        );
      });
    cy.get("@flag").should("have.attr", "aria-checked", "false");
  });
});
