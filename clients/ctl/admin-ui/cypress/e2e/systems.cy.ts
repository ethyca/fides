describe("System management page", () => {
  beforeEach(() => {
    cy.intercept("GET", "/api/v1/system", { fixture: "systems.json" }).as(
      "getSystems"
    );
  });

  it("Can navigate to the system management page", () => {
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
      // Uncomment when we enable the more actions button
      // cy.getByTestId("system-fidesctl_system").within(() => {
      //   cy.getByTestId("more-btn").click();
      //   cy.getByTestId("edit-btn");
      //   cy.getByTestId("delete-btn");
      // });
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
      cy.intercept("POST", "/api/v1/system", { fixture: "system.json" }).as(
        "postSystem"
      );
      cy.intercept("GET", "/api/v1/system/*", { fixture: "system.json" }).as(
        "getSystem"
      );
      cy.intercept("PUT", "/api/v1/system*", { fixture: "system.json" }).as(
        "putSystem"
      );
    });
    describe("Create a system via yaml", () => {
      it("Can insert yaml and post", () => {
        cy.visit("/system/new");
        cy.getByTestId("upload-yaml-btn").click();
        cy.fixture("system.json").then((system) => {
          const systemAsString = JSON.stringify(system);
          // Cypress doesn't have a native "paste" command, so instead do change the value directly
          // (.type() is too slow, even with 0 delay)
          cy.getByTestId("input-yaml")
            .click()
            .invoke("val", systemAsString)
            .trigger("change");
          // type just one space character to make sure the text field triggers Formik's handlers
          cy.getByTestId("input-yaml").type(" ");

          cy.getByTestId("submit-yaml-btn").click();
          cy.wait("@postSystem").then((interception) => {
            const { body } = interception.request;
            expect(body).to.eql(system);
          });

          // should navigate to the created system
          cy.getByTestId("toast-success-msg");
          cy.url().should("contain", `system`);
        });
      });

      it("Can render errors in yaml", () => {
        cy.intercept("POST", "/api/v1/system", {
          statusCode: 422,
          body: {
            detail: [
              {
                loc: ["body", "fides_key"],
                msg: "field required",
                type: "value_error.missing",
              },
              {
                loc: ["body", "system_type"],
                msg: "field required",
                type: "value_error.missing",
              },
            ],
          },
        }).as("postSystem");
        cy.visit("/system/new");
        cy.getByTestId("upload-yaml-btn").click();

        // invalid system with missing fields
        cy.getByTestId("input-yaml")
          .clear()
          .type("valid yaml that is not a system");
        cy.getByTestId("submit-yaml-btn").click();
        cy.getByTestId("error-yaml").should("contain", "field required");
      });
    });

    describe("Create a system manually", () => {
      it("Can step through the flow", () => {
        cy.fixture("system.json").then((system) => {
          // Fill in the describe form based on fixture data
          cy.visit("/system/new");
          cy.getByTestId("manually-generate-btn").click();
          cy.url().should("contain", "/system/new/configure");
          cy.getByTestId("input-name").type(system.name);
          cy.getByTestId("input-fides_key").type(system.fides_key);
          cy.getByTestId("input-description").type(system.description);
          cy.getByTestId("input-system_type").type(system.system_type);
          system.tags.forEach((tag) => {
            cy.getByTestId("input-tags").type(`${tag}{enter}`);
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
            });
          });

          // Fill in the privacy declaration form
          const declaration = {
            name: "my declaration",
            data_categories: ["user.biometric", "user.contact"],
            data_use: "advertising",
            data_subjects: ["citizen_voter", "consultant"],
            data_qualifier: "aggregated",
          };
          cy.getByTestId("input-name").type(declaration.name);
          declaration.data_categories.forEach((dc) => {
            cy.getByTestId("input-data_categories").type(`${dc}{enter}`);
          });
          cy.getByTestId("input-data_use").type(
            `${declaration.data_use}{enter}`
          );
          declaration.data_subjects.forEach((ds) => {
            cy.getByTestId("input-data_subjects").type(`${ds}{enter}`);
          });
          cy.getByTestId("input-data_qualifier").type(
            `${declaration.data_qualifier}{enter}`
          );
          cy.getByTestId("confirm-btn").click();
          cy.wait("@putSystem").then((interception) => {
            const { body } = interception.request;
            expect(body.privacy_declarations[1]).to.eql(declaration);
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
          // Open up the privacy declaration
          cy.getByTestId(
            "declaration-Analyze customer behaviour for improvements."
          ).click();
          const reviewDeclaration = system.privacy_declarations[0];
          reviewDeclaration.data_categories.forEach((dc) => {
            cy.getByTestId("declaration-categories").contains(dc);
          });
          cy.getByTestId("declaration-use").within(() => {
            cy.get("input").should("have.value", reviewDeclaration.data_use);
          });
          reviewDeclaration.data_subjects.forEach((ds) => {
            cy.getByTestId("declaration-subjects").contains(ds);
          });
          cy.getByTestId("declaration-qualifier").within(() => {
            cy.get("input").should(
              "have.value",
              reviewDeclaration.data_qualifier
            );
          });
          cy.getByTestId("confirm-btn").click();

          // Success page
          cy.getByTestId("success-page-heading").should(
            "contain",
            `${system.name} successfully registered`
          );
          cy.getByTestId("continue-btn").click();
          cy.url().should("match", /system$/);
        });
      });
    });
  });
});
