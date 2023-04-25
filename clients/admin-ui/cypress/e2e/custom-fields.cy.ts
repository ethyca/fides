import { stubPlus, stubTaxonomyEntities } from "cypress/support/stubs";

import { CUSTOM_FIELDS_ROUTE } from "~/features/common/nav/v2/routes";
import { RoleRegistryEnum } from "~/types/api";

const TAXONOMY_SINGLE_SELECT_ID = "plu_1850be9e-fabc-424d-8224-2fc44c84605a";
const ESSENTIAL_NOTICE_ID = "plu_cce3d8da-1a86-492a-b81e-decb279f7384";

describe("Custom Fields", () => {
  beforeEach(() => {
    cy.login();
    cy.intercept(
      "GET",
      "/api/v1/plus/custom-metadata/custom-field-definition*",
      {
        fixture: "custom-fields/list.json",
      }
    ).as("getCustomFields");
    stubPlus(true);
  });

  describe("permissions", () => {
    it("should not be viewable for approvers", () => {
      cy.assumeRole(RoleRegistryEnum.APPROVER);
      cy.visit(CUSTOM_FIELDS_ROUTE);
      // should be redirected to the home page
      cy.getByTestId("home-content");
    });

    it("should be visible to everyone else", () => {
      [
        RoleRegistryEnum.CONTRIBUTOR,
        RoleRegistryEnum.OWNER,
        RoleRegistryEnum.VIEWER,
      ].forEach((role) => {
        cy.assumeRole(role);
        cy.visit(CUSTOM_FIELDS_ROUTE);
        cy.getByTestId("custom-fields-page");
      });
    });

    it("viewers and approvers cannot toggle the enable toggle", () => {
      [RoleRegistryEnum.VIEWER, RoleRegistryEnum.VIEWER_AND_APPROVER].forEach(
        (role) => {
          cy.assumeRole(role);
          cy.visit(CUSTOM_FIELDS_ROUTE);
          cy.wait("@getCustomFields");
          cy.getByTestId("toggle-Enable")
            .first()
            .within(() => {
              cy.get("span").should("have.attr", "data-disabled");
            });
        }
      );
    });

    it("viewers and approvers cannot add custom fields", () => {
      [RoleRegistryEnum.VIEWER, RoleRegistryEnum.VIEWER_AND_APPROVER].forEach(
        (role) => {
          cy.assumeRole(role);
          cy.visit(CUSTOM_FIELDS_ROUTE);
          cy.wait("@getCustomFields");
          cy.getByTestId("custom-fields-page");
          cy.getByTestId("add-custom-field-btn").should("not.exist");
        }
      );
    });
  });

  it("can show an empty state", () => {
    cy.intercept(
      "GET",
      "/api/v1/plus/custom-metadata/custom-field-definition*",
      {
        body: [],
      }
    ).as("getEmptyCustomFields");
    stubPlus(true);
    cy.visit(CUSTOM_FIELDS_ROUTE);
    cy.wait("@getEmptyCustomFields");
    cy.getByTestId("empty-state");
  });

  describe("table", () => {
    beforeEach(() => {
      cy.visit(CUSTOM_FIELDS_ROUTE);
      cy.wait("@getCustomFields");
      stubTaxonomyEntities();
    });

    it("should render a row for each custom field", () => {
      [
        "Taxonomy - Single select",
        "Taxonomy - Multiple select",
        "Single select list",
        "Multiple select list",
      ].forEach((name) => {
        cy.getByTestId(`row-${name}`);
      });
    });

    it("can sort", () => {
      cy.get("tbody > tr")
        .first()
        .should("contain", "Taxonomy - Single select");
      // sort alphabetical
      cy.getByTestId("column-Title").click();
      cy.get("tbody > tr").first().should("contain", "Multiple select list");

      // sort reverse
      cy.getByTestId("column-Title").click();
      cy.get("tbody > tr")
        .first()
        .should("contain", "Taxonomy - Single select");
    });

    it("can click a row to bring up the edit modal", () => {
      cy.intercept("GET", "/api/v1/plus/custom-metadata/allow-list/*", {
        fixture: "taxonomy/custom-metadata/allow-list/create.json",
      }).as("getAllowList");
      cy.getByTestId("row-Taxonomy - Single select").click();
      cy.wait("@getAllowList");
      cy.getByTestId("custom-field-modal");
    });

    it("can click add button to get to a new form", () => {
      cy.getByTestId("add-custom-field-btn").click();
      cy.getByTestId("custom-field-modal");
    });

    describe("more actions menu", () => {
      it("can edit from the more actions menu", () => {
        cy.intercept("GET", "/api/v1/plus/custom-metadata/allow-list/*", {
          fixture: "taxonomy/custom-metadata/allow-list/create.json",
        }).as("getAllowList");
        cy.get("tbody > tr")
          .first()
          .within(() => {
            cy.getByTestId("more-actions-btn").click();
            cy.getByTestId("edit-btn").click();
          });

        cy.wait("@getAllowList");
        cy.getByTestId("custom-field-modal");
      });

      it("can delete from the more actions menu", () => {
        cy.intercept(
          "DELETE",
          "/api/v1/plus/custom-metadata/custom-field-definition/*",
          { body: {} }
        ).as("deleteCustomFieldDefinition");
        cy.get("tbody > tr")
          .first()
          .within(() => {
            cy.getByTestId("more-actions-btn").click();
            cy.getByTestId("delete-btn").click();
          });
        cy.getByTestId("confirmation-modal");
        cy.getByTestId("continue-btn").click();
        cy.wait("@deleteCustomFieldDefinition").then((interception) => {
          const { url } = interception.request;
          expect(url).to.contain(TAXONOMY_SINGLE_SELECT_ID);
        });
      });
    });

    describe("enabling and disabling", () => {
      beforeEach(() => {
        cy.intercept(
          "PUT",
          "/api/v1/plus/custom-metadata/custom-field-definition*",
          {
            fixture: "custom-fields/list.json",
          }
        ).as("patchCustomFields");
      });

      it("can enable a custom field", () => {
        cy.getByTestId("row-Taxonomy - Single select").within(() => {
          cy.getByTestId("toggle-Enable").within(() => {
            cy.get("span").should("not.have.attr", "data-checked");
          });
          cy.getByTestId("toggle-Enable").click();
        });

        cy.wait("@patchCustomFields").then((interception) => {
          const { body } = interception.request;
          expect(body.id).to.eql(TAXONOMY_SINGLE_SELECT_ID);
          expect(body.active).to.eql(true);
        });
        // redux should requery after invalidation
        cy.wait("@getCustomFields");
      });

      it("can disable a custom field with a warning", () => {
        cy.getByTestId("row-Single select list").within(() => {
          cy.getByTestId("toggle-Enable").within(() => {
            cy.get("span").should("have.attr", "data-checked");
          });
          cy.getByTestId("toggle-Enable").click();
        });

        cy.getByTestId("confirmation-modal");
        cy.getByTestId("continue-btn").click();
        cy.wait("@patchCustomFields").then((interception) => {
          const { body } = interception.request;
          expect(body.id).to.eql(ESSENTIAL_NOTICE_ID);
          expect(body.active).to.eql(false);
        });
        // redux should requery after invalidation
        cy.wait("@getCustomFields");
      });
    });
  });
});
