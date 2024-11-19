import {
  stubExperienceConfig,
  stubFidesCloud,
  stubLanguages,
  stubPlus,
  stubProperties,
} from "cypress/support/stubs";

import { PROPERTIES_ROUTE } from "~/features/common/nav/v2/routes";
import { RoleRegistryEnum } from "~/types/api";

describe("Properties page", () => {
  beforeEach(() => {
    cy.login();
    stubPlus(true);
    stubProperties();
    stubExperienceConfig();
    stubFidesCloud();
    stubLanguages();
    cy.visit(PROPERTIES_ROUTE);
  });

  describe("Table", () => {
    it("Should render properties table", () => {
      cy.getByTestId("fidesTable").should("be.visible");
      cy.getByTestId("fidesTable-body").find("tr").should("have.length", 2);
    });

    it("Should show empty table notice if there are no properties", () => {
      cy.intercept("GET", "/api/v1/plus/properties*", {
        fixture: "empty-pagination.json",
      }).as("getProperties");
      cy.getByTestId("fidesTable").should("be.visible");
      cy.getByTestId("no-results-notice").should("be.visible");
    });
  });

  describe("Permissions", () => {
    it("Owner and contributor have create, edit, and delete permissions", () => {
      [RoleRegistryEnum.OWNER, RoleRegistryEnum.CONTRIBUTOR].forEach((role) => {
        cy.assumeRole(role);
        cy.visit(PROPERTIES_ROUTE);

        cy.intercept("GET", "/api/v1/plus/property/*", {
          fixture: "properties/property.json",
        }).as("getProperty");

        cy.getByTestId("add-property-button").should("be.visible");
        cy.getByTestId("edit-property-button").should("be.visible");
        cy.getByTestId("delete-property-button").should("be.visible");

        cy.get("table").contains("tr", "Property A").click();
        cy.wait("@getProperty");
        cy.getByTestId("delete-property-button").should("exist");
      });
    });
    it("Viewer and approver have view-only permissions", () => {
      [RoleRegistryEnum.VIEWER, RoleRegistryEnum.VIEWER_AND_APPROVER].forEach(
        (role) => {
          cy.assumeRole(role);
          cy.visit(PROPERTIES_ROUTE);

          cy.getByTestId("add-property-button").should("not.exist");
          cy.getByTestId("edit-property-button").should("not.exist");
          cy.getByTestId("delete-property-button").should("not.exist");

          cy.get("table").contains("tr", "Property A").click();
          cy.url().should("not.contain", "/property/FDS-");
        },
      );
    });
  });

  describe("Delete", () => {
    it("Should only allow deletes if a property does not have any experiences", () => {
      cy.contains("tr", "Property A").within(() => {
        cy.getByTestId("delete-property-button").should("be.enabled");
      });

      cy.contains("tr", "Property B").within(() => {
        cy.getByTestId("delete-property-button").should("be.disabled");
      });
    });

    it("Should trigger a delete after confirming the delete modal", () => {
      cy.intercept("DELETE", "/api/v1/plus/property/*", { statusCode: 200 }).as(
        "deleteProperty",
      );

      cy.contains("tr", "Property A").within(() => {
        cy.getByTestId("delete-property-button").click();
      });
      cy.getByTestId("confirmation-modal").should("be.visible");
      cy.getByTestId("continue-btn").click();
      cy.wait("@deleteProperty");
    });
  });
});
