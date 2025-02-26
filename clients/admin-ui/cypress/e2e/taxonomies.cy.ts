import { stubTaxonomyEntities } from "cypress/support/stubs";

import { RoleRegistryEnum } from "~/types/api";

const dataCategoriesFixture = require("../fixtures/taxonomy/data_categories.json");

describe("Taxonomy management page", () => {
  beforeEach(() => {
    cy.login();
    stubTaxonomyEntities();
  });

  it("Can navigate to the taxonomy page", () => {
    cy.visit("/");
    cy.getByTestId("Settings-nav-group").click();
    cy.getByTestId("Taxonomy-nav-link").click();
    cy.getByTestId("taxonomy-type-selector");
  });

  describe("Can view taxonomy labels", () => {
    beforeEach(() => {
      cy.visit("/taxonomy");
    });

    it("Can switch between different taxonomies and load data", () => {
      // data uses
      cy.getByTestId("taxonomy-type-selector").selectAntMenuOption("Data uses");
      cy.wait("@getDataUses");

      // data subjects
      cy.getByTestId("taxonomy-type-selector").selectAntMenuOption(
        "Data subjects",
      );
      cy.wait("@getDataSubjects");

      // data categories
      cy.getByTestId("taxonomy-type-selector").selectAntMenuOption(
        "Data categories",
      );
      cy.wait("@getDataCategories");
    });

    it("Renders all active label from the taxonomy", () => {
      cy.getByTestId("taxonomy-interactive-tree").within(() => {
        dataCategoriesFixture
          .filter((c) => c.active)
          .forEach((category) => {
            cy.getByTestId(`taxonomy-node-${category.fides_key}`).should(
              "exist",
            );
          });
      });
    });

    it("Doesn't render inactive labels", () => {
      cy.getByTestId("taxonomy-interactive-tree").within(() => {
        dataCategoriesFixture
          .filter((c) => !c.active)
          .forEach((category) => {
            cy.getByTestId(`taxonomy-node-${category.fides_key}`).should(
              "not.exist",
            );
          });
      });
    });
  });

  describe("Can edit data", () => {
    beforeEach(() => {
      cy.visit("/taxonomy");
      const taxonomyPayload = {
        statusCode: 200,
        body: {
          fides_key: "key",
          organization_fides_key: "default_organization",
          name: "name",
          description: "description",
          parent_key: undefined,
          version_added: "2.0.0",
        },
      };
      cy.intercept("PUT", "/api/v1/data_category*", taxonomyPayload).as(
        "putDataCategory",
      );
      cy.intercept("PUT", "/api/v1/data_use*", taxonomyPayload).as(
        "putDataUse",
      );
      cy.intercept("PUT", "/api/v1/data_subject*", taxonomyPayload).as(
        "putDataSubject",
      );
    });

    it("Open edit drawer when clicking on a taxonomy item", () => {
      cy.getByTestId(`taxonomy-node-user.content`).click();
      cy.getByTestId("edit-drawer-content").should("be.visible");
    });

    it("Edit drawer displays details", () => {
      cy.getByTestId(`taxonomy-node-user.content`).click();
      cy.getByTestId("edit-drawer-content").within(() => {
        cy.contains("header", "User Content");
        cy.getByTestId("edit-drawer-fides-key").should(
          "contain",
          "user.content",
        );
        cy.getByTestId("edit-taxonomy-form_name");
        cy.getByTestId("edit-taxonomy-form_description").should(
          "have.value",
          "Content related to, or created by the subject.",
        );
      });
    });

    it("Can edit taxonomy item", () => {
      const taxonomyiesTestData = [
        {
          menuItemName: "Data categories",
          nodeToEdit: "user.content",
          updateRequest: "@putDataCategory",
        },
        {
          menuItemName: "Data uses",
          nodeToEdit: "functional.service",
          updateRequest: "@putDataUse",
        },
        {
          menuItemName: "Data subjects",
          nodeToEdit: "customer",
          updateRequest: "@putDataSubject",
        },
      ];

      taxonomyiesTestData.forEach((data) => {
        cy.getByTestId("taxonomy-type-selector").selectAntMenuOption(
          data.menuItemName,
        );
        cy.getByTestId(`taxonomy-node-${data.nodeToEdit}`).click();
        cy.getByTestId("edit-drawer-content").within(() => {
          cy.getByTestId("edit-taxonomy-form_name").clear().type("New name");
          cy.getByTestId("edit-taxonomy-form_description")
            .clear()
            .type("New description");
          cy.getByTestId("save-btn").click();
        });
        cy.wait(data.updateRequest).then((interception) => {
          const { body } = interception.request;
          expect(body.name).to.eql("New name");
          expect(body.description).to.eql("New description");
          expect(body.fides_key).to.eql(data.nodeToEdit);
        });
      });
    });

    describe("Data Subject special fields", () => {
      it("Can render an extended form for Data Subject", () => {
        cy.getByTestId("taxonomy-type-selector").selectAntMenuOption(
          "Data subjects",
        );
        cy.getByTestId(`taxonomy-node-customer`).click();

        cy.getByTestId("edit-taxonomy-form_automated-decisions").should(
          "exist",
        );
        cy.getByTestId("edit-taxonomy-form_rights").should("be.visible");
        cy.getByTestId("edit-taxonomy-form_strategy").should("not.exist");
        cy.getByTestId("edit-taxonomy-form_rights").antSelect("Erasure");
        cy.getByTestId("edit-taxonomy-form_strategy").should("be.visible");
      });

      describe("Does valition for data uses special fields", () => {
        it("Can submit without filling any fields", () => {
          cy.getByTestId("taxonomy-type-selector").selectAntMenuOption(
            "Data subjects",
          );
          cy.getByTestId(`taxonomy-node-customer`).click();
          cy.getByTestId("save-btn").click();
          cy.wait("@putDataSubject");
        });
        it("Throws validation error if only Rights is selected", () => {
          cy.getByTestId("taxonomy-type-selector").selectAntMenuOption(
            "Data subjects",
          );
          cy.getByTestId(`taxonomy-node-customer`).click();
          cy.getByTestId("edit-taxonomy-form_rights").antSelect("Erasure");
          cy.getByTestId("save-btn").click();
          cy.get("#edit-taxonomy-form_rights_strategy_help").should(
            "contain",
            "Please select a strategy",
          );
        });
        it("Can submit when Rights and Strategy are selected", () => {
          cy.getByTestId("taxonomy-type-selector").selectAntMenuOption(
            "Data subjects",
          );
          cy.getByTestId(`taxonomy-node-customer`).click();
          cy.getByTestId("edit-taxonomy-form_rights").antSelect("Erasure");
          cy.getByTestId("edit-taxonomy-form_strategy").antSelect("INCLUDE");
          cy.getByTestId("save-btn").click();
          cy.wait("@putDataSubject");
        });
      });

      it("Can edit data uses special fields", () => {
        cy.getByTestId("taxonomy-type-selector").selectAntMenuOption(
          "Data subjects",
        );
        cy.getByTestId(`taxonomy-node-customer`).click();
        cy.getByTestId("edit-taxonomy-form_automated-decisions").click();
        cy.getByTestId("edit-taxonomy-form_rights").antSelect("Erasure");
        cy.getByTestId("edit-taxonomy-form_strategy").antSelect("INCLUDE");
        cy.getByTestId("save-btn").click();
        cy.wait("@putDataSubject").then((interception) => {
          const { body } = interception.request;
          expect(body.automated_decisions_or_profiling).to.equal(true);
          expect(body.rights.values).to.eql(["Erasure"]);
          expect(body.rights.strategy).to.equal("INCLUDE");
        });
      });
    });
  });

  describe("New label creation", () => {
    beforeEach(() => {
      cy.visit("/taxonomy");
    });

    it("Add buttons displays", () => {
      cy.getByTestId(`taxonomy-node-user.content`).within(() => {
        cy.getByTestId("taxonomy-add-child-label-button")
          .should("exist")
          .should("not.be.visible");
      });
      cy.getByTestId(`taxonomy-node-user.content`)
        .realMouseMove(-100, -100, { position: "topLeft" })
        .realMouseMove(0, 0, {
          position: "center",
        });
      cy.getByTestId(`taxonomy-node-user.content`).within(() => {
        cy.getByTestId("taxonomy-add-child-label-button")
          .should("exist")
          .should("be.visible");
      });
    });

    it("Clicking add button adds text input nodes", () => {
      cy.getByTestId("taxonomy-text-input-node").should("not.exist");
      cy.getByTestId(`taxonomy-node-user.content`).within(() => {
        cy.getByTestId("taxonomy-add-child-label-button").click();
      });
      cy.getByTestId("taxonomy-text-input-node").should("exist");
    });

    it("Can add new label", () => {
      cy.intercept("POST", "/api/v1/data_category*", {
        fides_key: "user.content.mynewlabel",
      }).as("postDataCategory");

      cy.getByTestId(`taxonomy-node-user.content`).within(() => {
        cy.getByTestId("taxonomy-add-child-label-button").click();
      });

      cy.getByTestId("taxonomy-text-input-node")
        .find("input")
        .clear()
        .type("My new label{enter}", { delay: 50, waitForAnimations: true });

      cy.wait("@postDataCategory").then((interception) => {
        const { body } = interception.request;
        expect(body.name).to.equal("My new label");
        expect(body.parent_key).to.equal("user.content");
      });
    });
  });

  describe("Label deletion", () => {
    beforeEach(() => {
      cy.visit("/taxonomy");
    });

    it("Delete button triggers confirmation", () => {
      cy.getByTestId(`taxonomy-node-user.content`).click();
      cy.getByTestId("edit-drawer-content").within(() => {
        cy.getByTestId("delete-btn").click();
      });
      cy.getByTestId("confirmation-modal").should("be.visible");
    });

    it("Can (soft) delete a label", () => {
      cy.intercept("PUT", "/api/v1/data_category*", {
        fides_key: "user.content",
        active: false,
      }).as("deleteDataCategory");

      cy.getByTestId(`taxonomy-node-user.content`).click();
      cy.getByTestId("edit-drawer-content").within(() => {
        cy.getByTestId("delete-btn").click();
      });
      cy.getByTestId("confirmation-modal").within(() => {
        cy.getByTestId("continue-btn").click();
      });

      cy.wait("@deleteDataCategory").then((interception) => {
        const { body } = interception.request;
        expect(body.fides_key).to.equal("user.content");
        expect(body.active).to.equal(false);
      });
    });
  });

  describe("Read-only view for users with only read permissions", () => {
    beforeEach(() => {
      cy.login();
      cy.assumeRole(RoleRegistryEnum.VIEWER);
      cy.visit("/taxonomy");
    });

    it("Edit tray inputs are readOnly", () => {
      cy.getByTestId(`taxonomy-node-user.content`).click();
      cy.getByTestId("edit-drawer-content").within(() => {
        cy.getByTestId("edit-taxonomy-form_name").should(
          "have.attr",
          "readonly",
          "readonly",
        );
        cy.getByTestId("edit-taxonomy-form_description").should(
          "have.attr",
          "readonly",
          "readonly",
        );
      });
    });

    it("Edit tray doesn't show save button and delete button", () => {
      cy.getByTestId(`taxonomy-node-user.content`).click();
      cy.getByTestId("edit-drawer-content").within(() => {
        cy.getByTestId("save-btn").should("not.exist");
        cy.getByTestId("delete-btn").should("not.exist");
      });
    });

    it("Doesn't show add label button", () => {
      cy.getByTestId(`taxonomy-node-user.content`).within(() => {
        cy.getByTestId("taxonomy-add-child-label-button").should("not.exist");
      });
    });
  });

  describe("Hidden features", () => {
    beforeEach(() => {
      cy.visit("/taxonomy?showDisabledItems=true");
    });

    it("Can view disabled labels when using ?showDisabledItems=true", () => {
      cy.getByTestId("taxonomy-interactive-tree").within(() => {
        dataCategoriesFixture.forEach((category) => {
          cy.getByTestId(`taxonomy-node-${category.fides_key}`).should("exist");

          if (category.active === false) {
            cy.getByTestId(`taxonomy-node-${category.fides_key}`).should(
              "contain",
              "(disabled)",
            );
          }
        });
      });
    });

    it("Can reenable a disabled label", () => {
      cy.intercept("PUT", "/api/v1/data_category*", {
        fides_key: "user.device.cookie_id",
        active: true,
      }).as("putDataCategory");

      cy.getByTestId(`taxonomy-node-user.device.cookie_id`).click();
      cy.getByTestId("edit-drawer-content").within(() => {
        cy.getByTestId("enable-btn").click();
      });

      cy.wait("@putDataCategory").then((interception) => {
        const { body } = interception.request;
        expect(body.fides_key).to.equal("user.device.cookie_id");
        expect(body.active).to.equal(true);
      });
    });
  });
});
