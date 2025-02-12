import {
  stubDatasetCrud,
  stubPlus,
  stubSystemCrud,
  stubSystemIntegrations,
  stubTaxonomyEntities,
} from "cypress/support/stubs";

import {
  ADD_SYSTEMS_MANUAL_ROUTE,
  ADD_SYSTEMS_ROUTE,
  INTEGRATION_MANAGEMENT_ROUTE,
  SYSTEM_ROUTE,
} from "~/features/common/nav/routes";
import { RoleRegistryEnum } from "~/types/api";

describe("System management page", () => {
  beforeEach(() => {
    cy.login();
    stubSystemCrud();
    stubPlus(false);
    stubSystemIntegrations();
    stubTaxonomyEntities();
    stubDatasetCrud();
  });

  describe("plus features", () => {
    beforeEach(() => {
      cy.visit(`${SYSTEM_ROUTE}/configure/demo_analytics_system`);
    });

    it("doesn't display the vendor dropdown", () => {
      cy.getByTestId("input-vendor_id").should("not.exist");
    });
  });

  it("Can navigate to the system management page", () => {
    cy.visit("/");
    cy.getByTestId("Data inventory-nav-group").click();
    cy.getByTestId("System inventory-nav-link").click();
    cy.wait("@getSystemsPaginated");
    cy.getByTestId("system-management");
  });

  describe("Can view data", () => {
    beforeEach(() => {
      cy.visit(SYSTEM_ROUTE);
    });

    it("Can render system rows", () => {
      cy.getByTestId("system-fidesctl_system");

      cy.getByTestId("system-fidesctl_system").within(() => {
        cy.getByTestId("edit-btn");
        cy.getByTestId("delete-btn");
      });
      cy.getByTestId("system-demo_analytics_system");
      cy.getByTestId("system-demo_marketing_system");
    });

    it("Can search and filter cards", () => {
      cy.getByTestId("system-search").type("demo m{enter}");

      cy.wait("@getSystemsWithSearch").then((interception) => {
        expect(interception.request.query.search).to.eq("demo m");
      });

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
        cy.intercept("GET", "/api/v1/connection_type*", {
          fixture: "connectors/connection_types.json",
        }).as("getConnectionTypes");
      });

      it("can't create a system with the same name as an existing system", () => {
        cy.visit(ADD_SYSTEMS_MANUAL_ROUTE);
        cy.getByTestId("input-name").type("Demo Analytics System");
        cy.getByTestId("input-description").focus();
        cy.getByTestId("error-name");
      });

      it.skip("Can step through the flow", () => {
        cy.fixture("systems/system.json").then((system) => {
          cy.intercept("GET", "/api/v1/system/*", {
            body: { ...system, privacy_declarations: [] },
          }).as("getDemoSystem");
          // Fill in the describe form based on fixture data
          cy.visit(ADD_SYSTEMS_ROUTE);
          cy.getByTestId("manual-btn").click();
          cy.url().should("contain", ADD_SYSTEMS_MANUAL_ROUTE);
          cy.wait("@getSystemsPaginated");
          cy.getByTestId("input-name").type(system.name);
          cy.getByTestId("input-description").type(system.description);

          cy.getByTestId("save-btn").click();
          cy.wait("@postSystem").then((interception) => {
            const { body } = interception.request;
            expect(body).to.eql({
              administrating_department: "",
              data_security_practices: "",
              dataset_references: [],
              description: system.description,
              does_international_transfers: false,
              exempt_from_privacy_regulations: false,
              fides_key: system.fides_key,
              joint_controller_info: "",
              legal_address: "",
              legal_name: "",
              name: system.name,
              privacy_declarations: [],
              privacy_policy: "",
              processes_personal_data: true,
              requires_data_protection_assessments: false,
              responsibility: [],
              system_type: "",
              tags: [],
              uses_profiling: false,
            });
          });

          // Fill in the privacy declaration form
          cy.getByTestId("tab-Data uses").click();
          cy.getByTestId("add-btn").click();
          cy.wait([
            "@getDataCategories",
            "@getDataSubjects",
            "@getDataUses",
            "@getFilteredDatasets",
            "@getDemoSystem",
          ]);
          cy.getByTestId("declaration-form");
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
              cookies: [],
              id: "",
              features: [],
              impact_assessment_location: "",
              retention_period: "0",
              processes_special_category_data: false,
              data_shared_with_third_parties: false,
            });
          });
        });
      });

      it.skip("can render a warning when there is unsaved data", () => {
        cy.fixture("systems/system.json").then((system) => {
          cy.intercept("GET", "/api/v1/system/*", {
            body: { ...system, privacy_declarations: [] },
          }).as("getDemoSystem");
          cy.visit(ADD_SYSTEMS_MANUAL_ROUTE);
          cy.wait("@getSystemsPaginated");
          cy.getByTestId("input-name").type(system.name);
          cy.getByTestId("input-description").type(system.description);
          cy.getByTestId("save-btn").click();
          cy.wait("@postSystem");

          // start typing a description
          const description = "half formed thought";
          cy.getByTestId("input-description").clear().type(description);
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
          // navigate back and make sure description has the original description
          cy.getByTestId("tab-System information").click();
          cy.getByTestId("input-description").should(
            "have.value",
            system.description,
          );
        });
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

    it("Can't delete a system as a viewer", () => {
      cy.assumeRole(RoleRegistryEnum.VIEWER);
      cy.visit(SYSTEM_ROUTE);
      cy.getByTestId("system-fidesctl_system").within(() => {
        cy.getByTestId("delete-btn").should("not.exist");
      });
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
      cy.fixture("systems/systems.json").then((systems) => {
        cy.intercept("GET", "/api/v1/system/*", {
          body: systems[0],
        }).as("getFidesctlSystem");
      });
      cy.visit(SYSTEM_ROUTE);
      cy.wait("@getUserPermission");
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

    it("Can go to a system's edit page by clicking its card", () => {
      cy.getByTestId("row-0").click();
      cy.url().should("contain", "/systems/configure/fidesctl_system");
    });

    it("Can access integration management page from system edit page", () => {
      cy.visit("/systems/configure/fidesctl_system");
      cy.wait("@getFidesctlSystem");
      cy.getByTestId("integration-page-btn").click();
      cy.url().should("contain", INTEGRATION_MANAGEMENT_ROUTE);
    });

    it("Can persist fields not directly in the form", () => {
      cy.visit("/systems/configure/fidesctl_system");
      cy.wait("@getFidesctlSystem");
      cy.getByTestId("input-name").type("edit");
      cy.getByTestId("save-btn").click();
      cy.wait("@putSystem").then((interception) => {
        const { body } = interception.request;
        expect(body.cookies).to.eql([
          {
            name: "test_cookie",
            path: "/",
            domain: "https://www.example.com",
          },
        ]);
      });
    });

    it.skip("Can go through the edit flow", () => {
      cy.getByTestId("system-fidesctl_system").within(() => {
        cy.getByTestId("edit-btn").click();
      });
      cy.url().should("contain", "/systems/configure/fidesctl_system");

      cy.wait("@getFidesctlSystem");

      // check that the form has the proper values filled in
      cy.getByTestId("input-name").should("have.value", "Fidesctl System");
      cy.getByTestId("input-fides_key").should("have.value", "fidesctl_system");
      cy.getByTestId("input-description").should(
        "have.value",
        "Software that functionally applies Fides.",
      );
      cy.getByTestId("input-administrating_department").should(
        "have.value",
        "Not defined",
      );
      cy.wait("@getFidesctlSystem");

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
      cy.getByTestId("accordion-header-functional.service.improve").click();
      cy.getByTestId("functional.service.improve-form").within(() => {
        cy.getByTestId("input-data_subjects").type(`customer{enter}`);
        cy.getByTestId("save-btn").click();
      });
      cy.wait("@putSystem").then((interception) => {
        const { body } = interception.request;
        expect(body.privacy_declarations.length).to.eql(1);
        expect(body.privacy_declarations[0].data_subjects).to.eql([
          "anonymous_user",
          "customer",
        ]);
      });
      cy.getByTestId("saved-indicator");
    });

    it.skip("Can render and edit extended form fields", () => {
      cy.intercept("GET", "/api/v1/dataset", { fixture: "datasets.json" }).as(
        "getDatasets",
      );
      const system = {
        fides_key: "fidesctl_system",
        system_type: "cool system",

        organization_fides_key: "default_organization",
        administrating_department: "department",
      };
      cy.getByTestId("system-fidesctl_system").within(() => {
        cy.getByTestId("edit-btn").click();
      });

      cy.getByTestId("save-btn").click();
      cy.wait("@putSystem").then((interception) => {
        const { body } = interception.request;
        const {
          privacy_declarations: privacyDeclarations,
          tags,
          fidesctl_meta: fidesctlMeta,
          meta,
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
          administrating_department: system.administrating_department,
        });
      });
    });
  });

  describe("Data uses", () => {
    beforeEach(() => {
      cy.intercept("/api/v1/system/*", {
        fixture: "systems/system.json",
      }).as("getDemoAnalyticsSystem");
      cy.visit(`/${SYSTEM_ROUTE}/configure/demo_analytics_system`);
      cy.wait("@getDemoAnalyticsSystem");
      cy.fixture("systems/system.json").then((system) => {
        const newSystem = { ...system, fides_key: "demo_analytics_system" };
        cy.intercept("PUT", "/api/v1/system*", { body: newSystem }).as(
          "putDemoAnalyticsSystem",
        );
      });

      cy.getByTestId("tab-Data uses").click();
    });

    it("shows data uses in the data use tab", () => {
      cy.getByTestId("row-functional.service.improve");
    });

    it.skip("warns when a data use and processing activity is being added that is already used", () => {
      cy.visit(SYSTEM_ROUTE);
      cy.getByTestId("system-fidesctl_system").within(() => {
        cy.getByTestId("edit-btn").click();
      });
      // "functional.service.improve" and "Store system data." are already being used
      cy.getByTestId("tab-Data uses").click();
      cy.getByTestId("add-btn").click();
      cy.wait(["@getDataCategories", "@getDataSubjects", "@getDataUses"]);
      cy.getByTestId("new-declaration-form").within(() => {
        cy.getByTestId("input-data_use").type(
          `functional.service.improve{enter}`,
        );
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

    // Cannot currently edit the data use or name fields—they have been disabled
    it.skip("warns when a data use is being edited to one that is already used", () => {
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

      cy.getByTestId(`accordion-header-functional.service.improve`);
      cy.getByTestId(`accordion-header-advertising`).click();

      // try to change 'advertising' to 'functional.service.improve' and make their names match
      cy.getByTestId("advertising-form").within(() => {
        cy.getByTestId("input-data_use").type(
          `functional.service.improve{enter}`,
        );
        cy.getByTestId("input-name").clear().type(`Store system data.{enter}`);
        cy.getByTestId("save-btn").click();
      });
      cy.getByTestId("toast-error-msg");
    });

    it.skip("can have multiple of the same data use if the names are different", () => {
      cy.visit(SYSTEM_ROUTE);
      cy.getByTestId("system-fidesctl_system").within(() => {
        cy.getByTestId("edit-btn").click();
      });
      // "functional.service.improve" and "Store system data." are already being used
      // use "functional.service.improve" again but a different name
      cy.getByTestId("tab-Data uses").click();
      cy.getByTestId("add-btn").click();
      cy.wait(["@getDataCategories", "@getDataSubjects", "@getDataUses"]);
      cy.getByTestId("new-declaration-form").within(() => {
        cy.getByTestId("input-data_use").type(
          `functional.service.improve{enter}`,
        );
        cy.getByTestId("input-name").type(`A different description.{enter}`);
        cy.getByTestId("input-data_categories").type(`user.biometric{enter}`);
        cy.getByTestId("input-data_subjects").type(`anonymous{enter}`);
        cy.getByTestId("save-btn").click();
      });
      cy.getByTestId("toast-success-msg");
    });

    it.skip("can edit an accordion data use while persisting a newly added data use", () => {
      cy.visit(`${SYSTEM_ROUTE}/configure/fidesctl_system`);
      cy.getByTestId("tab-Data uses").click();
      cy.getByTestId("add-btn").click();
      cy.wait(["@getDataCategories", "@getDataSubjects", "@getDataUses"]);

      const newDeclaration = {
        id: "pri_bf701ddb-1d05-48f9-913f-b5ff05b8f987",
        name: "Second data use",
        data_categories: ["user.biometric"],
        data_use: "collect",
        data_subjects: ["anonymous"],
        dataset_references: [],
      };
      // We need to update both the PUT and GET fixtures to make sure they return
      // the data use we are adding. This is how we can get the form into a state
      // where there are both "accordion" declarations and the one declaration
      // in the new form
      cy.fixture("systems/system.json").then((system) => {
        const { privacy_declarations: declarations } = system;
        const updatedSystem = {
          ...system,
          fides_key: "fidesctl_system",
          privacy_declarations: [...declarations, newDeclaration],
        };
        cy.intercept("PUT", "/api/v1/system*", {
          body: updatedSystem,
        }).as("putSystemWithAddedDataUse");
        cy.intercept("GET", "/api/v1/system/*", {
          body: updatedSystem,
        }).as("getSystemWithAddedDataUse");
      });

      // Add one data use (one already exists)
      cy.getByTestId("new-declaration-form").within(() => {
        cy.getByTestId("input-data_use").type(
          `${newDeclaration.data_use}{enter}`,
        );
        cy.getByTestId("input-name").type(newDeclaration.name);
        cy.getByTestId("input-data_categories").type(
          `${newDeclaration.data_categories[0]}{enter}`,
        );
        cy.getByTestId("input-data_subjects").type(
          `${newDeclaration.data_subjects[0]}{enter}`,
        );
        cy.getByTestId("save-btn").click();
        cy.wait("@putSystemWithAddedDataUse")
          .its("request.body.privacy_declarations")
          .should("have.length", 2);
        cy.wait("@getSystemWithAddedDataUse");
      });

      // Edit the existing data use
      cy.getByTestId("privacy-declaration-accordion").within(() => {
        cy.getByTestId("accordion-header-functional.service.improve").click();
        // Add a data subject
        cy.getByTestId("input-data_subjects").type(`citizen{enter}`);
        cy.getByTestId("save-btn").click();
        cy.wait("@putSystemWithAddedDataUse")
          .its("request.body.privacy_declarations")
          .should("have.length", 2);
      });
    });

    describe("delete privacy declaration", () => {
      beforeEach(() => {
        cy.intercept("GET", "/api/v1/system/*", {
          fixture: "systems/system.json",
        }).as("getDemoAnalyticsSystem");
        cy.visit(`/${SYSTEM_ROUTE}/configure/demo_analytics_system`);
        cy.wait("@getDemoAnalyticsSystem");
        cy.fixture("systems/system.json").then((system) => {
          const newSystem = { ...system, fides_key: "demo_analytics_system" };
          cy.intercept("PUT", "/api/v1/system*", { body: newSystem }).as(
            "putDemoAnalyticsSystem",
          );
        });

        cy.getByTestId("tab-Data uses").click();
      });

      it("can visit the privacy declaration tab", () => {
        cy.getByTestId("privacy-declarations-table");
        cy.getByTestId("row-functional.service.improve");
      });

      it("can show a modal on deleting a privacy declaration", () => {
        cy.getByTestId("delete-btn").click();
        cy.getByTestId("continue-btn").click();
        cy.getByTestId("toast-success-msg").contains("Data use deleted");
      });

      it.skip("deletes a new privacy declaration", () => {
        cy.getByTestId("add-btn").click();
        cy.wait(["@getDataCategories", "@getDataSubjects", "@getDataUses"]);

        // new form's "delete" btn should be disabled until save
        cy.getByTestId("new-declaration-form").within(() => {
          cy.getByTestId("input-data_use").type(`collect{enter}`);
          cy.getByTestId("input-data_categories").type(`user.biometric{enter}`);
          cy.getByTestId("input-data_subjects").type(`anonymous{enter}`);
          cy.getByTestId("delete-btn").should("be.disabled");
          cy.getByTestId("save-btn").click();
          cy.wait("@putFidesSystem");
          cy.getByTestId("delete-btn").should("be.enabled");
          // now go through delete flow
          cy.getByTestId("delete-btn").click();
        });
        cy.getByTestId("continue-btn").click();
        cy.wait("@putFidesSystem");
        cy.getByTestId("toast-success-msg").contains("Data use deleted");
      });

      it.skip("deletes an accordion privacy declaration", () => {
        cy.getByTestId("accordion-header-functional.service.improve").click();
        cy.getByTestId("functional.service.improve-form").within(() => {
          cy.getByTestId("delete-btn").click();
        });
        cy.getByTestId("continue-btn").click();
        cy.wait("@putFidesSystem").then((interception) => {
          const { body } = interception.request;
          expect(body.privacy_declarations.length).to.eql(1);
          expect(
            body.privacy_declarations[0].data_use !==
              "functional.service.improve",
          );
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
        cy.getByTestId("edit-btn").click();
      });
      cy.getByTestId("tab-Data flow").click();
    });

    it("Can navigate to the data flow tab", () => {
      cy.getByTestId("data-flow-accordion").should("exist");
    });

    it("Can open both accordion items", () => {
      cy.getByTestId("data-flow-accordion").within(() => {
        cy.getByTestId("data-flow-button-Source").click();
        cy.getByTestId("data-flow-panel-Source").should("exist");
        cy.getByTestId("data-flow-button-Destination").click();
        cy.getByTestId("data-flow-panel-Destination").should("exist");
      });
    });
  });
});
