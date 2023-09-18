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
      stubPlus(true);
      cy.intercept("GET", "/api/v1/system", {
        body: [],
      }).as("getEmptySystems");
      cy.visit(CONFIGURE_CONSENT_ROUTE);
      cy.getByTestId("empty-state");
      cy.get("body").click(0, 0);
      cy.getByTestId("add-vendor-btn").click();
      cy.getByTestId("add-vendor-modal-content");
    });
  });

  describe("with existing systems", () => {
    beforeEach(() => {
      stubSystemCrud();
      stubTaxonomyEntities();
      stubPlus(true);
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
      cy.getByTestId("subrow-cell_1_Data use").contains("advertising");
      cy.getByTestId("subrow-cell_2_Cookie name").contains("cookie");
      cy.getByTestId("subrow-cell_2_Data use").contains("Improve Service");
      cy.getByTestId("subrow-cell_3_Cookie name").contains("cookie2");
      cy.getByTestId("subrow-cell_3_Data use").contains("Improve Service");

      cy.getByTestId("add-cookie-btn");
      cy.getByTestId("add-vendor-btn");
    });
  });

  describe.only("adding a vendor", () => {
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
          fides_cloud: {
            enabled: false,
          },
        });
        cy.visit(CONFIGURE_CONSENT_ROUTE);
      });

      it("can add a vendor without the dictionary", () => {
        cy.getByTestId("add-vendor-btn").click();
        cy.getByTestId("input-name").type("test vendor");
        cy.selectOption("input-privacy_declarations.0.data_use", "advertising");
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
                data_use: "advertising",
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
        cy.selectOption("input-privacy_declarations.0.data_use", "advertising");
        cy.getByTestId("input-privacy_declarations.0.cookieNames")
          .find(".custom-creatable-select__input-container")
          .type("one{enter}");

        // Add another use
        cy.getByTestId("add-data-use-btn").click();
        cy.selectOption(
          "input-privacy_declarations.1.data_use",
          "personalize.system"
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
              data_use: "advertising",
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
              data_use: "personalize.system",
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
        stubPlus(true);
        cy.visit(CONFIGURE_CONSENT_ROUTE);
      });

      it.only("can fill in dictionary suggestions", () => {
        cy.getByTestId("add-vendor-btn").click();
        cy.getByTestId("input-vendor_id")
          .click()
          .find(`.custom-creatable-select__menu-list`)
          .contains("Aniview LTD")
          .click();
        cy.getByTestId("sparkle-btn").click();
        cy.wait("@getDictionaryDeclarations");
        // TODO: fix when taxonomy fixes are in
        // cy.getSelectValueContainer(
        //   "input-privacy_declarations.0.data_use"
        // ).contains("marketing.advertising.profiling");
        ["av_*", "aniC", "2_C_*"].forEach((cookieName) => {
          cy.getByTestId("input-privacy_declarations.0.cookieNames").contains(
            cookieName
          );
        });

        // Also check one that shouldn't have any cookies
        cy.getByTestId("input-privacy_declarations.3.cookieNames").contains(
          "Select..."
        );
        // There should be 13 declarations (but start from 0, so 12)
        cy.getByTestId("input-privacy_declarations.12.cookieNames");
      });

      it("can create a vendor that is not in the dictionary", () => {
        cy.getByTestId("add-vendor-btn").click();
        cy.getByTestId("input-vendor_id").type("custom vendor{enter}");
        cy.selectOption("input-privacy_declarations.0.data_use", "advertising");
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
                data_use: "advertising",
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
