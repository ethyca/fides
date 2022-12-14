import { USER_PRIVILEGES } from "~/constants";

describe("User Authentication", () => {
  describe("when the user not logged in", () => {
    it("redirects them to the login page", () => {
      cy.visit("/");
      cy.location("pathname").should("eq", "/login");

      cy.visit("/user-management");
      cy.location("pathname").should("eq", "/login");

      cy.visit("/system");
      cy.location("pathname").should("eq", "/login");

      cy.getByTestId("Login");
    });

    it("lets them log in", () => {
      cy.visit("/login");
      cy.getByTestId("Login");

      cy.intercept("GET", "/api/v1/system", { body: [] });
      cy.fixture("login.json").then((body) => {
        cy.intercept("POST", "/api/v1/login", body).as("postLogin");
        cy.intercept("/api/v1/user/*/permission", {
          body: {
            id: body.user_data.id,
            user_id: body.user_data.id,
            scopes: USER_PRIVILEGES.map((up) => up.scope),
          },
        }).as("getUserPermission");
      });

      cy.get("#email").type("cypress-user@ethyca.com");
      cy.get("#password").type("FakePassword123!{Enter}");

      cy.getByTestId("nav-bar");
    });
  });

  describe("when the user is logged in", () => {
    beforeEach(() => {
      cy.login();
    });

    it("lets them navigate to protected routes", () => {
      cy.visit("/");
      cy.getByTestId("Privacy Requests");

      cy.visit("/user-management");
      cy.getByTestId("User Management");

      cy.visit("/system");
      cy.getByTestId("Systems");
    });

    it("lets them log out", () => {
      cy.visit("/system");
      cy.getByTestId("Systems");

      cy.intercept("POST", "/api/v1/logout", {
        statusCode: 204,
      });

      cy.getByTestId("header-menu-button").click();
      cy.getByTestId("header-menu-sign-out").click();

      cy.location("pathname").should("eq", "/login");
      cy.getByTestId("Login");
    });

    it("/login redirects to the onboarding flow if the user has no systems", () => {
      cy.intercept("GET", "/api/v1/system", { body: [] });
      cy.visit("/login");
      cy.getByTestId("setup");
    });

    it("/login redirects to the systems page if the user has systems", () => {
      cy.intercept("GET", "/api/v1/system", { fixture: "systems.json" }).as(
        "getSystems"
      );
      cy.visit("/login");
      cy.wait("@getSystems");
      cy.getByTestId("system-management");
    });
  });
});
