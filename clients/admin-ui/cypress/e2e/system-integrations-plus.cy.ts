import {
  stubDatasetCrud,
  stubPlus,
  stubSystemCrud,
  stubSystemIntegrations,
  stubTaxonomyEntities,
} from "cypress/support/stubs";

import { SYSTEM_ROUTE } from "~/features/common/nav/routes";

describe("System integrations", () => {
  beforeEach(() => {
    cy.login();
    stubPlus(true);
    stubSystemIntegrations();
    stubSystemCrud();
    stubTaxonomyEntities();
    stubDatasetCrud();
    cy.visit(SYSTEM_ROUTE);
  });

  it("should render the integration configuration panel when navigating to integrations tab", () => {
    cy.getAntTableRow("fidesctl_system").within(() => {
      cy.getByTestId("system-link-fidesctl_system").click();
    });
    cy.wait("@getDict");
    cy.getAntTab("Integrations").click({ force: true });
    cy.get("#rc-tabs-0-panel-integrations").should("be.visible");
  });

  describe("Integration search", () => {
    beforeEach(() => {
      cy.getAntTableRow("fidesctl_system").within(() => {
        cy.getByTestId("system-link-fidesctl_system").click();
      });
      cy.getAntTab("Integrations").click({ force: true });
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
      cy.getByTestId("system-link-fidesctl_system").click();
      cy.getAntTab("Integrations").click({ force: true });
      cy.getByTestId("select-dropdown-btn").click();

      cy.getByTestId("input-search-integrations").type("PostgreSQL");
      cy.getByTestId("select-dropdown-list")
        .contains('[role="menuitem"]', /^PostgreSQL$/)
        .click();
    });

    // Verify Postgres shows access and erasure by default
    it("should display Request types (enabled-actions) field", () => {
      cy.getByTestId("controlled-select-enabled_actions").should("exist");
      cy.getByTestId("controlled-select-enabled_actions").within(() => {
        cy.contains("Access");
        cy.contains("Erasure");
        cy.contains("Consent").should("not.exist");
      });
    });
  });

  describe("Bidirectional consent", () => {
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
      cy.getByTestId("system-link-fidesctl_system").click();
      cy.getAntTab("Integrations").click({ force: true });
    });
    it("should render the Bidirectional consent accordion panel", () => {
      cy.getByTestId("accordion-consent-automation").click();
      cy.getByTestId("accordion-panel-consent-automation").should("exist");
      cy.getByTestId("consentable-item-label").should("have.length", 5);
      cy.getByTestId("consentable-item-label-child").should("have.length", 6);
      cy.getByTestId("consentable-item-select").should("have.length", 11);
    });
    it("should save the Bidirectional consent settings", () => {
      cy.getByTestId("accordion-consent-automation").click();
      cy.getByTestId("consentable-item-select").antSelect(0);
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
