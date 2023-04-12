import { stubSystemCrud, stubTaxonomyEntities } from "cypress/support/stubs";

import {
  ADD_SYSTEMS_MANUAL_ROUTE,
  ADD_SYSTEMS_ROUTE,
  SYSTEM_ROUTE,
} from "~/features/common/nav/v2/routes";

describe("System management page", () => {
  beforeEach(() => {
    cy.login();
    cy.intercept("GET", "/api/v1/system", {
      fixture: "systems/systems.json",
    }).as("getSystems");
  });

  it("Can navigate to the system management page", () => {
    cy.visit("/");
    cy.contains("nav a", "Data map").click();
    cy.contains("nav a", "View systems").click();
    cy.wait("@getSystems");
    cy.getByTestId("system-management");
  });

  describe("Can view data", () => {
    beforeEach(() => {
      cy.visit(SYSTEM_ROUTE);
    });

    it("Can render system cards", () => {
      cy.getByTestId("system-fidesctl_system");

      cy.getByTestId("system-fidesctl_system").within(() => {
        cy.getByTestId("more-btn").click();
        cy.getByTestId("edit-btn");
        cy.getByTestId("delete-btn");
      });
      cy.getByTestId("system-demo_analytics_system");
      cy.getByTestId("system-demo_marketing_system");
    });

    it("Can search and filter cards", () => {
      cy.getByTestId("system-search").type("demo m");
      cy.getByTestId("system-fidesctl_system").should("not.exist");
      cy.getByTestId("system-demo_analytics_system").should("not.exist");
      cy.getByTestId("system-demo_marketing_system");

      // erase "m" so that search input is "demo "
      cy.getByTestId("system-search").type("{backspace}");
      cy.getByTestId("system-fidesctl_system").should("not.exist");
      cy.getByTestId("system-demo_analytics_system");
      cy.getByTestId("system-demo_marketing_system");
    });
  });

  describe("Can create a new system", () => {
    beforeEach(() => {
      stubSystemCrud();
    });

    describe("Create a system manually", () => {
      beforeEach(() => {
        stubTaxonomyEntities();
        stubSystemCrud();
        cy.intercept("GET", "/api/v1/dataset", { fixture: "datasets.json" }).as(
          "getDatasets"
        );
        cy.intercept("GET", "/api/v1/connection_type*", {
          fixture: "connectors/connection_types.json",
        }).as("getConnectionTypes");
      });

      it("shows available system types and lets the user choose one", () => {
        cy.visit(ADD_SYSTEMS_ROUTE);
        cy.getByTestId("manual-btn").click();
        cy.url().should("contain", ADD_SYSTEMS_MANUAL_ROUTE);
        cy.wait("@getConnectionTypes");
        cy.getByTestId("header").contains("Choose a type of system");
        cy.getByTestId("bigquery-item");
        cy.getByTestId("mariadb-item");
        // Click into one of the connectors
        cy.getByTestId("mongodb-item").click();
        cy.getByTestId("header").contains("Describe your MongoDB system");

        // Go back to choosing to add a new type of system
        cy.getByTestId("breadcrumbs").contains("Choose your system").click();
        cy.getByTestId("create-system-btn").click();
        cy.getByTestId("header").contains("Describe your new system");
      });

      it("should allow searching", () => {
        cy.visit(ADD_SYSTEMS_MANUAL_ROUTE);
        cy.wait("@getConnectionTypes");
        cy.getByTestId("bigquery-item");
        cy.getByTestId("system-catalog-search").type("db");
        cy.getByTestId("bigquery-item").should("not.exist");
        cy.getByTestId("mariadb-item");
        cy.getByTestId("mongodb-item");
        cy.getByTestId("timescale-item");

        // empty state
        cy.getByTestId("system-catalog-search")
          .clear()
          .type("a very specific system that we do not have");
        cy.getByTestId("no-systems-found");
      });

      it("Can step through the flow", () => {
        cy.fixture("systems/system.json").then((system) => {
          // Fill in the describe form based on fixture data
          cy.visit(ADD_SYSTEMS_ROUTE);
          cy.getByTestId("manual-btn").click();
          cy.url().should("contain", ADD_SYSTEMS_MANUAL_ROUTE);
          cy.wait("@getSystems");
          cy.wait("@getConnectionTypes");
          cy.getByTestId("create-system-btn").click();
          cy.getByTestId("input-name").type(system.name);
          cy.getByTestId("input-fides_key").type(system.fides_key);
          cy.getByTestId("input-description").type(system.description);

          cy.getByTestId("save-btn").click();
          cy.wait("@postSystem").then((interception) => {
            const { body } = interception.request;
            expect(body).to.eql({
              name: system.name,
              organization_fides_key: system.organization_fides_key,
              fides_key: system.fides_key,
              description: system.description,
              system_type: "",
              tags: [],
              privacy_declarations: [],
              third_country_transfers: [],
              system_dependencies: [],
            });
          });

          // Fill in the privacy declaration form
          cy.getByTestId("tab-Data uses").click();
          cy.getByTestId("add-btn").click();
          cy.wait([
            "@getDataCategories",
            "@getDataSubjects",
            "@getDataUses",
            "@getDatasets",
          ]);
          cy.getByTestId("new-declaration-form");
          const declaration = system.privacy_declarations[0];
          cy.getByTestId("input-data_use").click();
          cy.getByTestId("input-data_use").within(() => {
            cy.contains(declaration.data_use).click();
          });
          declaration.data_categories.forEach((dc) => {
            cy.getByTestId("input-data_categories").type(`${dc}{enter}`);
          });
          declaration.data_subjects.forEach((ds) => {
            cy.getByTestId("input-data_subjects").type(`${ds}{enter}`);
          });
          cy.getByTestId("input-dataset_references").click();
          cy.getByTestId("input-dataset_references").within(() => {
            cy.contains("Demo Users Dataset 2").click();
          });

          cy.getByTestId("save-btn").click();
          cy.wait("@putSystem").then((interception) => {
            const { body } = interception.request;
            expect(body.privacy_declarations[0]).to.eql({
              name: "",
              data_use: declaration.data_use,
              data_categories: declaration.data_categories,
              data_subjects: declaration.data_subjects,
              dataset_references: ["demo_users_dataset_2"],
            });
          });
          cy.getByTestId("new-declaration-form").within(() => {
            cy.getByTestId("header").contains("System");
          });
        });
      });

      it("can render a warning when there is unsaved data", () => {
        cy.visit(ADD_SYSTEMS_MANUAL_ROUTE);
        cy.wait("@getSystems");
        cy.wait("@getConnectionTypes");
        cy.getByTestId("create-system-btn").click();
        cy.getByTestId("input-name").type("test");
        cy.getByTestId("input-fides_key").type("test");
        cy.getByTestId("save-btn").click();
        cy.wait("@postSystem");

        // start typing a description
        const description = "half formed thought";
        cy.getByTestId("input-description").type(description);
        // then try navigating to the privacy declarations tab
        cy.getByTestId("tab-Data uses").click();
        cy.getByTestId("confirmation-modal");
        // make sure canceling works
        cy.getByTestId("cancel-btn").click();
        cy.getByTestId("input-description").should("have.value", description);
        // now actually discard
        cy.getByTestId("tab-Data uses").click();
        cy.getByTestId("continue-btn").click();
        // should load the privacy declarations page
        cy.getByTestId("privacy-declaration-step");
        // navigate back
        cy.getByTestId("tab-System information").click();
        cy.getByTestId("input-description").should("have.value", "");
      });
    });
  });

  describe("Can delete a system", () => {
    beforeEach(() => {
      stubSystemCrud();
    });

    it("Can delete a system from its card", () => {
      cy.visit(SYSTEM_ROUTE);
      cy.getByTestId("system-fidesctl_system").within(() => {
        cy.getByTestId("more-btn").click();
        cy.getByTestId("delete-btn").click();
      });
      cy.getByTestId("confirmation-modal");
      cy.getByTestId("continue-btn").click();
      cy.wait("@deleteSystem").then((interception) => {
        const { url } = interception.request;
        expect(url).to.contain("fidesctl_system");
      });
      cy.getByTestId("toast-success-msg");
    });

    it("Can render an error on delete", () => {
      cy.intercept("DELETE", "/api/v1/system/*", {
        statusCode: 404,
        body: {
          detail: {
            error: "resource does not exist",
            fides_key: "key",
            resource_type: "System",
          },
        },
      }).as("deleteSystemError");
      cy.visit(SYSTEM_ROUTE);
      cy.getByTestId("system-fidesctl_system").within(() => {
        cy.getByTestId("more-btn").click();
        cy.getByTestId("delete-btn").click();
      });
      cy.getByTestId("confirmation-modal");
      cy.getByTestId("continue-btn").click();
      cy.wait("@deleteSystemError");
      cy.getByTestId("toast-error-msg").contains("resource does not exist");
    });
  });

  describe("Can edit a system", () => {
    beforeEach(() => {
      stubSystemCrud();
      stubTaxonomyEntities();
      cy.fixture("systems/systems.json").then((systems) => {
        cy.intercept("GET", "/api/v1/system/*", {
          body: systems[0],
        }).as("getFidesctlSystem");
      });
      cy.visit(SYSTEM_ROUTE);
    });

    it("Can go directly to a system's edit page", () => {
      cy.visit("/systems/configure/fidesctl_system");
      cy.wait("@getFidesctlSystem");
      cy.getByTestId("input-name").should("have.value", "Fidesctl System");

      cy.intercept("GET", "/api/v1/system/*", {
        statusCode: 404,
      }).as("getNotFoundSystem");

      // and can render a not found state
      cy.visit("/systems/configure/system-that-does-not-exist");
      cy.getByTestId("system-not-found");
    });

    it("Can go through the edit flow", () => {
      cy.getByTestId("system-fidesctl_system").within(() => {
        cy.getByTestId("more-btn").click();
        cy.getByTestId("edit-btn").click();
      });
      cy.url().should("contain", "/systems/configure/fidesctl_system");

      cy.wait("@getFidesctlSystem");

      // check that the form has the proper values filled in
      cy.getByTestId("input-name").should("have.value", "Fidesctl System");
      cy.getByTestId("input-fides_key").should("have.value", "fidesctl_system");
      cy.getByTestId("input-description").should(
        "have.value",
        "Software that functionally applies Fides."
      );
      cy.getByTestId("input-data_responsibility_title").should(
        "contain",
        "Controller"
      );
      cy.getByTestId("input-administrating_department").should(
        "have.value",
        "Not defined"
      );
      // add something for joint controller
      const controllerName = "Sally Controller";
      cy.getByTestId("input-joint_controller.name").type(controllerName);
      cy.getByTestId("save-btn").click();
      cy.wait("@putSystem").then((interception) => {
        const { body } = interception.request;
        expect(body.joint_controller.name).to.eql(controllerName);
      });

      // Switch to the Data Uses tab
      cy.getByTestId("tab-Data uses").click();

      // add another privacy declaration
      const secondDataUse = "advertising";
      cy.getByTestId("tab-Data uses").click();
      cy.getByTestId("add-btn").click();
      cy.wait(["@getDataCategories", "@getDataSubjects", "@getDataUses"]);
      cy.getByTestId("new-declaration-form").within(() => {
        cy.getByTestId("input-data_use").type(`${secondDataUse}{enter}`);
        cy.getByTestId("input-name").type(`test-1{enter}`);
        cy.getByTestId("input-data_categories").type(`user.biometric{enter}`);
        cy.getByTestId("input-data_subjects").type(`anonymous{enter}`);
        cy.getByTestId("save-btn").click();
      });
      cy.wait("@putSystem").then((interception) => {
        const { body } = interception.request;
        expect(body.privacy_declarations.length).to.eql(2);
        expect(body.privacy_declarations[1].data_use).to.eql(secondDataUse);
      });

      // edit the existing declaration
      const newDataUse = "collect";
      cy.getByTestId("accordion-header-improve.system").click();
      cy.getByTestId("improve.system-form").within(() => {
        cy.getByTestId("input-data_use").type(`${newDataUse}{enter}`);
        cy.getByTestId("save-btn").click();
      });
      cy.wait("@putSystem").then((interception) => {
        const { body } = interception.request;
        expect(body.privacy_declarations.length).to.eql(1);
        expect(body.privacy_declarations[0].data_use).to.eql(newDataUse);
      });
      cy.getByTestId("saved-indicator");
    });

    it("Can render and edit extended form fields", () => {
      cy.intercept("GET", "/api/v1/dataset", { fixture: "datasets.json" }).as(
        "getDatasets"
      );
      const system = {
        fides_key: "fidesctl_system",
        system_type: "cool system",
        data_responsibility_title: "Sub-Processor",
        organization_fides_key: "default_organization",
        administrating_department: "department",
        third_country_transfers: ["USA"],
        joint_controller: {
          name: "bob",
          email: "bob@ethyca.com",
        },
        data_protection_impact_assessment: {
          is_required: true,
          progress: "in progress",
          link: "http://www.ethyca.com",
        },
      };
      cy.getByTestId("system-fidesctl_system").within(() => {
        cy.getByTestId("more-btn").click();
        cy.getByTestId("edit-btn").click();
      });

      // input extra fields
      cy.getByTestId("input-data_responsibility_title").click();
      cy.getByTestId("input-data_responsibility_title").within(() => {
        cy.contains(system.data_responsibility_title).click();
      });
      cy.getByTestId("input-administrating_department")
        .clear()
        .type(system.administrating_department);
      cy.getByTestId("input-third_country_transfers").type(
        "United States of America{enter}"
      );
      cy.getByTestId("input-joint_controller.name").type(
        system.joint_controller.name
      );
      cy.getByTestId("input-joint_controller.email").type(
        system.joint_controller.email
      );
      cy.getByTestId(
        "input-data_protection_impact_assessment.is_required"
      ).within(() => {
        cy.getByTestId("option-true").click();
      });
      cy.getByTestId("input-data_protection_impact_assessment.progress").type(
        system.data_protection_impact_assessment.progress
      );
      cy.getByTestId("input-data_protection_impact_assessment.link").type(
        system.data_protection_impact_assessment.link
      );

      cy.getByTestId("save-btn").click();
      cy.wait("@putSystem").then((interception) => {
        const { body } = interception.request;
        const {
          privacy_declarations: privacyDeclarations,
          tags,
          fidesctl_meta: fidesctlMeta,
          meta,
          registry_id: registryid,
          system_dependencies: systemDependencies,
          ...edited
        } = body;
        expect(edited).to.eql({
          name: "Fidesctl System",
          organization_fides_key: system.organization_fides_key,
          fides_key: system.fides_key,
          description: "Software that functionally applies Fides.",
          system_type: "Service",
          egress: [],
          ingress: [],
          third_country_transfers: ["USA"],
          administrating_department: system.administrating_department,
          data_responsibility_title: system.data_responsibility_title,
          joint_controller: system.joint_controller,
          data_protection_impact_assessment:
            system.data_protection_impact_assessment,
        });
      });
    });
  });

  describe("Data uses", () => {
    beforeEach(() => {
      stubSystemCrud();
      stubTaxonomyEntities();
      cy.fixture("systems/systems.json").then((systems) => {
        cy.intercept("GET", "/api/v1/system/*", {
          body: systems[0],
        }).as("getFidesctlSystem");
      });
    });

    it("warns when a data use and processing activity is being added that is already used", () => {
      cy.visit(SYSTEM_ROUTE);
      cy.getByTestId("system-fidesctl_system").within(() => {
        cy.getByTestId("more-btn").click();
        cy.getByTestId("edit-btn").click();
      });
      // "improve.system" and "Store system data." are already being used
      cy.getByTestId("tab-Data uses").click();
      cy.getByTestId("add-btn").click();
      cy.wait(["@getDataCategories", "@getDataSubjects", "@getDataUses"]);
      cy.getByTestId("new-declaration-form").within(() => {
        cy.getByTestId("input-data_use").type(`improve.system{enter}`);
        cy.getByTestId("input-name").type(`Store system data.{enter}`);
        cy.getByTestId("input-data_categories").type(`user.biometric{enter}`);
        cy.getByTestId("input-data_subjects").type(`anonymous{enter}`);
        cy.getByTestId("save-btn").click();
      });
      cy.getByTestId("toast-error-msg");

      // changing to a different data use should go through
      cy.getByTestId("new-declaration-form").within(() => {
        cy.getByTestId("input-data_use").type(`collect{enter}`);
        cy.getByTestId("save-btn").click();
      });
      cy.getByTestId("toast-success-msg");
    });

    it("warns when a data use is being edited to one that is already used", () => {
      cy.fixture("systems/systems_with_data_uses.json").then((systems) => {
        cy.intercept("GET", "/api/v1/system/*", {
          body: systems[0],
        }).as("getFidesctlSystemWithDataUses");
      });
      cy.visit(`${SYSTEM_ROUTE}/configure/fidesctl_system`);
      cy.wait("@getFidesctlSystemWithDataUses");

      cy.getByTestId("tab-Data uses").click();
      cy.getByTestId("add-btn").click();
      cy.wait(["@getDataCategories", "@getDataSubjects", "@getDataUses"]);

      cy.getByTestId(`accordion-header-improve.system`);
      cy.getByTestId(`accordion-header-advertising`).click();

      // try to change 'advertising' to 'improve.system' and make their names match
      cy.getByTestId("advertising-form").within(() => {
        cy.getByTestId("input-data_use").type(`improve.system{enter}`);
        cy.getByTestId("input-name").clear().type(`Store system data.{enter}`);
        cy.getByTestId("save-btn").click();
      });
      cy.getByTestId("toast-error-msg");
    });

    it("can have multiple of the same data use if the names are different", () => {
      cy.visit(SYSTEM_ROUTE);
      cy.getByTestId("system-fidesctl_system").within(() => {
        cy.getByTestId("more-btn").click();
        cy.getByTestId("edit-btn").click();
      });
      // "improve.system" and "Store system data." are already being used
      // use "improve.system" again but a different name
      cy.getByTestId("tab-Data uses").click();
      cy.getByTestId("add-btn").click();
      cy.wait(["@getDataCategories", "@getDataSubjects", "@getDataUses"]);
      cy.getByTestId("new-declaration-form").within(() => {
        cy.getByTestId("input-data_use").type(`improve.system{enter}`);
        cy.getByTestId("input-name").type(`A different description.{enter}`);
        cy.getByTestId("input-data_categories").type(`user.biometric{enter}`);
        cy.getByTestId("input-data_subjects").type(`anonymous{enter}`);
        cy.getByTestId("save-btn").click();
      });
      cy.getByTestId("toast-success-msg");
    });

    describe("delete privacy declaration", () => {
      beforeEach(() => {
        cy.fixture("systems/systems_with_data_uses.json").then((systems) => {
          cy.intercept("GET", "/api/v1/system/*", {
            body: systems[0],
          }).as("getFidesctlSystemWithDataUses");
        });
        cy.visit(`${SYSTEM_ROUTE}/configure/fidesctl_system`);
        cy.wait("@getFidesctlSystemWithDataUses");

        cy.getByTestId("tab-Data uses").click();
      });

      it("deletes a new privacy declaration", () => {
        cy.getByTestId("add-btn").click();
        cy.wait(["@getDataCategories", "@getDataSubjects", "@getDataUses"]);

        // new form's "delete" btn should be disabled until save
        cy.getByTestId("new-declaration-form").within(() => {
          cy.getByTestId("input-data_use").type(`collect{enter}`);
          cy.getByTestId("input-data_categories").type(`user.biometric{enter}`);
          cy.getByTestId("input-data_subjects").type(`anonymous{enter}`);
          cy.getByTestId("delete-btn").should("be.disabled");
          cy.getByTestId("save-btn").click();
          cy.wait("@putSystem");
          cy.getByTestId("delete-btn").should("be.enabled");
          // now go through delete flow
          cy.getByTestId("delete-btn").click();
        });
        cy.getByTestId("continue-btn").click();
        cy.wait("@putSystem");
        cy.getByTestId("toast-success-msg").contains("Data use deleted");
      });

      it("deletes an accordion privacy declaration", () => {
        cy.getByTestId("accordion-header-improve.system").click();
        cy.getByTestId("improve.system-form").within(() => {
          cy.getByTestId("delete-btn").click();
        });
        cy.getByTestId("continue-btn").click();
        cy.wait("@putSystem").then((interception) => {
          const { body } = interception.request;
          expect(body.privacy_declarations.length).to.eql(1);
          expect(body.privacy_declarations[0].data_use !== "improve.system");
        });
        cy.getByTestId("toast-success-msg").contains("Data use deleted");
      });
    });
  });

  describe("Data flow", () => {
    beforeEach(() => {
      stubSystemCrud();
      stubTaxonomyEntities();
      cy.fixture("systems/systems.json").then((systems) => {
        cy.intercept("GET", "/api/v1/system/*", {
          body: systems[1],
        }).as("getFidesctlSystem");
      });

      cy.visit(SYSTEM_ROUTE);
      cy.getByTestId("system-fidesctl_system").within(() => {
        cy.getByTestId("more-btn").click();
        cy.getByTestId("edit-btn").click();
      });
      cy.getByTestId("tab-Data flow").click();
    });

    it("Can navigate to the data flow tab", () => {
      cy.getByTestId("data-flow-accordion").should("exist");
    });

    it("Can open both accordion items", () => {
      cy.getByTestId("data-flow-accordion").within(()=>{
        cy.getByTestId("data-flow-button-Source").click();
        cy.getByTestId("data-flow-panel-Source").should("exist");
        cy.getByTestId("data-flow-button-Destination").click();
        cy.getByTestId("data-flow-panel-Destination").should("exist");
      })
    });
  });
});
