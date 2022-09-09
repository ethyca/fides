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
    it("Can create a system via yaml", () => {
      cy.intercept("POST", "/api/v1/system", { fixture: "system.json" }).as(
        "postSystem"
      );
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
});
