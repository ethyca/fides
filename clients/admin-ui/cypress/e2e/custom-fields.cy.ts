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

    it("viewers and approvers cannot edit", () => {
      [RoleRegistryEnum.VIEWER, RoleRegistryEnum.VIEWER_AND_APPROVER].forEach(
        (role) => {
          cy.assumeRole(role);
          cy.visit(CUSTOM_FIELDS_ROUTE);

          // row should not be clickable
          cy.getByTestId("row-Taxonomy - Single select").click();
          cy.getByTestId("custom-field-modal").should("not.exist");

          // also should not see the kebob menu
          cy.getByTestId("row-Taxonomy - Single select").within(() => {
            cy.getByTestId("more-actions-btn").should("not.exist");
          });
        }
      );
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

    describe("sorting", () => {
      beforeEach(() => {
        cy.intercept(
          "PUT",
          "/api/v1/plus/custom-metadata/custom-field-definition*",
          {
            fixture: "custom-fields/list.json",
          }
        ).as("patchCustomFields");
      });
      it("should be able to sort", () => {
        cy.get("tbody > tr")
          .first()
          .should("contain", "Taxonomy - Single select");
        // sort alphabetical
        cy.getByTestId("column-Label").click();
        cy.get("tbody > tr").first().should("contain", "Multiple select list");

        // sort reverse
        cy.getByTestId("column-Label").click();
        cy.get("tbody > tr")
          .first()
          .should("contain", "Taxonomy - Single select");
      });

      it("should maintain sort after custom field is enabled/disabled", () => {
        cy.get("tbody > tr")
          .first()
          .should("contain", "Taxonomy - Single select");
        // sort alphabetical
        cy.getByTestId("column-Label").click();
        cy.get("tbody > tr").first().should("contain", "Multiple select list");

        // the patched data needs to be mock or cypress will return the same data
        cy.fixture("custom-fields/list.json").then((customFieldsList) => {
          const updatedList = customFieldsList.map((cf) => {
            if (cf.name === "Single select list") {
              return { ...cf, active: false };
            }
            return cf;
          });
          cy.intercept(
            "GET",
            "/api/v1/plus/custom-metadata/custom-field-definition*",
            {
              body: updatedList,
            }
          ).as("getCustomFieldSingleSelectEnabled");
        });

        // enable custom field
        cy.getByTestId("row-Taxonomy - Single select").within(() => {
          cy.getByTestId("toggle-Enable").click();
        });

        cy.wait("@patchCustomFields");
        // redux should requery after invalidation
        cy.wait("@getCustomFieldSingleSelectEnabled");

        cy.get("tbody > tr").first().should("contain", "Multiple select list");

        // the original mock needs to be brought back
        cy.intercept(
          "GET",
          "/api/v1/plus/custom-metadata/custom-field-definition*",
          {
            fixture: "custom-fields/list.json",
          }
        ).as("getCustomFields");

        // disable custom field
        cy.getByTestId("row-Taxonomy - Single select").within(() => {
          cy.getByTestId("toggle-Enable").click();
        });

        cy.wait("@patchCustomFields");
        // redux should requery after invalidation
        cy.wait("@getCustomFields");

        cy.get("tbody > tr").first().should("contain", "Multiple select list");
      });
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

  describe("editing", () => {
    beforeEach(() => {
      cy.visit(CUSTOM_FIELDS_ROUTE);
      cy.wait("@getCustomFields");
      stubTaxonomyEntities();
      cy.intercept("GET", "/api/v1/plus/custom-metadata/allow-list/*", {
        fixture: "taxonomy/custom-metadata/allow-list/create.json",
      }).as("getAllowList");
    });

    it("can edit from the more actions menu", () => {
      cy.get("tbody > tr")
        .first()
        .within(() => {
          cy.getByTestId("more-actions-btn").click();
          cy.getByTestId("edit-btn").click();
        });

      cy.wait("@getAllowList");
      cy.getByTestId("custom-field-modal");
    });

    it("can click a row to bring up the edit modal", () => {
      cy.getByTestId("row-Taxonomy - Single select").click();
      cy.wait("@getAllowList");
      cy.getByTestId("custom-field-modal");
    });

    describe("edit modal", () => {
      beforeEach(() => {
        cy.getByTestId("row-Taxonomy - Single select").click();
        cy.wait("@getAllowList");
        cy.intercept(
          "PUT",
          "/api/v1/plus/custom-metadata/custom-field-definition*",
          { body: {} }
        ).as("putCustomFieldDefinition");
        cy.intercept("PUT", "/api/v1/plus/custom-metadata/allow-list*", {
          body: {},
        }).as("upsertAllowList");
      });

      it("renders existing values", () => {
        // Field information
        cy.getByTestId("custom-input-name").should(
          "have.value",
          "Taxonomy - Single select"
        );
        cy.getByTestId("custom-input-description").should(
          "have.value",
          "Description!!"
        );
        cy.getSelectValueContainer("input-resource_type").contains(
          "taxonomy:data category"
        );

        // Configuration
        cy.getSelectValueContainer("input-field_type").contains(
          "Single select"
        );
        cy.getByTestId("custom-input-allow_list.allowed_values[0]").should(
          "have.value",
          "allowed"
        );
        cy.getByTestId("custom-input-allow_list.allowed_values[1]").should(
          "have.value",
          "values"
        );
      });

      it("can edit field information", () => {
        const newDescription = "new description";
        cy.getByTestId("custom-input-description").clear().type(newDescription);
        cy.selectOption("input-field_type", "Multiple select");
        cy.getByTestId("save-btn").click();
        cy.wait("@putCustomFieldDefinition").then((interception) => {
          const { body } = interception.request;
          expect(body.description).to.eql(newDescription);
          expect(body.field_type).to.eql("string[]");
        });
        cy.wait("@upsertAllowList");
      });

      it("can add values to the allow list", () => {
        const newAllowItem = "new item";

        cy.getByTestId("add-list-value-btn").click();
        cy.getByTestId(`custom-input-allow_list.allowed_values[2]`).type(
          newAllowItem
        );
        cy.getByTestId("save-btn").click();

        cy.wait("@upsertAllowList").then((interception) => {
          expect(interception.request.body.allowed_values).to.eql([
            "allowed",
            "values",
            newAllowItem,
          ]);
        });
      });

      it("can delete values from the allow list", () => {
        cy.getByTestId("remove-list-value-btn-1").click();
        cy.getByTestId("save-btn").click();
        cy.wait("@upsertAllowList").then((interception) => {
          expect(interception.request.body.allowed_values).to.eql(["allowed"]);
        });
      });
    });

    describe("create modal", () => {
      beforeEach(() => {
        cy.getByTestId("add-custom-field-btn").click();
        cy.intercept(
          "POST",
          "/api/v1/plus/custom-metadata/custom-field-definition*",
          { body: {} }
        ).as("postCustomFieldDefinition");
        cy.intercept("PUT", "/api/v1/plus/custom-metadata/allow-list*", {
          body: {},
        }).as("upsertAllowList");
      });

      it("can fill out a form to create a new select custom field", () => {
        const payload = {
          name: "name",
          description: "description",
          field_type: "string",
          resource_type: "system",
        };
        // Field info
        cy.getByTestId("custom-input-name").type(payload.name);
        cy.getByTestId("custom-input-description").type(payload.description);

        // Configuration
        const allowList = ["snorlax", "eevee"];
        cy.selectOption("input-field_type", "Single select");
        allowList.forEach((item, idx) => {
          cy.getByTestId("add-list-value-btn").click();
          cy.getByTestId(`custom-input-allow_list.allowed_values[${idx}]`).type(
            item
          );
        });

        cy.getByTestId("save-btn").click();
        cy.wait("@postCustomFieldDefinition").then((interception) => {
          const { body } = interception.request;
          expect(body).to.eql(payload);
        });
        cy.wait("@upsertAllowList").then((interception) => {
          const { body } = interception.request;
          expect(body.allowed_values).to.eql(allowList);
        });
      });

      it("can fill out a form to create a new open text custom field", () => {
        const payload = {
          name: "name",
          description: "description",
          field_type: "string",
          resource_type: "data category",
        };
        // Field info
        cy.getByTestId("custom-input-name").type(payload.name);
        cy.getByTestId("custom-input-description").type(payload.description);
        cy.selectOption("input-resource_type", "taxonomy:data category");

        // Configuration
        cy.selectOption("input-field_type", "Open Text");

        cy.getByTestId("save-btn").click();
        cy.wait("@postCustomFieldDefinition").then((interception) => {
          const { body } = interception.request;
          // eslint-disable-next-line @typescript-eslint/naming-convention
          const { allow_list, ...rest } = body;
          expect(rest).to.eql(payload);
        });
      });
    });
  });
});
