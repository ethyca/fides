import { stubTaxonomyEntities } from "cypress/support/stubs";

const dataCategoriesFixture = require("../fixtures/taxonomy/data_categories.json");

describe("Taxonomy management page", () => {
  beforeEach(() => {
    cy.login();
    stubTaxonomyEntities();
  });

  it("Can navigate to the taxonomy page", () => {
    cy.visit("/");
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
      console.log("dataCategoriesFixture", dataCategoriesFixture);

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
          cy.getByTestId("edit-taxonomy-form_strategy").should(
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

  describe("Custom fields", () => {
    it("Can render an extended form for custom fields", () => {});

    it("Does validation for custom fields", () => {});

    it("Can edit custom fields", () => {});
  });

  describe("New label creation", () => {
    it("Add buttons displays", () => {});

    it("Clicking add button adds text input nodes", () => {});

    it("Can add new label", () => {});
  });

  describe("Label deletion", () => {
    it("Delete button triggers confirmation", () => {});

    it("Can delete a label", () => {});
  });

  describe("Hidden features", () => {
    it("Can view disabled labels when using ?showDisabledItems=true", () => {});

    it("Can reenable a disabled label", () => {});
  });

  describe("Can create data", () => {
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
        },
      };
      cy.intercept("POST", "/api/v1/data_category*", taxonomyPayload).as(
        "postDataCategory",
      );
      cy.intercept("POST", "/api/v1/data_use*", taxonomyPayload).as(
        "postDataUse",
      );
      cy.intercept("POST", "/api/v1/data_subject*", taxonomyPayload).as(
        "postDataSubject",
      );
    });

    it("Can open a create form for each taxonomy entity", () => {
      const expectedTabValues = [
        {
          tab: "Data Categories",
          name: "Data category",
          request: "@postDataCategory",
        },
        {
          tab: "Data Uses",
          name: "Data use",
          request: "@postDataUse",
        },
        {
          tab: "Data Subjects",
          name: "Data subject",
          request: "@postDataSubject",
        },
      ];
      expectedTabValues.forEach((tabValue) => {
        cy.getByTestId(`tab-${tabValue.tab}`).click();
        cy.getByTestId("add-taxonomy-btn").click();
        cy.getByTestId("create-taxonomy-form");
        cy.getByTestId("form-heading").should("contain", tabValue.name);

        // add a root value
        cy.getByTestId("input-fides_key").type("foo");
        if (tabValue.tab !== "Data Subjects") {
          cy.getByTestId("input-parent_key").should("have.value", "");
        }
        cy.getByTestId("submit-btn").click();
        cy.wait(tabValue.request).then((interception) => {
          const { body } = interception.request;
          expect(body.fides_key).to.eql("foo");
          expect(body.parent_key).to.equal(undefined);
          expect(body.is_default).to.equal(false);
        });
        cy.getByTestId("toast-success-msg").should("exist");

        // add a child value
        cy.getByTestId("add-taxonomy-btn").click();
        cy.getByTestId("input-fides_key").type("foo.bar.baz");
        if (tabValue.tab !== "Data Subjects") {
          cy.getByTestId("input-parent_key").should("have.value", "foo.bar");
        }
        cy.getByTestId("submit-btn").click();
        cy.wait(tabValue.request).then((interception) => {
          const { body } = interception.request;
          expect(body.fides_key).to.eql("foo.bar.baz");
          expect(body.parent_key).to.equal("foo.bar");
          expect(body.is_default).to.equal(false);
        });
        cy.getByTestId("toast-success-msg").should("exist");
      });
    });

    it("Can trigger an error", () => {
      const errorMsg = "Internal Server Error";
      cy.intercept("POST", "/api/v1/data_category*", {
        statusCode: 500,
        body: errorMsg,
      }).as("postDataCategoryError");

      cy.getByTestId(`tab-Data Categories`).click();
      cy.getByTestId("add-taxonomy-btn").click();

      cy.getByTestId("input-fides_key").type("foo");
      cy.getByTestId("submit-btn").click();

      cy.wait("@postDataCategoryError");
      cy.getByTestId("toast-success-msg").should("not.exist");
      cy.getByTestId("taxonomy-form-error").should("contain", errorMsg);
    });

    it("Will only show either the add or the edit form", () => {
      cy.getByTestId(`tab-Data Categories`).click();
      const openEditForm = () => {
        cy.getByTestId("accordion-item-System Data").trigger("mouseover");
        cy.getByTestId("edit-btn").click();
      };
      const openCreateForm = () => {
        cy.getByTestId("add-taxonomy-btn").click();
      };
      openEditForm();
      cy.getByTestId("edit-taxonomy-form");
      cy.getByTestId("create-taxonomy-form").should("not.exist");
      openCreateForm();
      cy.getByTestId("edit-taxonomy-form").should("not.exist");
      cy.getByTestId("create-taxonomy-form");
      openEditForm();
      cy.getByTestId("edit-taxonomy-form");
      cy.getByTestId("create-taxonomy-form").should("not.exist");
    });
  });

  describe("Can delete data", () => {
    beforeEach(() => {
      cy.visit("/taxonomy");

      const taxonomyPayload = {
        statusCode: 200,
        body: {
          message: "resource deleted",
          resource: {
            fides_key: "key",
            organization_fides_key: "default_organization",
            tags: null,
            name: "name",
            description: "description",
            parent_key: null,
            is_default: false,
          },
        },
      };
      cy.intercept("DELETE", "/api/v1/data_category/*", taxonomyPayload).as(
        "deleteDataCategory",
      );
      cy.intercept("DELETE", "/api/v1/data_use/*", taxonomyPayload).as(
        "deleteDataUse",
      );
      cy.intercept("DELETE", "/api/v1/data_subject/*", taxonomyPayload).as(
        "deleteDataSubject",
      );
    });

    it("Only renders delete button on custom fields", () => {
      cy.getByTestId(`tab-Data Categories`).click();
      // try default fields first
      cy.getByTestId("accordion-item-User Data").trigger("mouseover");
      cy.getByTestId("delete-btn").should("not.exist");
      cy.getByTestId("accordion-item-User Data").click();
      cy.getByTestId("item-Job Title").trigger("mouseover");
      cy.getByTestId("delete-btn").should("not.exist");

      // now try custom fields
      cy.getByTestId("accordion-item-Custom field").trigger("mouseover");
      cy.getByTestId("delete-btn").click();
      // parent custom fields should render with a warning
      cy.getByTestId("delete-children-warning");
      cy.getByTestId("cancel-btn").click();
      cy.getByTestId("accordion-item-Custom field").click();
      cy.getByTestId("item-Custom foo").trigger("mouseover");
      cy.getByTestId("delete-btn").click();
      // leaf nodes do not need a warning though
      cy.getByTestId("delete-children-warning").should("not.exist");
    });

    it("Can delete from each taxonomy type (except Data Subject)", () => {
      // Data Subject is slightly different than the others since it doesn't have
      // a parent field, so easiest to split it out into its own test
      const tabValues = [
        { tab: "Data Categories", request: "@deleteDataCategory" },
        { tab: "Data Uses", request: "@deleteDataUse" },
      ];
      tabValues.forEach((tabValue) => {
        cy.getByTestId(`tab-${tabValue.tab}`).click();
        cy.getByTestId("accordion-item-Custom field").click();
        cy.getByTestId("item-Custom foo").trigger("mouseover");
        cy.getByTestId("delete-btn").click();
        cy.getByTestId("continue-btn").click();
        cy.wait(tabValue.request).then((interception) => {
          const { url } = interception.request;
          expect(url).to.contain("custom.foo");
        });
        cy.getByTestId("toast-success-msg");
      });
    });

    it("Can delete taxonomy field from Data Subject", () => {
      cy.getByTestId(`tab-Data Subjects`).click();
      cy.getByTestId("item-Custom field").trigger("mouseover");
      cy.getByTestId("delete-btn").click();
      cy.getByTestId("continue-btn").click();
      cy.wait("@deleteDataSubject").then((interception) => {
        const { url } = interception.request;
        expect(url).to.contain("custom");
      });
      cy.getByTestId("toast-success-msg");
    });

    it("Can render an error on delete", () => {
      cy.intercept("DELETE", "/api/v1/data_category/*", {
        statusCode: 500,
        body: "Internal Server Error",
      }).as("deleteDataCategoryError");
      cy.getByTestId(`tab-Data Categories`).click();
      cy.getByTestId("accordion-item-Custom field").click();
      cy.getByTestId("item-Custom foo").trigger("mouseover");
      cy.getByTestId("delete-btn").click();
      cy.getByTestId("continue-btn").click();
      cy.wait("@deleteDataCategoryError");
      cy.getByTestId("toast-error-msg");
    });
  });
});
