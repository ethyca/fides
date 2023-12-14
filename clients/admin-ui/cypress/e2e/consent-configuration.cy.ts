import {
  stubPlus,
  stubSystemCrud,
  stubTaxonomyEntities,
  stubVendorList,
} from "cypress/support/stubs";

import { CONFIGURE_CONSENT_ROUTE } from "~/features/common/nav/v2/routes";
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
      cy.intercept("GET", "/api/v1/system", {
        body: [],
      }).as("getEmptySystems");
      cy.visit(CONFIGURE_CONSENT_ROUTE);
      cy.getByTestId("empty-state");
      cy.get("body").click(0, 0);
    });
  });

  describe("with existing systems", () => {
    beforeEach(() => {
      stubSystemCrud();
      stubTaxonomyEntities();
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
        }
      );
      cy.intercept("GET", "/api/v1/system", {
        fixture: "systems/systems.json",
      }).as("getSystems");
      cy.visit(CONFIGURE_CONSENT_ROUTE);
    });

    it("can render existing systems and cookies", () => {
      // One row per system and one subrow per cookie
      cy.getByTestId("grouped-row-demo_analytics_system");
      cy.getByTestId("grouped-row-demo_marketing_system");
      cy.getByTestId("grouped-row-fidesctl_system");

      // One subrow per cookie. Should have corresponding data use
      cy.getByTestId("subrow-cell_0_Cookie name").contains("N/A");
      cy.getByTestId("subrow-cell_0_Data use").contains("N/A");
      cy.getByTestId("subrow-cell_1_Cookie name").contains("_ga");
      cy.getByTestId("subrow-cell_1_Data use").contains("Marketing");
      cy.getByTestId("subrow-cell_2_Cookie name").contains("cookie");
      cy.getByTestId("subrow-cell_2_Data use").contains("Improve Service");
      cy.getByTestId("subrow-cell_3_Cookie name").contains("cookie2");
      cy.getByTestId("subrow-cell_3_Data use").contains("Improve Service");
    });
  });

  describe("adding a vendor", () => {
    beforeEach(() => {
      stubSystemCrud();
      stubTaxonomyEntities();
      stubVendorList();
      cy.intercept("GET", "/api/v1/system", {
        fixture: "systems/systems.json",
      }).as("getSystems");
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

      it.skip("can add a vendor without the dictionary", () => {
        cy.getByTestId("add-vendor-btn").click();
        cy.getByTestId("input-name").type("test vendor");
        cy.selectOption(
          "input-privacy_declarations.0.consent_use",
          "analytics"
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

      it.skip("can manually add more data uses", () => {
        cy.getByTestId("add-vendor-btn").click();
        cy.getByTestId("add-data-use-btn").should("be.disabled");
        cy.getByTestId("input-name").type("test vendor");
        cy.selectOption(
          "input-privacy_declarations.0.consent_use",
          "analytics"
        );
        cy.getByTestId("input-privacy_declarations.0.cookieNames")
          .find(".custom-creatable-select__input-container")
          .type("one{enter}");

        // Add another use
        cy.getByTestId("add-data-use-btn").click();
        // TODO: this select fails when trying to select "essential" or "functional", but accepts "analytics" or "marketing"
        cy.selectOption(
          "input-privacy_declarations.1.consent_use",
          "marketing"
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
          }
        );
        cy.visit(CONFIGURE_CONSENT_ROUTE);
      });

      it.skip("can fill in dictionary suggestions", () => {
        cy.getByTestId("add-vendor-btn").click();
        cy.getByTestId("input-vendor_id")
          .click()
          .find(`.custom-creatable-select__menu-list`)
          .contains("Aniview LTD")
          .click();
        cy.getByTestId("sparkle-btn").click();
        cy.wait("@getDictionaryDeclarations");
        cy.getSelectValueContainer(
          "input-privacy_declarations.0.consent_use"
        ).contains("Marketing");
        cy.getSelectValueContainer(
          "input-privacy_declarations.0.data_use"
        ).contains("Profiling for Advertising");
        ["av_*", "aniC", "2_C_*"].forEach((cookieName) => {
          cy.getByTestId("input-privacy_declarations.0.cookieNames").contains(
            cookieName
          );
        });

        // Also check one that shouldn't have any cookies
        cy.getSelectValueContainer(
          "input-privacy_declarations.1.data_use"
        ).contains("Analytics for Insights");
        cy.getByTestId("input-privacy_declarations.1.cookieNames").contains(
          "Select..."
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

      it.skip("can create a vendor that is not in the dictionary", () => {
        cy.getByTestId("add-vendor-btn").click();
        cy.getByTestId("input-vendor_id").type("custom vendor{enter}");
        cy.selectOption(
          "input-privacy_declarations.0.consent_use",
          "analytics"
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

  describe("deleting a vendor", () => {
    beforeEach(() => {
      stubSystemCrud();
      stubTaxonomyEntities();
      stubVendorList();
      cy.intercept("GET", "/api/v1/system", {
        fixture: "systems/systems.json",
      }).as("getSystems");
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

    it("can delete a vendor", () => {
      cy.getByTestId("configure-demo_analytics_system").click();
      cy.getByTestId("delete-demo_analytics_system").click();
      cy.getByTestId("continue-btn").click();
      cy.wait("@deleteSystem").then((interception) => {
        const { url } = interception.request;
        expect(url).to.contain("demo_analytics_system");
      });
      cy.getByTestId("toast-success-msg");
    });
  });

  describe("editing a vendor", () => {
    beforeEach(() => {
      stubSystemCrud();
      stubTaxonomyEntities();
      stubVendorList();
      cy.intercept("GET", "/api/v1/system", {
        fixture: "systems/systems.json",
      }).as("getSystems");
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

    it("can add cookies to a vendor", () => {
      cy.getByTestId("configure-demo_marketing_system").click();
      cy.getByTestId("edit-demo_marketing_system").click();
      cy.getByTestId("input-privacy_declarations.0.cookieNames")
        .find(".custom-creatable-select__input-container")
        .type("test{enter}");
      cy.getByTestId("save-btn").click();
      cy.wait("@putSystem").then((interception) => {
        const { body } = interception.request;
        expect(body.privacy_declarations[0].cookies).to.eql([
          {
            name: "_ga",
          },
          {
            name: "test",
            path: "/",
          },
        ]);
      });
    });
  });
});
