import { SYSTEM_ROUTE } from "~/constants";

describe("User Authentication", () => {
  describe("when the user not logged in", () => {
    it("redirects them to the login page", () => {
      cy.visit("/");
      cy.location("pathname").should("eq", "/login");

      cy.visit("/user-management");
      cy.location("pathname").should("eq", "/login");

      cy.visit(SYSTEM_ROUTE);
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
          fixture: "user-management/permissions.json",
        }).as("getUserPermission");
      });

      cy.get("#email").type("cypress-user@ethyca.com");
      cy.get("#password").type("FakePassword123!{Enter}");

      cy.getByTestId("Home");
    });
  });

  describe("when the user is logged in", () => {
    beforeEach(() => {
      cy.login();
    });

    it("lets them navigate to protected routes", () => {
      cy.visit("/");
      cy.getByTestId("Home");

      cy.visit("/user-management");
      cy.getByTestId("User Management");

      cy.visit(SYSTEM_ROUTE);
      cy.getByTestId("Systems");
    });

    it("lets them log out", () => {
      cy.visit(SYSTEM_ROUTE);
      cy.getByTestId("Systems");

      cy.intercept("POST", "/api/v1/logout", {
        statusCode: 204,
      });

      cy.getByTestId("header-menu-button").click();
      cy.getByTestId("header-menu-sign-out").click();

      cy.location("pathname").should("eq", "/login");
      cy.getByTestId("Login");
    });

    it("/login redirects to the Home page", () => {
      cy.visit("/login");
      cy.location("pathname").should("eq", "/");
    });
  });
});
