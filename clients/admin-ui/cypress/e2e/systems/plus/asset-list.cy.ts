import {
  stubDatasetCrud,
  stubPlus,
  stubSystemAssets,
  stubSystemCrud,
  stubSystemIntegrations,
  stubSystemVendors,
  stubTaxonomyEntities,
} from "cypress/support/stubs";

import { SYSTEM_ROUTE } from "~/features/common/nav/routes";

describe("Plus Asset List", () => {
  beforeEach(() => {
    cy.login();
    stubSystemCrud();
    stubTaxonomyEntities();
    stubPlus(true);
    cy.intercept("GET", "/api/v1/system", {
      fixture: "systems/systems.json",
    }).as("getSystems");
    cy.intercept({ method: "POST", url: "/api/v1/system*" }).as(
      "postDictSystem",
    );
    cy.intercept("/api/v1/config?api_set=false", {});
    stubDatasetCrud();
    stubSystemIntegrations();
    stubSystemVendors();
    stubSystemAssets();
    cy.visit(`${SYSTEM_ROUTE}/configure/demo_analytics_system`);
    cy.wait("@getSystem");
  });

  it("shows an empty state", () => {
    cy.intercept("GET", "/api/v1/plus/system-assets/*", {
      fixture: "empty-pagination",
    }).as("getEmptySystemAssets");
    cy.getAntTab("Assets").click({ force: true });
    cy.wait("@getEmptySystemAssets");
    cy.getByTestId("empty-state").should("exist");
  });

  it("lists assets in the system assets tab", () => {
    cy.getAntTab("Assets").click({ force: true });
    cy.wait("@getSystemAssets");
    cy.getByTestId("row-0-col-name").should("contain", "ar_debug");
    cy.getByTestId("row-0-col-locations").should("contain", "United States");
    cy.getByTestId("row-0-col-data_uses").should("contain", "Essential");
  });

  describe("asset operations", () => {
    beforeEach(() => {
      cy.getAntTab("Assets").click({ force: true });
      cy.wait("@getSystemAssets");
    });

    it("can add a new asset", () => {
      cy.getByTestId("add-asset-btn").click();
      cy.getByTestId("add-modal-content").within(() => {
        cy.getByTestId("input-name").type("test_cookie");
        cy.getByTestId("input-domain").type("example.com");
        cy.getByTestId("controlled-select-asset_type").antSelect("Cookie");
        cy.getByTestId("controlled-select-data_uses").antSelect("analytics");
        cy.getByTestId("input-duration").type("A couple seconds");
        cy.getByTestId("save-btn").click({ force: true });
      });
      cy.wait("@addSystemAsset");
    });

    it("can edit an existing asset", () => {
      cy.getByTestId("row-0-col-actions").within(() => {
        cy.getByTestId("edit-btn").click();
      });
      cy.getByTestId("add-modal-content").within(() => {
        cy.getByTestId("input-name")
          .should("have.value", "ar_debug")
          .should("be.disabled");
        cy.getByTestId("controlled-select-asset_type")
          .should("contain", "Cookie")
          .should("have.class", "ant-select-disabled");
        cy.getByTestId("controlled-select-data_uses").should(
          "contain",
          "essential",
        );
        cy.getByTestId("controlled-select-data_uses").antSelect(0);
        cy.getByTestId("input-domain")
          .should("have.value", ".doubleclick.net")
          .should("be.disabled");
        cy.getByTestId("input-description")
          .should("have.value", "This is a test description")
          .clear({ force: true })
          .type("Updating the description");

        cy.getByTestId("save-btn").click();
      });
      cy.wait("@updateSystemAssets").then((interception) => {
        expect(interception.request.body[0].data_uses).to.eql([
          "essential",
          "analytics",
        ]);
      });
    });

    it("can delete an asset", () => {
      cy.getByTestId("row-0-col-actions").within(() => {
        cy.getByTestId("remove-btn").click();
      });

      cy.getByTestId("confirmation-modal").should("exist");
      cy.getByTestId("continue-btn").click({ force: true });
      cy.wait("@deleteSystemAssets");
    });

    it("validates base URL for non-cookie assets", () => {
      cy.getByTestId("add-asset-btn").click();
      cy.getByTestId("add-modal-content").within(() => {
        cy.getByTestId("input-name").type("test_tag");
        cy.getByTestId("input-domain").type("example.com");
        cy.getByTestId("controlled-select-asset_type").antSelect(
          "Javascript tag",
        );
        cy.getByTestId("controlled-select-data_uses").antSelect("analytics");
        cy.getByTestId("controlled-select-data_uses").within(() => {
          // force select menu to close so it doesn't cover the input
          cy.get("input").focus().blur();
        });
        // blur the input without entering anything to trigger the error
        cy.getByTestId("input-base_url").clear().blur();
        cy.getByTestId("save-btn").should("be.disabled");
        cy.getByTestId("error-base_url").should(
          "contain",
          "Base URL is required",
        );
        cy.getByTestId("input-base_url")
          .type("https://example.com/script.js")
          .blur();
      });
      cy.getByTestId("add-modal-content").within(() => {
        cy.getByTestId("save-btn").click();
      });
      cy.wait("@addSystemAsset");
    });

    it("can bulk delete assets", () => {
      cy.getByTestId("row-0-col-select").click();
      cy.getByTestId("row-1-col-select").click();
      cy.getByTestId("bulk-delete-btn").click();
      cy.getByTestId("confirmation-modal").should("exist");
      cy.getByTestId("continue-btn").click();
      cy.wait("@deleteSystemAssets");
    });
  });
});
