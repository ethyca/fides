import {
  stubExperienceConfig,
  stubFidesCloud,
  stubPlus,
  stubProperties,
  stubTranslationConfig,
} from "cypress/support/stubs";

import {
  ADD_PROPERTY_ROUTE,
  PROPERTIES_ROUTE,
} from "~/features/common/nav/routes";
import { RoleRegistryEnum } from "~/types/api";

describe("Properties page", () => {
  beforeEach(() => {
    cy.login();
    stubPlus(true);
    stubProperties();
    stubExperienceConfig();
    stubFidesCloud();
    stubTranslationConfig(true);
    cy.visit(PROPERTIES_ROUTE);
  });

  describe("Table", () => {
    it("Should render properties table", () => {
      cy.getByTestId("properties-table").should("be.visible");
      cy.get("tbody tr[data-row-key]").should("have.length", 2);
    });

    it("Should show empty table notice if there are no properties", () => {
      cy.intercept("GET", "/api/v1/plus/properties*", {
        fixture: "empty-pagination.json",
      }).as("getProperties");
      cy.visit(PROPERTIES_ROUTE);
      cy.wait("@getProperties");
      cy.getByTestId("properties-table").should("be.visible");
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
        cy.getAntTableRow("FDS-CEA9EV").within(() => {
          cy.getByTestId("edit-property-button").should("be.visible");
          cy.getByTestId("delete-property-button").should("be.visible");
        });

        cy.getAntTableRow("FDS-CEA9EV").contains("Property A").click();
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
          cy.getAntTableRow("FDS-CEA9EV").within(() => {
            cy.getByTestId("edit-property-button").should("not.exist");
            cy.getByTestId("delete-property-button").should("not.exist");
          });

          cy.getAntTableRow("FDS-CEA9EV").contains("Property A").click();
          cy.url().should("not.contain", "/property/FDS-");
        },
      );
    });
  });

  describe("Create", () => {
    it("Should create a new property", () => {
      cy.intercept("POST", "/api/v1/plus/property", {
        statusCode: 200,
        body: {
          id: "FDS-NEW123",
          name: "Test Property",
          type: "Website",
          paths: [],
          experiences: [],
        },
      }).as("createProperty");

      cy.visit(ADD_PROPERTY_ROUTE);
      cy.getByTestId("input-name").type("Test Property");
      cy.getByTestId("save-btn").click();

      cy.wait("@createProperty").then((interception) => {
        const { body } = interception.request;
        expect(body.name).to.eq("Test Property");
        expect(body.type).to.eq("Website");
        expect(body.paths).to.eql([]);
      });
    });
  });

  describe("Delete", () => {
    it("Should only allow deletes if a property does not have any experiences", () => {
      cy.getAntTableRow("FDS-CEA9EV").within(() => {
        cy.getByTestId("delete-property-button").should("be.enabled");
      });

      cy.getAntTableRow("FDS-Z21I5X").within(() => {
        cy.getByTestId("delete-property-button").should("be.disabled");
      });
    });

    it("Should trigger a delete after confirming the delete modal", () => {
      cy.intercept("DELETE", "/api/v1/plus/property/*", { statusCode: 200 }).as(
        "deleteProperty",
      );

      cy.getAntTableRow("FDS-CEA9EV").within(() => {
        cy.getByTestId("delete-property-button").click();
      });
      cy.get(".ant-modal-confirm").should("be.visible");
      cy.getAntModalConfirmButtons().contains("Ok").click();
      cy.wait("@deleteProperty");
    });
  });
});
