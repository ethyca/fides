import { stubLocations, stubPlus } from "cypress/support/stubs";

import { GLOBAL_CONSENT_CONFIG_ROUTE } from "~/features/common/nav/routes";

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
      it("does not show GPP Europe if TCF is not enabled", () => {
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
        cy.getByTestId("section-GPP U.S.").should("exist");
        cy.getByTestId("section-GPP Europe").should("not.exist");
      });
    });
  });

  describe("Publisher Settings", () => {
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
      plus_consent_settings: {
        tcf_publisher_country_code: "us",
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
      plus_consent_settings: {
        tcf_publisher_country_code: "br",
      },
    };

    it("shows the publisher settings when both config sets are present", () => {
      cy.intercept("/api/v1/config?api_set=false", { body: DEFAULT_CONFIG }).as(
        "getConfig",
      );
      cy.intercept("/api/v1/config?api_set=true", { body: API_CONFIG }).as(
        "getApiConfig",
      );
      cy.intercept("PATCH", "/api/v1/config", { body: {} }).as("patchConfig");
      cy.visit(GLOBAL_CONSENT_CONFIG_ROUTE);
      cy.wait("@getLocations");
      cy.wait("@getApiConfig");
      cy.wait("@getConfig");
      cy.getByTestId("save-btn").should("be.disabled");
      cy.getByTestId(
        "input-publisher_settings.publisher_country_code",
      ).contains("United States");
    });

    it("shows the publisher settings when only default config is present", () => {
      cy.intercept("/api/v1/config?api_set=false", { body: DEFAULT_CONFIG }).as(
        "getConfig",
      );
      cy.intercept("/api/v1/config?api_set=true", { body: {} }).as(
        "getApiConfig",
      );
      cy.intercept("PATCH", "/api/v1/config", { body: {} }).as("patchConfig");
      cy.visit(GLOBAL_CONSENT_CONFIG_ROUTE);
      cy.wait("@getLocations");
      cy.wait("@getApiConfig");
      cy.wait("@getConfig");
      cy.getByTestId("save-btn").should("be.disabled");
      cy.getByTestId(
        "input-publisher_settings.publisher_country_code",
      ).contains("Brazil");
    });

    it("shows the publisher settings when only api config is present", () => {
      cy.intercept("/api/v1/config?api_set=false", { body: {} }).as(
        "getConfig",
      );
      cy.intercept("/api/v1/config?api_set=true", { body: API_CONFIG }).as(
        "getApiConfig",
      );
      cy.intercept("PATCH", "/api/v1/config", { body: {} }).as("patchConfig");
      cy.visit(GLOBAL_CONSENT_CONFIG_ROUTE);
      cy.wait("@getLocations");
      cy.wait("@getApiConfig");
      cy.wait("@getConfig");
      cy.getByTestId("save-btn").should("be.disabled");
      cy.getByTestId(
        "input-publisher_settings.publisher_country_code",
      ).contains("United States");
    });

    it("saves new publisher settings", () => {
      cy.intercept("/api/v1/config?api_set=false", { body: DEFAULT_CONFIG }).as(
        "getConfig",
      );
      cy.intercept("/api/v1/config?api_set=true", { body: API_CONFIG }).as(
        "getApiConfig",
      );
      cy.intercept("PATCH", "/api/v1/config", { body: {} }).as("patchConfig");
      cy.visit(GLOBAL_CONSENT_CONFIG_ROUTE);
      cy.getByTestId("save-btn").should("be.disabled");
      cy.wait("@getLocations");
      cy.wait("@getApiConfig");
      cy.wait("@getConfig");
      cy.getByTestId(
        "input-publisher_settings.publisher_country_code",
      ).contains("United States");
      cy.getByTestId(
        "input-publisher_settings.publisher_country_code",
      ).antSelect("France");
      cy.getByTestId("save-btn").should("be.enabled").click();
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
            tcf_publisher_country_code: "fr",
          },
        });
      });
    });

    it("allows clearing the publisher country", () => {
      cy.intercept("/api/v1/config?api_set=false", { body: DEFAULT_CONFIG }).as(
        "getConfig",
      );
      cy.intercept("/api/v1/config?api_set=true", { body: API_CONFIG }).as(
        "getApiConfig",
      );
      cy.intercept("PATCH", "/api/v1/config", { body: {} }).as("patchConfig");
      cy.visit(GLOBAL_CONSENT_CONFIG_ROUTE);
      cy.getByTestId("save-btn").should("be.disabled");
      cy.wait("@getLocations");
      cy.wait("@getApiConfig");
      cy.wait("@getConfig");
      cy.getByTestId(
        "input-publisher_settings.publisher_country_code",
      ).contains("United States");
      cy.getByTestId(
        "input-publisher_settings.publisher_country_code",
      ).antClearSelect();
      cy.getByTestId("save-btn").should("be.enabled").click();
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
            tcf_publisher_country_code: null,
          },
        });
      });
    });
  });
});
