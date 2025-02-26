import {
  stubPlus,
  stubSystemCrud,
  stubSystemVendors,
  stubTaxonomyEntities,
  stubVendorList,
} from "cypress/support/stubs";

import {
  ADD_MULTIPLE_VENDORS_ROUTE,
  CONFIGURE_CONSENT_ROUTE,
} from "~/features/common/nav/routes";
import { RoleRegistryEnum } from "~/types/api";

describe("Consent configuration", () => {
  beforeEach(() => {
    cy.login();
  });

  describe("permissions", () => {
    it("cannot access consent config page without plus", () => {
      stubPlus(false);
      cy.visit(CONFIGURE_CONSENT_ROUTE);
      cy.getByTestId("home-content");
    });

    it("cannot access consent config page without privacy notice permission", () => {
      stubPlus(true);
      cy.assumeRole(RoleRegistryEnum.APPROVER);
      cy.visit(CONFIGURE_CONSENT_ROUTE);
      cy.getByTestId("home-content");
    });
  });

  describe("empty state", () => {
    it("can render an empty state", () => {
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
          enabled: true,
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
      cy.intercept("GET", "/api/v1/plus/dictionary/system-vendors", {
        body: [],
      }).as("getEmptySystems");
      cy.intercept("GET", "/api/v1/plus/dictionary/system?size*", {
        fixture: "dictionary-entries.json",
      }).as("getDict");
      cy.visit(ADD_MULTIPLE_VENDORS_ROUTE);
      cy.getByTestId("no-results-notice");
    });
  });

  describe.skip("adding a vendor", () => {
    beforeEach(() => {
      stubSystemCrud();
      stubTaxonomyEntities();
      stubVendorList();
      cy.intercept("GET", "/api/v1/system", {
        fixture: "systems/systems.json",
      }).as("getSystems");
      cy.intercept("GET", "/api/v1/purposes", {
        purposes: ["test"],
        special_purposes: ["test"],
      }).as("getPurposes");
    });

    describe("without the dictionary", () => {
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
        cy.visit(CONFIGURE_CONSENT_ROUTE);
      });

      it("can add a vendor from the modal without the dictionary", () => {
        cy.getByTestId("add-vendor-btn").click();
        cy.getByTestId("input-name").type("test vendor");
        cy.selectOption(
          "input-privacy_declarations.0.consent_use",
          "analytics",
        );
        cy.getByTestId("input-privacy_declarations.0.cookieNames")
          .find(".custom-creatable-select__input-container")
          .type("test{enter}cookie{enter}");
        cy.getByTestId("save-btn").click();
        cy.wait("@postSystem").then((interception) => {
          const { body } = interception.request;
          expect(body).to.eql({
            name: "test vendor",
            fides_key: "test_vendor",
            system_type: "",
            privacy_declarations: [
              {
                name: "",
                data_use: "analytics",
                data_categories: ["user"],
                cookies: [
                  {
                    name: "test",
                    path: "/",
                  },
                  {
                    name: "cookie",
                    path: "/",
                  },
                ],
              },
            ],
          });
        });
      });

      it("can manually add more data uses", () => {
        cy.getByTestId("add-vendor-btn").click();
        cy.getByTestId("add-data-use-btn").should("be.disabled");
        cy.getByTestId("input-name").type("test vendor");
        cy.selectOption(
          "input-privacy_declarations.0.consent_use",
          "analytics",
        );
        cy.getByTestId("input-privacy_declarations.0.cookieNames")
          .find(".custom-creatable-select__input-container")
          .type("one{enter}");

        // Add another use
        cy.getByTestId("add-data-use-btn").click();
        // TODO: this select fails when trying to select "essential" or "functional", but accepts "analytics" or "marketing"
        cy.selectOption(
          "input-privacy_declarations.1.consent_use",
          "marketing",
        );
        cy.getByTestId("input-privacy_declarations.1.cookieNames")
          .find(".custom-creatable-select__input-container")
          .type("two{enter}");
        cy.getByTestId("save-btn").click();
        cy.wait("@postSystem").then((interception) => {
          const { body } = interception.request;
          expect(body.privacy_declarations).to.eql([
            {
              name: "",
              data_use: "analytics",
              data_categories: ["user"],
              cookies: [
                {
                  name: "one",
                  path: "/",
                },
              ],
            },
            {
              name: "",
              data_use: "marketing.advertising.first_party.targeted",
              data_categories: ["user"],
              cookies: [
                {
                  name: "two",
                  path: "/",
                },
              ],
            },
            {
              name: "",
              data_use: "marketing.advertising.third_party.targeted",
              data_categories: ["user"],
              cookies: [
                {
                  name: "two",
                  path: "/",
                },
              ],
            },
          ]);
        });
      });
    });

    describe("with the dictionary", () => {
      beforeEach(() => {
        stubPlus(
          true,

          {
            core_fides_version: "1.9.6",
            fidesplus_server: "healthy",
            fidesplus_version: "1.9.6",
            system_scanner: {
              enabled: false,
              cluster_health: null,
              cluster_error: null,
            },
            dictionary: {
              enabled: true,
              service_health: null,
              service_error: null,
            },
            tcf: {
              enabled: false,
            },
            fides_cloud: {
              enabled: false,
            },
          },
        );
        stubSystemVendors();
      });

      it("redirects to 'add multiple vendors' page when 'Add vendors' is clicked", () => {
        cy.visit(CONFIGURE_CONSENT_ROUTE);
        cy.getByTestId("add-vendor-btn").click();
        cy.url().should("include", "/consent/configure/add-vendors");
      });

      it("can add a vendor with dictionary suggestions from the modal", () => {
        cy.visit(ADD_MULTIPLE_VENDORS_ROUTE);
        cy.getByTestId("add-vendor-btn").click();
        cy.getByTestId("input-name").type("Aniview LTD{enter}");
        cy.wait("@getDictionaryDeclarations");
        cy.getByTestId(
          "controlled-select-privacy_declarations.0.consent_use",
        ).contains("Marketing");
        cy.getByTestId(
          "controlled-select-privacy_declarations.0.data_use",
        ).contains("Profiling for Advertising");
        ["av_*", "aniC", "2_C_*"].forEach((cookieName) => {
          cy.getByTestId("input-privacy_declarations.0.cookieNames").contains(
            cookieName,
          );
        });

        // Also check one that shouldn't have any cookies
        cy.getByTestId(
          "controlled-select-privacy_declarations.1.data_use",
        ).contains("Analytics for Insights");
        cy.getByTestId("input-privacy_declarations.1.cookieNames").contains(
          "Select...",
        );
        // There should be 13 declarations (but start from 0, so 12)
        cy.getByTestId("input-privacy_declarations.12.cookieNames");
        cy.getByTestId("save-btn").click();
        cy.wait("@postSystem").then((interception) => {
          const { body } = interception.request;
          expect(body.name).to.eql("Aniview LTD");
          expect(body.privacy_declarations).to.eql([
            {
              name: "",
              data_use: "marketing.advertising.profiling",
              data_categories: [
                "user.device.ip_address",
                "user.device",
                "user.sensor",
                "user.user_sensor",
                "user.telemetry",
                "user.device.cookie_id",
                "user.device.device_id",
                "user.device.cookie",
                "user.behavior.purchase_history",
                "user.behavior",
                "user.behavior.browsing_history",
                "user.behavior.media_consumption",
                "user.behavior.search_history",
                "user.social",
                "user.location.imprecise",
              ],
              cookies: [
                {
                  name: "2_C_*",
                  domain: "*.aniview.com",
                  path: null,
                },
                {
                  name: "aniC",
                  domain: "*.aniview.com",
                  path: null,
                },
                {
                  name: "av_*",
                  domain: "*",
                  path: null,
                },
              ],
            },
            {
              name: "",
              data_use: "analytics.reporting.campaign_insights",
              data_categories: [
                "user.device.ip_address",
                "user.device",
                "user.sensor",
                "user.user_sensor",
                "user.telemetry",
                "user.device.cookie_id",
                "user.device.device_id",
                "user.device.cookie",
                "user.behavior.purchase_history",
                "user.behavior",
                "user.behavior.browsing_history",
                "user.behavior.media_consumption",
                "user.behavior.search_history",
                "user.social",
                "user.location.imprecise",
              ],
              cookies: [],
            },
            {
              name: "",
              data_use: "analytics.reporting.ad_performance",
              data_categories: [
                "user.device.ip_address",
                "user.device",
                "user.sensor",
                "user.user_sensor",
                "user.telemetry",
                "user.device.cookie_id",
                "user.device.device_id",
                "user.device.cookie",
                "user.behavior.purchase_history",
                "user.behavior",
                "user.behavior.browsing_history",
                "user.behavior.media_consumption",
                "user.behavior.search_history",
                "user.social",
                "user.location.imprecise",
              ],
              cookies: [
                {
                  name: "2_C_*",
                  domain: "*.aniview.com",
                  path: null,
                },
                {
                  name: "aniC",
                  domain: "*.aniview.com",
                  path: null,
                },
                {
                  name: "av_*",
                  domain: "*",
                  path: null,
                },
              ],
            },
            {
              name: "",
              data_use: "marketing.advertising.first_party.targeted",
              data_categories: [
                "user.device.ip_address",
                "user.device",
                "user.sensor",
                "user.user_sensor",
                "user.telemetry",
                "user.device.cookie_id",
                "user.device.device_id",
                "user.device.cookie",
                "user.behavior.purchase_history",
                "user.behavior",
                "user.behavior.browsing_history",
                "user.behavior.media_consumption",
                "user.behavior.search_history",
                "user.social",
                "user.location.imprecise",
              ],
              cookies: [
                {
                  name: "2_C_*",
                  domain: "*.aniview.com",
                  path: null,
                },
                {
                  name: "aniC",
                  domain: "*.aniview.com",
                  path: null,
                },
                {
                  name: "av_*",
                  domain: "*",
                  path: null,
                },
              ],
            },
            {
              name: "",
              data_use: "marketing.advertising.third_party.targeted",
              data_categories: [
                "user.device.ip_address",
                "user.device",
                "user.sensor",
                "user.user_sensor",
                "user.telemetry",
                "user.device.cookie_id",
                "user.device.device_id",
                "user.device.cookie",
                "user.behavior.purchase_history",
                "user.behavior",
                "user.behavior.browsing_history",
                "user.behavior.media_consumption",
                "user.behavior.search_history",
                "user.social",
                "user.location.imprecise",
              ],
              cookies: [
                {
                  name: "2_C_*",
                  domain: "*.aniview.com",
                  path: null,
                },
                {
                  name: "aniC",
                  domain: "*.aniview.com",
                  path: null,
                },
                {
                  name: "av_*",
                  domain: "*",
                  path: null,
                },
              ],
            },
            {
              name: "",
              data_use: "functional.storage",
              data_categories: [
                "user.device.ip_address",
                "user.device",
                "user.sensor",
                "user.user_sensor",
                "user.telemetry",
                "user.device.cookie_id",
                "user.device.device_id",
                "user.device.cookie",
                "user.behavior.purchase_history",
                "user.behavior",
                "user.behavior.browsing_history",
                "user.behavior.media_consumption",
                "user.behavior.search_history",
                "user.social",
                "user.location.imprecise",
              ],
              cookies: [
                {
                  name: "2_C_*",
                  domain: "*.aniview.com",
                  path: null,
                },
                {
                  name: "aniC",
                  domain: "*.aniview.com",
                  path: null,
                },
                {
                  name: "av_*",
                  domain: "*",
                  path: null,
                },
              ],
            },
            {
              name: "",
              data_use: "essential.fraud_detection",
              data_categories: [
                "user.device.ip_address",
                "user.device",
                "user.sensor",
                "user.user_sensor",
                "user.telemetry",
                "user.device.cookie_id",
                "user.device.device_id",
                "user.device.cookie",
                "user.behavior.purchase_history",
                "user.behavior",
                "user.behavior.browsing_history",
                "user.behavior.media_consumption",
                "user.behavior.search_history",
                "user.social",
                "user.location.imprecise",
              ],
              cookies: [],
            },
            {
              name: "",
              data_use: "marketing.advertising.negative_targeting",
              data_categories: [
                "user.device.ip_address",
                "user.device",
                "user.sensor",
                "user.user_sensor",
                "user.telemetry",
                "user.device.cookie_id",
                "user.device.device_id",
                "user.device.cookie",
                "user.behavior.purchase_history",
                "user.behavior",
                "user.behavior.browsing_history",
                "user.behavior.media_consumption",
                "user.behavior.search_history",
                "user.social",
                "user.location.imprecise",
              ],
              cookies: [
                {
                  name: "2_C_*",
                  domain: "*.aniview.com",
                  path: null,
                },
                {
                  name: "aniC",
                  domain: "*.aniview.com",
                  path: null,
                },
                {
                  name: "av_*",
                  domain: "*",
                  path: null,
                },
              ],
            },
            {
              name: "",
              data_use: "marketing.advertising.frequency_capping",
              data_categories: [
                "user.device.ip_address",
                "user.device",
                "user.sensor",
                "user.user_sensor",
                "user.telemetry",
                "user.device.cookie_id",
                "user.device.device_id",
                "user.device.cookie",
                "user.behavior.purchase_history",
                "user.behavior",
                "user.behavior.browsing_history",
                "user.behavior.media_consumption",
                "user.behavior.search_history",
                "user.social",
                "user.location.imprecise",
              ],
              cookies: [
                {
                  name: "2_C_*",
                  domain: "*.aniview.com",
                  path: null,
                },
                {
                  name: "aniC",
                  domain: "*.aniview.com",
                  path: null,
                },
                {
                  name: "av_*",
                  domain: "*",
                  path: null,
                },
              ],
            },
            {
              name: "",
              data_use: "analytics.reporting.content_performance",
              data_categories: [
                "user.device.ip_address",
                "user.device",
                "user.sensor",
                "user.user_sensor",
                "user.telemetry",
                "user.device.cookie_id",
                "user.device.device_id",
                "user.device.cookie",
                "user.behavior.purchase_history",
                "user.behavior",
                "user.behavior.browsing_history",
                "user.behavior.media_consumption",
                "user.behavior.search_history",
                "user.social",
                "user.location.imprecise",
              ],
              cookies: [],
            },
            {
              name: "",
              data_use: "marketing.advertising.first_party.contextual",
              data_categories: [
                "user.device.ip_address",
                "user.device",
                "user.sensor",
                "user.user_sensor",
                "user.telemetry",
                "user.device.cookie_id",
                "user.device.device_id",
                "user.device.cookie",
                "user.behavior.purchase_history",
                "user.behavior",
                "user.behavior.browsing_history",
                "user.behavior.media_consumption",
                "user.behavior.search_history",
                "user.social",
                "user.location.imprecise",
              ],
              cookies: [
                {
                  name: "2_C_*",
                  domain: "*.aniview.com",
                  path: null,
                },
                {
                  name: "aniC",
                  domain: "*.aniview.com",
                  path: null,
                },
                {
                  name: "av_*",
                  domain: "*",
                  path: null,
                },
              ],
            },
            {
              name: "",
              data_use: "functional.service.improve",
              data_categories: [
                "user.device.ip_address",
                "user.device",
                "user.sensor",
                "user.user_sensor",
                "user.telemetry",
                "user.device.cookie_id",
                "user.device.device_id",
                "user.device.cookie",
                "user.behavior.purchase_history",
                "user.behavior",
                "user.behavior.browsing_history",
                "user.behavior.media_consumption",
                "user.behavior.search_history",
                "user.social",
                "user.location.imprecise",
              ],
              cookies: [],
            },
            {
              name: "",
              data_use: "essential.service.security",
              data_categories: [
                "user.device.ip_address",
                "user.device",
                "user.sensor",
                "user.user_sensor",
                "user.telemetry",
                "user.device.cookie_id",
                "user.device.device_id",
                "user.device.cookie",
                "user.behavior.purchase_history",
                "user.behavior",
                "user.behavior.browsing_history",
                "user.behavior.media_consumption",
                "user.behavior.search_history",
                "user.social",
                "user.location.imprecise",
              ],
              cookies: [],
            },
          ]);
        });
      });

      it("can create a vendor that is not in the dictionary", () => {
        cy.visit(ADD_MULTIPLE_VENDORS_ROUTE);
        cy.getByTestId("add-vendor-btn").click();
        cy.getByTestId("input-name").type("custom vendor{enter}");
        cy.selectOption(
          "input-privacy_declarations.0.consent_use",
          "analytics",
        );
        cy.getByTestId("input-privacy_declarations.0.cookieNames")
          .find(".custom-creatable-select__input-container")
          .type("test{enter}");
        cy.getByTestId("save-btn").click();
        cy.wait("@postSystem").then((interception) => {
          const { body } = interception.request;
          expect(body).to.eql({
            name: "custom vendor",
            fides_key: "custom_vendor",
            system_type: "",
            privacy_declarations: [
              {
                name: "",
                data_use: "analytics",
                data_categories: ["user"],
                cookies: [
                  {
                    name: "test",
                    path: "/",
                  },
                ],
              },
            ],
          });
        });
      });
    });
  });
});
