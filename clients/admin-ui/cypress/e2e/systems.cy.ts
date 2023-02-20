import { stubSystemCrud, stubTaxonomyEntities } from "cypress/support/stubs";

describe("System management page", () => {
  beforeEach(() => {
    cy.login();
    cy.intercept("GET", "/api/v1/system", { fixture: "systems.json" }).as(
      "getSystems"
    );
  });

  // TODO: Update Cypress test to reflect the nav bar 2.0
  it.skip("Can navigate to the system management page", () => {
    cy.visit("/");
    cy.getByTestId("nav-link-Systems").click();
    cy.wait("@getSystems");
    cy.getByTestId("system-management");
  });

  describe("Can view data", () => {
    beforeEach(() => {
      cy.visit("/system");
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
      });

      it("Can step through the flow", () => {
        cy.fixture("system.json").then((system) => {
          // Fill in the describe form based on fixture data
          cy.visit("/add-systems");
          cy.getByTestId("manual-btn").click();
          cy.url().should("contain", "/add-systems");
          cy.wait("@getSystems");
          cy.getByTestId("input-name").type(system.name);
          cy.getByTestId("input-fides_key").type(system.fides_key);
          cy.getByTestId("input-description").type(system.description);
          cy.getByTestId("input-system_type").type(system.system_type);
          system.tags.forEach((tag) => {
            cy.getByTestId("input-tags").type(`${tag}{enter}`);
          });
          cy.getByTestId("input-system_dependencies").click();
          cy.getByTestId("input-system_dependencies").within(() => {
            cy.contains("Demo Analytics System").click();
          });

          cy.getByTestId("confirm-btn").click();
          cy.wait("@postSystem").then((interception) => {
            const { body } = interception.request;
            expect(body).to.eql({
              name: system.name,
              organization_fides_key: system.organization_fides_key,
              fides_key: system.fides_key,
              description: system.description,
              system_type: system.system_type,
              tags: system.tags,
              privacy_declarations: [],
              third_country_transfers: [],
              system_dependencies: ["demo_analytics_system"],
            });
          });

          // Fill in the privacy declaration form
          cy.wait("@getDataCategories");
          cy.wait("@getDataQualifiers");
          cy.wait("@getDataSubjects");
          cy.wait("@getDataUses");
          cy.getByTestId("privacy-declaration-form");
          const declaration = system.privacy_declarations[0];
          cy.getByTestId("input-name").type(declaration.name);
          declaration.data_categories.forEach((dc) => {
            cy.getByTestId("input-data_categories").type(`${dc}{enter}`);
          });
          cy.getByTestId("input-data_use").click();
          cy.getByTestId("input-data_use").within(() => {
            cy.contains(declaration.data_use).click();
          });

          declaration.data_subjects.forEach((ds) => {
            cy.getByTestId("input-data_subjects").type(`${ds}{enter}`);
          });
          cy.getByTestId("input-data_qualifier").click();
          cy.getByTestId("input-data_qualifier").within(() => {
            cy.contains(declaration.data_qualifier).click();
          });
          cy.getByTestId("add-btn").click();
          cy.getByTestId("next-btn").click();
          cy.wait("@putSystem").then((interception) => {
            const { body } = interception.request;
            expect(body.privacy_declarations[0]).to.eql({
              ...declaration,
              dataset_references: [],
            });
          });

          // Now at the Review stage
          cy.getByTestId("review-heading");
          cy.getByTestId("review-System name").contains(system.name);
          cy.getByTestId("review-System key").contains(system.fides_key);
          cy.getByTestId("review-System description").contains(
            system.description
          );
          cy.getByTestId("review-System type").contains(system.system_type);
          system.tags.forEach((tag) => {
            cy.getByTestId("review-System tags").contains(tag);
          });
          system.system_dependencies.forEach((dep) => {
            cy.getByTestId("review-System dependencies").contains(dep);
          });
          // Open up the privacy declaration
          cy.getByTestId(
            "declaration-Analyze customer behaviour for improvements."
          ).click();
          const reviewDeclaration = system.privacy_declarations[0];
          reviewDeclaration.data_categories.forEach((dc) => {
            cy.getByTestId("declaration-Data categories").contains(dc);
          });
          cy.getByTestId("declaration-Data use").contains(
            reviewDeclaration.data_use
          );
          reviewDeclaration.data_subjects.forEach((ds) => {
            cy.getByTestId("declaration-Data subjects").contains(ds);
          });
          cy.getByTestId("declaration-Data qualifier").contains(
            reviewDeclaration.data_qualifier
          );

          cy.getByTestId("confirm-btn").click();

          // Success page
          cy.getByTestId("success-page-heading").should(
            "contain",
            `${system.name} successfully registered`
          );
          cy.getByTestId("finish-btn").click();
          cy.url().should("match", /system$/);
        });
      });
    });
  });

  describe("Can delete a system", () => {
    beforeEach(() => {
      stubSystemCrud();
    });

    it("Can delete a system from its card", () => {
      cy.visit("/system");
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
      cy.visit("/system");
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
      cy.visit("/system");
    });

    it("Can go through the edit flow", () => {
      cy.getByTestId("system-fidesctl_system").within(() => {
        cy.getByTestId("more-btn").click();
        cy.getByTestId("edit-btn").click();
      });
      cy.url().should("contain", "/system/configure");

      // check that the form has the proper values filled in
      cy.getByTestId("input-name").should("have.value", "Fidesctl System");
      cy.getByTestId("input-fides_key").should("have.value", "fidesctl_system");
      cy.getByTestId("input-description").should(
        "have.value",
        "Software that functionally applies Fides."
      );
      cy.getByTestId("input-system_type").should("have.value", "Service");
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
      cy.getByTestId("confirm-btn").click();
      cy.wait("@putSystem").then((interception) => {
        const { body } = interception.request;
        expect(body.joint_controller.name).to.eql(controllerName);
      });

      // add another privacy declaration
      const secondName = "Second declaration";
      cy.getByTestId("privacy-declaration-form");
      cy.getByTestId("input-name").type(secondName);
      cy.getByTestId("input-data_categories").type(`user.biometric{enter}`);
      cy.getByTestId("input-data_use").type(`advertising{enter}`);
      cy.getByTestId("input-data_subjects").type(`anonymous{enter}`);
      cy.getByTestId("add-btn").click();

      // edit the existing declaration
      const newName = "Store a lot of system data";
      cy.getByTestId("declaration-Store system data.")
        .click()
        .within(() => {
          cy.getByTestId("edit-declaration-btn").click();
          cy.getByTestId("input-name").clear().type(newName);
          cy.getByTestId("confirm-edit-btn").click();
        });
      cy.getByTestId(`declaration-${newName}`);
      cy.getByTestId(`declaration-${secondName}`);

      cy.getByTestId("next-btn").click();
      cy.wait("@putSystem").then((interception) => {
        const { body } = interception.request;
        expect(body.privacy_declarations.length).to.eql(2);
        expect(body.privacy_declarations[0].name).to.eql(newName);
        expect(body.privacy_declarations[1].name).to.eql(secondName);
      });
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

      cy.getByTestId("confirm-btn").click();
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

      // Add privacy declaration form
      cy.wait("@getDataCategories");
      cy.wait("@getDataQualifiers");
      cy.wait("@getDataSubjects");
      cy.wait("@getDataUses");
      cy.wait("@getDatasets");
      cy.getByTestId("privacy-declaration-form");
      const declaration = {
        name: "my declaration",
        data_categories: ["user.biometric", "user.contact"],
        data_use: "advertising",
        data_subjects: ["citizen_voter", "consultant"],
        dataset_references: ["demo_users_dataset_2"],
      };
      cy.getByTestId("input-name").type(declaration.name);
      declaration.data_categories.forEach((dc) => {
        cy.getByTestId("input-data_categories").type(`${dc}{enter}`);
      });
      cy.getByTestId("input-data_use").type(`${declaration.data_use}{enter}`);
      declaration.data_subjects.forEach((ds) => {
        cy.getByTestId("input-data_subjects").type(`${ds}{enter}`);
      });
      cy.getByTestId("input-dataset_references").click();
      cy.getByTestId("input-dataset_references").within(() => {
        cy.contains("Demo Users Dataset 2").click();
      });
      cy.getByTestId("add-btn").click();
      cy.getByTestId("next-btn").click();
      cy.wait("@putSystem").then((interception) => {
        const { body } = interception.request;
        expect(body.privacy_declarations[1]).to.eql(declaration);
      });

      // Now at the Review stage
      cy.getByTestId("review-heading");
      cy.getByTestId("review-Data responsibility title").contains("Controller");
      cy.getByTestId("review-Administrating department").contains(
        "Engineering"
      );
      cy.getByTestId("review-Geographic location").contains("USA");
      cy.getByTestId("review-Geographic location").contains("CAN");
      cy.getByTestId("review-Joint controller").within(() => {
        cy.getByTestId("review-Name").contains("Sally Controller");
      });
      cy.getByTestId("review-Data protection impact assessment").within(() => {
        cy.getByTestId("review-Is required").contains("Yes");
        cy.getByTestId("review-Progress").contains("Complete");
        cy.getByTestId("review-Link").contains(
          "https://example.org/analytics_system_data_protection_impact_assessment"
        );
      });
    });
  });
});
