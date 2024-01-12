import { stubPlus } from "cypress/support/stubs";

import { GLOBAL_CONSENT_CONFIG_ROUTE } from "~/features/common/nav/v2/routes";

describe("Consent settings", () => {
  beforeEach(() => {
    cy.intercept("GET", "/api/v1/plus/tcf/purpose_overrides", { body: [] });
    cy.intercept("PATCH", "/api/v1/plus/tcf/purpose_overrides", { body: {} });
    stubPlus(true);
    cy.login();
  });

  describe("gpp settings", () => {
    const API_CONFIG = {
      consent: {
        override_vendor_purposes: false,
      },
      gpp: {
        us_approach: "national",
        mspa_service_provider_mode: true,
        mspa_opt_out_option_mode: false,
        mspa_covered_transactions: true,
      },
    };
    const DEFAULT_CONFIG = {
      consent: {
        override_vendor_purposes: false,
      },
      gpp: {
        enabled: true,
        us_approach: "state",
        mspa_service_provider_mode: false,
        mspa_opt_out_option_mode: false,
        mspa_covered_transactions: false,
      },
    };

    it("reads from default config", () => {
      cy.intercept("/api/v1/config?api_set=false", { body: DEFAULT_CONFIG });
      cy.intercept("/api/v1/config?api_set=true", {});
      cy.visit(GLOBAL_CONSENT_CONFIG_ROUTE);
      cy.getByTestId("consent-configuration");
      cy.getByTestId("setting-Global Privacy Platform").within(() => {
        cy.get("p").contains("GPP status Enabled");
        cy.getByTestId("option-national").should(
          "not.have.attr",
          "data-checked"
        );
        cy.getByTestId("option-state").should("have.attr", "data-checked");
        cy.getByTestId("input-gpp.mspa_covered_transactions").should(
          "not.have.attr",
          "data-checked"
        );
        cy.getByTestId("input-gpp.mspa_service_provider_mode").should(
          "not.have.attr",
          "data-checked"
        );
        cy.getByTestId("input-gpp.mspa_opt_out_option_mode").should(
          "not.have.attr",
          "data-checked"
        );
      });
    });

    it("prefers API set config when it exists", () => {
      cy.intercept("/api/v1/config?api_set=false", { body: DEFAULT_CONFIG });
      cy.intercept("/api/v1/config?api_set=true", { body: API_CONFIG });
      cy.visit(GLOBAL_CONSENT_CONFIG_ROUTE);
      cy.getByTestId("consent-configuration");
      cy.getByTestId("setting-Global Privacy Platform").within(() => {
        cy.get("p").contains("GPP status Enabled");
        cy.getByTestId("option-national").should("have.attr", "data-checked");
        cy.getByTestId("option-state").should("not.have.attr", "data-checked");
        cy.getByTestId("input-gpp.mspa_covered_transactions").should(
          "have.attr",
          "data-checked"
        );
        cy.getByTestId("input-gpp.mspa_service_provider_mode").should(
          "have.attr",
          "data-checked"
        );
        cy.getByTestId("input-gpp.mspa_opt_out_option_mode").should(
          "not.have.attr",
          "data-checked"
        );
      });
    });

    it("disables MSPA settings conditionally", () => {
      cy.intercept("/api/v1/config?api_set=false", { body: DEFAULT_CONFIG });
      cy.intercept("/api/v1/config?api_set=true", { body: {} });
      cy.visit(GLOBAL_CONSENT_CONFIG_ROUTE);
      cy.getByTestId("setting-Global Privacy Platform").within(() => {
        cy.getByTestId("input-gpp.mspa_service_provider_mode").click();
        cy.getByTestId("input-gpp.mspa_opt_out_option_mode").should(
          "have.attr",
          "data-disabled"
        );
        cy.getByTestId("input-gpp.mspa_service_provider_mode").click();
        cy.getByTestId("input-gpp.mspa_opt_out_option_mode").should(
          "not.have.attr",
          "data-disabled"
        );
        cy.getByTestId("input-gpp.mspa_opt_out_option_mode").click();
        cy.getByTestId("input-gpp.mspa_service_provider_mode").should(
          "have.attr",
          "data-disabled"
        );
      });
    });

    it("saves new gpp settings", () => {
      cy.intercept("/api/v1/config?api_set=false", { body: DEFAULT_CONFIG });
      cy.intercept("/api/v1/config?api_set=true", { body: {} });
      cy.intercept("PATCH", "/api/v1/config", { body: {} }).as("patchConfig");
      cy.visit(GLOBAL_CONSENT_CONFIG_ROUTE);
      cy.getByTestId("save-btn").should("be.disabled");
      cy.getByTestId("setting-Global Privacy Platform").within(() => {
        // Reverse everything
        cy.getByTestId("option-national").click();
        cy.getByTestId("input-gpp.mspa_covered_transactions").click();
        cy.getByTestId("input-gpp.mspa_service_provider_mode").click();
      });
      cy.getByTestId("save-btn").click();
      cy.wait("@patchConfig").then((interception) => {
        const { body } = interception.request;
        expect(body).to.eql({
          gpp: {
            us_approach: "national",
            mspa_service_provider_mode: true,
            mspa_opt_out_option_mode: false,
            mspa_covered_transactions: true,
          },
        });
      });
    });
  });
});
