import {
  stubPlus,
  stubSystemCrud,
  stubTaxonomyEntities,
} from "cypress/support/stubs";

import { SYSTEM_ROUTE } from "~/constants";

describe("System management with Plus features", () => {
  beforeEach(() => {
    cy.login();
    stubSystemCrud();
    stubTaxonomyEntities();
    stubPlus(true);
    cy.intercept("GET", "/api/v1/system", {
      fixture: "systems/systems.json",
    }).as("getSystems");
  });

  describe("custom metadata", () => {
    beforeEach(() => {
      cy.intercept(
        {
          method: "GET",
          pathname: "/api/v1/plus/custom-metadata/allow-list",
          query: {
            show_values: "true",
          },
        },
        {
          fixture: "taxonomy/custom-metadata/allow-list/list.json",
        }
      ).as("getAllowLists");
      cy.intercept(
        "GET",
        `/api/v1/plus/custom-metadata/custom-field-definition/resource-type/*`,

        {
          fixture: "taxonomy/custom-metadata/custom-field-definition/list.json",
        }
      ).as("getCustomFieldDefinitions");
      cy.intercept(
        "GET",
        `/api/v1/plus/custom-metadata/custom-field/resource/*`,
        {
          fixture: "taxonomy/custom-metadata/custom-field/list.json",
        }
      ).as("getCustomFields");
      cy.intercept("PUT", `/api/v1/plus/custom-metadata/custom-field`, {
        fixture: "taxonomy/custom-metadata/custom-field/update-party.json",
      }).as("updateParty");
    });

    it("can populate initial custom metadata", () => {
      cy.visit(`${SYSTEM_ROUTE}/configure/demo_analytics_system`);

      // Should not be able to save while form is untouched
      cy.getByTestId("save-btn").should("be.disabled");
      const testId =
        "input-customFieldValues.id-custom-field-definition-pokemon-party";
      cy.getByTestId(testId).contains("Charmander");
      cy.getByTestId(testId).contains("Eevee");
      cy.getByTestId(testId).contains("Snorlax");
      cy.getByTestId(testId).type("Bulbasaur{enter}");

      // Should be able to save now that form is dirty
      cy.getByTestId("save-btn").should("be.enabled");
      cy.getByTestId("save-btn").click();

      cy.wait("@putSystem");
      cy.wait("@updateParty").then((interception) => {
        expect(interception.request.body.id).to.eql(
          "id-custom-field-pokemon-party"
        );
        expect(interception.request.body.resource_id).to.eql(
          "demo_analytics_system"
        );
        expect(interception.request.body.value).to.eql([
          "Charmander",
          "Eevee",
          "Snorlax",
          "Bulbasaur",
        ]);
      });
    });
  });
});
