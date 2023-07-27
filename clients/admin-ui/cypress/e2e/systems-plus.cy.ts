import {
  stubPlus,
  stubSystemCrud,
  stubTaxonomyEntities,
  stubVendorList
} from "cypress/support/stubs";

import { SYSTEM_ROUTE } from "~/features/common/nav/v2/routes";

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

  describe("vendor list", ()=>{
    beforeEach(()=>{
      cy.visit(`${SYSTEM_ROUTE}/configure/demo_analytics_system`);
      stubVendorList();
    })

    it("can display the vendor list dropdown",()=>{
      cy.getSelectValueContainer("input-meta.vendor.id")
    })

    it("contains dictionary entries", ()=>{
      cy.selectOption("input-meta.vendor.id", "Aniview LTD")
    })
    
    it("can switch entries", ()=>{
      cy.selectOption("input-meta.vendor.id", "Aniview LTD")
      cy.getSelectValueContainer("input-meta.vendor.id").contains("Aniview LTD")

      cy.selectOption("input-meta.vendor.id", "Jaduda GmbH")
      cy.getSelectValueContainer("input-meta.vendor.id").contains("Jaduda GmbH")
    })
    
  })

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

      // There are two custom field updates that will take place, but order is not stable
      const expectedValues = [
        {
          id: "id-custom-field-pokemon-party",
          resource_id: "demo_analytics_system",
          value: ["Charmander", "Eevee", "Snorlax", "Bulbasaur"],
        },
        {
          id: "id-custom-field-starter-pokemon",
          resource_id: "demo_analytics_system",
          value: "Squirtle",
        },
      ];
      cy.wait(["@updateParty", "@updateParty"]).then((interceptions) => {
        expectedValues.forEach((expected) => {
          const interception = interceptions.find(
            (i) => i.request.body.id === expected.id
          );
          expect(interception.request.body.resource_id).to.eql(
            expected.resource_id
          );
          expect(interception.request.body.value).to.eql(expected.value);
        });
      });
    });
  });
});
