import {
  stubDatasetCrud,
  stubDisabledIntegrationSystemCrud,
  stubPlus,
  stubPrivacyNoticesCrud,
  stubSystemCrud,
  stubSystemIntegrations,
  stubTaxonomyEntities,
} from "cypress/support/stubs";

import { EDIT_SYSTEM_ROUTE, SYSTEM_ROUTE } from "~/features/common/nav/routes";

describe("System integrations", () => {
  beforeEach(() => {
    cy.login();
    stubPlus(false);
    stubSystemIntegrations();
    stubSystemCrud();
    stubDatasetCrud();
    stubTaxonomyEntities();
    cy.visit(SYSTEM_ROUTE);
  });

  it("should render the integration configuration panel when navigating to integrations tab", () => {
    cy.getByTestId("system-fidesctl_system").within(() => {
      cy.getByTestId("edit-btn").click();
    });
    cy.getAntTab("Integrations").click({ force: true });
    cy.get("#rc-tabs-0-panel-integrations").should("be.visible");
  });

  describe("Integration search", () => {
    beforeEach(() => {
      cy.getByTestId("system-fidesctl_system").within(() => {
        cy.getByTestId("edit-btn").click();
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
      cy.getByTestId("system-fidesctl_system").within(() => {
        cy.getByTestId("edit-btn").click();
      });
      cy.getAntTab("Integrations").click({ force: true });
      cy.getByTestId("select-dropdown-btn").click();

      cy.getByTestId("input-search-integrations").type("PostgreSQL");
      cy.getByTestId("select-dropdown-list")
        .contains('[role="menuitem"]', "PostgreSQL")
        .click();
    });

    it("should not Request types (enabled-actions) field", () => {
      cy.getByTestId("controlled-select-enabled_actions").should("not.exist");
    });
  });

  describe("Loading existing integration", () => {
    beforeEach(() => {
      cy.login();
      stubPlus(false);
      stubSystemIntegrations();
      stubSystemCrud();
      stubDatasetCrud();
      stubTaxonomyEntities();
      stubPrivacyNoticesCrud();
      stubDisabledIntegrationSystemCrud();

      cy.visit(EDIT_SYSTEM_ROUTE.replace("[id]", "disabled_postgres_system"));
      cy.getAntTab("Integrations").click({ force: true });
    });

    it("should format dataset references as objects", () => {
      cy.wait("@getPostgresConnectorSecret");
      cy.getByTestId("input-secrets.dataset_reference").type(
        "test_dataset.test_collection.test_field",
      );
      cy.getByTestId("save-integration-btn").click();
      cy.wait("@patchConnectionSecret").then(({ request }) => {
        expect(request.body.dataset_reference).to.deep.equal({
          dataset: "test_dataset",
          field: "test_collection.test_field",
          direction: "from",
        });
      });
    });

    it("when saving the form it shouldn't re-enable the integration", () => {
      cy.getByTestId("save-integration-btn").click();
      cy.wait("@patchConnection").then(({ request }) => {
        expect(request.body[0]).to.deep.equal({
          access: "write",
          connection_type: "postgres",
          description: "",
          key: "asdasd_postgres",
          enabled_actions: [],
        });
        expect(request.body[0].disabled).to.be.undefined;
      });
    });
  });
});
