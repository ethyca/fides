import { stubLocations, stubPlus, stubTCFConfig } from "cypress/support/stubs";

import { GLOBAL_CONSENT_CONFIG_ROUTE } from "~/features/common/nav/routes";
import {
  FORBIDDEN_LEGITIMATE_INTEREST_PURPOSE_IDS,
  RESTRICTION_TYPE_LABELS,
} from "~/features/consent-settings/tcf/constants";
describe("Consent settings", () => {
  beforeEach(() => {
    cy.intercept("GET", "/api/v1/plus/tcf/purpose_overrides", { body: [] });
    cy.intercept("PATCH", "/api/v1/plus/tcf/purpose_overrides", { body: {} });
    stubPlus(true);
    cy.intercept("GET", "/api/v1/purposes", {
      purposes: ["test"],
      special_purposes: ["test"],
    }).as("getPurposes");
    stubLocations();
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
        enable_tcfeu_string: true,
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
        enable_tcfeu_string: false,
      },
    };

    it("reads from default config", () => {
      cy.intercept("/api/v1/config?api_set=false", { body: DEFAULT_CONFIG });
      cy.intercept("/api/v1/config?api_set=true", {});
      cy.visit(GLOBAL_CONSENT_CONFIG_ROUTE);
      cy.getByTestId("consent-configuration");
      cy.getByTestId("setting-Global Privacy Platform").within(() => {
        cy.get("p").contains("GPP status Enabled");
        cy.getByTestId("option-national").should("not.have.attr", "checked");
        cy.getByTestId("option-state").should("have.attr", "checked");
        cy.getByTestId("input-gpp.mspa_covered_transactions").should(
          "not.have.attr",
          "data-checked",
        );
        cy.getByTestId("input-gpp.mspa_service_provider_mode").should(
          "not.have.attr",
          "data-checked",
        );
        cy.getByTestId("input-gpp.mspa_opt_out_option_mode").should(
          "not.have.attr",
          "data-checked",
        );
        cy.getByTestId("input-gpp.enable_tcfeu_string").should(
          "not.have.attr",
          "data-checked",
        );
      });
    });

    it("prefers API set config when it exists", () => {
      cy.intercept("/api/v1/config?api_set=false", { body: DEFAULT_CONFIG });
      cy.intercept("/api/v1/config?api_set=true", { body: API_CONFIG });
      cy.visit(GLOBAL_CONSENT_CONFIG_ROUTE);
      cy.getByTestId("setting-Global Privacy Platform").within(() => {
        cy.get("p").contains("GPP status Enabled");
        cy.getByTestId("option-national").should("have.attr", "checked");
        cy.getByTestId("option-state").should("not.have.attr", "checked");
        cy.getByTestId("input-gpp.mspa_covered_transactions").should(
          "have.attr",
          "data-checked",
        );
        cy.getByTestId("input-gpp.mspa_service_provider_mode").should(
          "have.attr",
          "aria-checked",
          "true",
        );
        cy.getByTestId("input-gpp.mspa_opt_out_option_mode").should(
          "have.attr",
          "aria-checked",
          "false",
        );
        cy.getByTestId("input-gpp.enable_tcfeu_string").should(
          "have.attr",
          "aria-checked",
          "true",
        );
      });
    });

    it("does not show MSPA when there is no US approach", () => {
      cy.intercept("/api/v1/config?api_set=false", {
        body: { gpp: { enabled: true } },
      });
      cy.intercept("/api/v1/config?api_set=true", { body: {} });
      cy.visit(GLOBAL_CONSENT_CONFIG_ROUTE);
      cy.getByTestId("section-GPP U.S.").should("exist");
      cy.getByTestId("section-MSPA").should("not.exist");
      cy.getByTestId("option-national").click();
      cy.getByTestId("section-MSPA").should("exist");
    });

    it("disables MSPA settings conditionally", () => {
      cy.intercept("/api/v1/config?api_set=false", { body: DEFAULT_CONFIG });
      cy.intercept("/api/v1/config?api_set=true", { body: {} });
      cy.visit(GLOBAL_CONSENT_CONFIG_ROUTE);
      cy.getByTestId("setting-Global Privacy Platform").within(() => {
        // Test covered transactions checkbox behavior
        cy.getByTestId("input-gpp.mspa_covered_transactions").click(); // Check
        cy.getByTestId("input-gpp.mspa_service_provider_mode").click();
        cy.getByTestId("input-gpp.mspa_covered_transactions").click({
          force: true,
        }); // Uncheck
        cy.getByTestId("input-gpp.mspa_service_provider_mode").should(
          "not.be.checked",
        );
        cy.getByTestId("input-gpp.mspa_opt_out_option_mode").should(
          "not.be.checked",
        );
        cy.getByTestId("input-gpp.mspa_service_provider_mode").should(
          "have.attr",
          "disabled",
        );
        cy.getByTestId("input-gpp.mspa_opt_out_option_mode").should(
          "have.attr",
          "disabled",
        );

        // Re-enable covered transactions and test mode toggles
        cy.getByTestId("input-gpp.mspa_covered_transactions").click();
        cy.getByTestId("input-gpp.mspa_service_provider_mode").click();
        cy.getByTestId("input-gpp.mspa_opt_out_option_mode").should(
          "have.attr",
          "disabled",
        );
        cy.getByTestId("input-gpp.mspa_service_provider_mode").click();
        cy.getByTestId("input-gpp.mspa_opt_out_option_mode").should(
          "not.have.attr",
          "disabled",
        );
        cy.getByTestId("input-gpp.mspa_opt_out_option_mode").click();
        cy.getByTestId("input-gpp.mspa_service_provider_mode").should(
          "have.attr",
          "disabled",
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
        cy.getByTestId("input-gpp.enable_tcfeu_string").click();
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
            enable_tcfeu_string: true,
          },
          plus_consent_settings: {
            tcf_publisher_country_code: null, // Doesn't change publisher country code settings
          },
        });
      });
    });

    describe("TCF disabled", () => {
      beforeEach(() => {
        stubPlus(true, {
          core_fides_version: "1.9.6",
          fidesplus_server: "healthy",
          fidesplus_version: "1.9.6",
          system_scanner: {
            enabled: false,
            cluster_health: null,
            cluster_error: null,
          },
          dictionary: {
            enabled: false,
            service_health: null,
            service_error: null,
          },
          tcf: {
            enabled: false,
          },
          fides_cloud: {
            enabled: false,
          },
        });
        cy.intercept("/api/v1/config?api_set=false", { body: DEFAULT_CONFIG });
        cy.intercept("/api/v1/config?api_set=true", { body: {} });
        cy.visit(GLOBAL_CONSENT_CONFIG_ROUTE);
      });

      it("does not show GPP Europe if TCF is not enabled", () => {
        cy.getByTestId("section-GPP U.S.").should("exist");
        cy.getByTestId("section-GPP Europe").should("not.exist");
      });

      it("does not show Publisher Restrictions if TCF is not enabled", () => {
        cy.getByTestId(
          "setting-Transparency & Consent Framework settings",
        ).should("exist");
        cy.contains("TCF status Disabled").should("exist");
        cy.getByTestId("setting-Publisher restrictions").should("not.exist");
      });
    });
  });

  describe("Publisher restrictions", () => {
    describe("New configs", () => {
      beforeEach(() => {
        cy.intercept("/api/v1/config?api_set=false", { body: {} });
        cy.intercept("/api/v1/config?api_set=true", { body: {} });
        cy.intercept("PATCH", "/api/v1/config", { body: {} }).as("patchConfig");
        cy.intercept("GET", "/api/v1/plus/tcf/configurations", {
          body: { items: [] },
        }).as("getTCFConfigs");
        cy.intercept("POST", "/api/v1/plus/tcf/configurations", {
          body: { id: "new-config-id" },
        }).as("createConfig");
        cy.visit(GLOBAL_CONSENT_CONFIG_ROUTE);
      });
      it("displays TCF override toggle and handles state change", () => {
        cy.contains("TCF status Enabled").should("exist");
        cy.getByTestId("tcf-override-toggle").should("exist");
        cy.getByTestId("tcf-override-toggle").click();
        cy.getByTestId("tcf-override-toggle").should(
          "have.attr",
          "aria-checked",
          "true",
        );
      });

      it("allows creating a new TCF configuration", () => {
        cy.getByTestId("tcf-override-toggle").click();
        cy.getByTestId("create-config-button").click();
        cy.getByTestId("input-name").type("New Config");
        cy.getByTestId("save-config-button").click();
        cy.wait("@createConfig");
        cy.contains("Successfully created TCF configuration").should(
          "be.visible",
        );
      });
    });

    describe("TCF override enabled and config created", () => {
      beforeEach(() => {
        stubTCFConfig();
        cy.visit(GLOBAL_CONSENT_CONFIG_ROUTE);
      });

      it("shows configuration dropdown when overrides are enabled", () => {
        cy.getByTestId("tcf-config-dropdown-trigger")
          .should("exist")
          .should("have.text", "Default TCF Config");
        cy.getByTestId("tcf-config-dropdown-trigger").click();
        cy.contains("TCF configurations").should("be.visible");
        cy.getByTestId("tcf-config-item-tcf_config_1").should("exist");
        cy.getByTestId("tcf-config-item-tcf_config_2").should("exist");
        cy.getByTestId("delete-config-button")
          .should("exist")
          .should("have.length", 2);
        cy.getByTestId("create-config-button").should("exist");
        cy.getByTestId("apply-config-button").should("exist");
      });

      it("allows creating a new TCF configuration when configs exist", () => {
        cy.getByTestId("tcf-config-dropdown-trigger").click();
        cy.getByTestId("create-config-button").click();
        cy.getByTestId("input-name").should("exist");
        cy.getByTestId("save-config-button").should("exist");
      });

      it("allows changing the TCF configuration", () => {
        cy.getAllLocalStorage().then((ls) => {
          expect(ls["http://localhost:3000"]?.selectedTCFConfigId).to.not.exist;
        });
        cy.getByTestId("tcf-config-dropdown-trigger").click();
        cy.getByTestId("tcf-config-item-tcf_config_2").click();
        cy.getByTestId("apply-config-button").click();
        cy.getByTestId("tcf-config-dropdown-trigger").should(
          "have.text",
          "Strict TCF Config",
        );
        cy.getAllLocalStorage().then((ls) => {
          expect(ls["http://localhost:3000"]?.selectedTCFConfigId).to.eq(
            `"tcf_config_2"`,
          );
        });
        // check that the selected config gets remembered with new page load
        cy.visit(GLOBAL_CONSENT_CONFIG_ROUTE);
        cy.getAllLocalStorage().then((ls) => {
          expect(ls["http://localhost:3000"]?.selectedTCFConfigId).to.eq(
            `"tcf_config_2"`,
          );
        });
        cy.getByTestId("tcf-config-dropdown-trigger").should(
          "have.text",
          "Strict TCF Config",
        );
      });

      it("displays publisher restrictions table with correct data", () => {
        cy.wait("@getTcfPurposes");
        cy.getByTestId("publisher-restrictions-table").should("exist");
        cy.fixture("tcf/purposes.json").then(
          (data: {
            purposes: Record<number, any>;
            special_purposes: Record<number, any>;
          }) => {
            // shows all purposes
            Object.values(data.purposes).forEach((purpose) => {
              cy.contains(purpose.name).should("be.visible");
              cy.getByTestId(`restriction-type-cell-${purpose.id}`).should(
                "have.text",
                "none",
              );
              cy.getByTestId(`flexibility-tag-${purpose.id}`).should(
                "have.text",
                FORBIDDEN_LEGITIMATE_INTEREST_PURPOSE_IDS.includes(purpose.id)
                  ? "No"
                  : "Yes",
              );
              cy.getByTestId(`edit-restriction-btn-${purpose.id}`).should(
                "exist",
              );
            });
          },
        );
      });

      it("allows adding a new publisher restriction", () => {
        cy.intercept(
          "GET",
          "/api/v1/plus/tcf/configurations/*/publisher_restrictions?purpose_id=*",
          {
            body: { items: [] },
          },
        ).as("getTcfRestrictions");
        cy.getByTestId("edit-restriction-btn-2").click({ force: true });
        cy.getByTestId("add-restriction-button").click();
        cy.getByTestId("controlled-select-restriction_type").antSelect(
          "Require consent",
          { force: true },
        );
        cy.getByTestId("controlled-select-vendor_restriction").antSelect(
          "Restrict specific vendors",
        );
        cy.getByTestId("controlled-select-vendor_ids").should("be.visible");
        cy.getByTestId("controlled-select-vendor_restriction").antSelect(
          "Restrict all vendors",
        );
        cy.getByTestId("controlled-select-vendor_ids").should("not.be.visible");
        cy.getByTestId("save-restriction-button").click();
        cy.wait("@createRestriction");
        cy.contains("Restriction created successfully").should("be.visible");
      });

      it("allows deleting an existing restriction", () => {
        cy.getByTestId("edit-restriction-btn-2").click({ force: true });
        cy.getByTestId("delete-restriction-button").first().click();
        cy.getByTestId("continue-btn").click();
        cy.wait("@deleteRestriction");
        cy.contains("Publisher restriction deleted successfully").should(
          "be.visible",
        );
      });

      it("validates vendor ID input format", () => {
        cy.intercept(
          "GET",
          "/api/v1/plus/tcf/configurations/*/publisher_restrictions?purpose_id=*",
          {
            body: { items: [] },
          },
        ).as("getTcfRestrictions");
        cy.getByTestId("edit-restriction-btn-2").click({ force: true });
        cy.getByTestId("add-restriction-button").click();
        cy.getByTestId("controlled-select-restriction_type").antSelect(
          "Require consent",
          { force: true },
        );
        cy.getByTestId("controlled-select-vendor_restriction").antSelect(
          "Restrict specific vendors",
        );
        // a more comprehensive test of the validation exists in the unit tests, this is just a check of the UI for the error message
        cy.get("input[id='vendor_ids']").type("invalid format{enter}");
        cy.get("input[id='vendor_ids']").blur();
        cy.getByTestId("error-vendor_ids").should("be.visible");
      });

      it("displays purpose restrictions table correctly", () => {
        cy.getByTestId("edit-restriction-btn-2").click({ force: true });
        cy.getByTestId("fidesTable").should("exist");
        // mock purpose includes all restriction types, so we can check that all are present and that the Add Restriction button is disabled
        Object.values(RESTRICTION_TYPE_LABELS).forEach((label) => {
          cy.contains(label).should("exist");
        });
        cy.getByTestId("add-restriction-button")
          .should("exist")
          .should("be.disabled");
      });
    });
  });

  describe("Publisher settings", () => {
    const API_CONFIG = {
      consent: {
        override_vendor_purposes: false,
      },
      plus_consent_settings: {
        tcf_publisher_country_code: "us",
      },
    };
    const DEFAULT_CONFIG = {
      consent: {
        override_vendor_purposes: false,
      },
      plus_consent_settings: {
        tcf_publisher_country_code: "br",
      },
    };

    beforeEach(() => {
      if (Cypress.currentTest.title.includes("only api config is present")) {
        cy.intercept("/api/v1/config?api_set=false", { body: {} }).as(
          "getConfig",
        );
      } else {
        cy.intercept("/api/v1/config?api_set=false", {
          body: DEFAULT_CONFIG,
        }).as("getConfig");
      }
      if (
        Cypress.currentTest.title.includes("only default config is present")
      ) {
        cy.intercept("/api/v1/config?api_set=true", { body: {} }).as(
          "getApiConfig",
        );
      } else {
        cy.intercept("/api/v1/config?api_set=true", { body: API_CONFIG }).as(
          "getApiConfig",
        );
      }
      cy.intercept("PATCH", "/api/v1/config", { body: {} }).as("patchConfig");
      cy.visit(GLOBAL_CONSENT_CONFIG_ROUTE);
      cy.getByTestId("save-btn").should("be.disabled");
      cy.wait("@getLocations");
      cy.wait("@getApiConfig");
      cy.wait("@getConfig");
    });

    it("shows the publisher settings when both config sets are present", () => {
      cy.getByTestId(
        "input-publisher_settings.publisher_country_code",
      ).contains("United States");
    });

    it("shows the publisher settings when only default config is present", () => {
      cy.getByTestId(
        "input-publisher_settings.publisher_country_code",
      ).contains("Brazil");
    });

    it("shows the publisher settings when only api config is present", () => {
      cy.getByTestId(
        "input-publisher_settings.publisher_country_code",
      ).contains("United States");
    });

    it("saves publisher country code", () => {
      cy.getByTestId(
        "input-publisher_settings.publisher_country_code",
      ).contains("United States");
      cy.getByTestId(
        "input-publisher_settings.publisher_country_code",
      ).antSelect("France");
      cy.getByTestId("save-btn").should("be.enabled").click();
      cy.wait("@patchConfig").then((interception) => {
        const { body } = interception.request;
        expect(body.plus_consent_settings).to.eql({
          tcf_publisher_country_code: "fr",
        });
      });
    });

    it("allows clearing the publisher country code", () => {
      cy.getByTestId(
        "input-publisher_settings.publisher_country_code",
      ).contains("United States");
      cy.getByTestId(
        "input-publisher_settings.publisher_country_code",
      ).antClearSelect();
      cy.getByTestId("save-btn").should("be.enabled").click();
      cy.wait("@patchConfig").then((interception) => {
        const { body } = interception.request;
        expect(body.plus_consent_settings).to.eql({
          tcf_publisher_country_code: null,
        });
      });
    });
  });
});
