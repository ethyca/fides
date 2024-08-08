import { stubPlus, stubSystemCrud } from "cypress/support/stubs";

import { SYSTEM_ROUTE } from "~/features/common/nav/v2/routes";

describe("System integrations", () => {
  beforeEach(() => {
    cy.login();
    cy.intercept("GET", "/api/v1/system*", {
      fixture: "systems/systems_paginated.json",
    }).as("getSystems");
    cy.intercept("GET", "/api/v1/connection_type*", {
      fixture: "connectors/connection_types.json",
    }).as("getConnectionTypes");
    cy.intercept("GET", "/api/v1/connection_type/postgres/secret", {
      fixture: "connectors/postgres_secret.json",
    }).as("getPostgresConnectorSecret");
    cy.intercept("GET", "/api/v1/plus/dictionary/system?size=2000", {
      fixture: "dictionary-entries.json",
    }).as("getDict");
    stubPlus(true);
    stubSystemCrud();
    cy.visit(SYSTEM_ROUTE);
  });

  it("should render the integration configuration panel when navigating to integrations tab", () => {
    cy.getByTestId("system-fidesctl_system").within(() => {
      cy.getByTestId("edit-btn").click();
    });
    cy.wait("@getDict");
    cy.getByTestId("tab-Integrations").click();
    cy.getByTestId("tab-panel-Integrations").should("exist");
  });

  describe("Integration search", () => {
    beforeEach(() => {
      cy.getByTestId("system-fidesctl_system").within(() => {
        cy.getByTestId("edit-btn").click();
      });
      cy.getByTestId("tab-Integrations").click();
      cy.getByTestId("select-dropdown-btn").click();
    });

    it("should display Shopify when searching with upper case letters", () => {
      cy.getByTestId("input-search-integrations").type("Sho");
      cy.getByTestId("select-dropdown-list")
        .find('[role="menuitem"] p')
        .should("contain.text", "Shopify");
    });

    it("should display Shopify when searching with lower case letters", () => {
      cy.getByTestId("input-search-integrations").type("sho");
      cy.getByTestId("select-dropdown-list")
        .find('[role="menuitem"] p')
        .should("contain.text", "Shopify");
    });
  });

  describe("Integration form contents", () => {
    beforeEach(() => {
      cy.getByTestId("system-fidesctl_system").within(() => {
        cy.getByTestId("edit-btn").click();
      });
      cy.getByTestId("tab-Integrations").click();
      cy.getByTestId("select-dropdown-btn").click();

      cy.getByTestId("input-search-integrations").type("PostgreSQL");
      cy.getByTestId("select-dropdown-list")
        .contains('[role="menuitem"]', /^PostgreSQL$/)
        .click();
    });

    // Verify Postgres shows access and erasure by default
    it("should display Request types (enabled-actions) field", () => {
      cy.getByTestId("enabled-actions").should("exist");
      cy.getByTestId("enabled-actions").within(() => {
        cy.contains("Access");
        cy.contains("Erasure");
        cy.contains("Consent").should("not.exist");
      });
    });
  });

  describe("Consent automation", () => {
    beforeEach(() => {
      cy.intercept("GET", "/api/v1/system/*", {
        fixture: "systems/system_active_integration.json",
      });
      cy.intercept("GET", "/api/v1/plus/connection/*/consentable-items", {
        fixture: "connectors/consentable_items.json",
      });
      cy.intercept("PUT", "/api/v1/plus/connection/*/consentable-items", {
        fixture: "connectors/consentable_items.json",
      }).as("putConsentableItems");
      cy.intercept("GET", "/api/v1/privacy-notice*", {
        fixture: "privacy-notices/list.json",
      }).as("getNotices");
      cy.getByTestId("system-fidesctl_system").within(() => {
        cy.getByTestId("edit-btn").click();
      });
      cy.getByTestId("tab-Integrations").click();
    });
    it("should render the consent automation accordion panel", () => {
      cy.getByTestId("accordion-consent-automation").click();
      cy.getByTestId("accordion-panel-consent-automation").should("exist");
      cy.getByTestId("consentable-item-label").should("have.length", 5);
      cy.getByTestId("consentable-item-label-child").should("have.length", 6);
      cy.getByTestId("consentable-item-select").should("have.length", 11);
      cy.getByTestId("consentable-item-select")
        .first()
        .within(() => {
          cy.get(".custom-select__input").focus().realPress(" ");
        });
      cy.get(".custom-select__menu").first().should("exist");
      cy.get(".custom-select__menu")
        .first()
        .within(() => {
          cy.get(".custom-select__option").should("have.length", 5);
        });
    });
    it("should save the consent automation settings", () => {
      cy.getByTestId("accordion-consent-automation").click();
      cy.getByTestId("consentable-item-select")
        .first()
        .within(() => {
          cy.get(".custom-select__input").focus().realPress(" ");
        });
      cy.get(".custom-select__menu")
        .first()
        .within(() => {
          cy.get(".custom-select__option").first().click();
        });
      cy.getByTestId("save-consent-automation").click();
      cy.wait("@putConsentableItems").then((interception) => {
        cy.fixture("connectors/consentable_items.json").then((expected) => {
          // eslint-disable-next-line no-param-reassign
          expected[0].notice_id = "pri_b1244715-2adb-499f-abb2-e86b6c0040c2";
          expect(interception.request.body).to.deep.equal(expected);
        });
      });
      cy.getByTestId("toast-success-msg").should("exist");
    });
  });
});
