import {
  stubLogout,
  stubOpenIdProviders,
  stubUserManagement,
} from "cypress/support/stubs";

import { SYSTEM_ROUTE } from "~/features/common/nav/routes";

describe("User Authentication", () => {
  beforeEach(() => {
    stubOpenIdProviders();
  });
  const login = () => {
    cy.fixture("login.json").then((body) => {
      cy.intercept("POST", "/api/v1/login", body).as("postLogin");
      cy.intercept("/api/v1/user/*/permission", {
        fixture: "user-management/permissions.json",
      }).as("getUserPermission");
    });

    cy.getByTestId("input-username").type("cypress-user@ethyca.com");
    cy.getByTestId("input-password").type("FakePassword123!{Enter}");
  };
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
      login();

      cy.getByTestId("Home");
    });

    it("can persist URL after logging in", () => {
      stubUserManagement();
      cy.visit("/user-management");
      cy.location("pathname").should("eq", "/login");
      cy.location("search").should("eq", "?redirect=%2Fuser-management");

      // Now log in
      login();
      cy.location("pathname").should("eq", "/user-management");
    });
  });

  describe("when the user is logged in", () => {
    beforeEach(() => {
      cy.login();
    });

    it("lets them navigate to protected routes", () => {
      stubUserManagement();
      cy.visit("/");
      cy.getByTestId("Home");

      cy.visit("/user-management");
      cy.getByTestId("User Management");

      cy.visit(SYSTEM_ROUTE);
      cy.getByTestId("system-management");
    });

    it("lets them log out", () => {
      cy.visit(SYSTEM_ROUTE);
      cy.getByTestId("system-management");

      stubLogout();
      cy.getByTestId("header-menu-button").click();
      cy.getByTestId("header-menu-sign-out").click({ force: true });

      cy.location("pathname").should("eq", "/login");
      cy.getByTestId("Login");
    });

    it("/login redirects to the Home page", () => {
      cy.visit("/login");
      cy.location("pathname").should("eq", "/");
    });
  });

  describe("invited user", () => {
    beforeEach(() => {
      cy.intercept("/api/v1/user/*/permission", {
        fixture: "user-management/permissions.json",
      }).as("getUserPermission");
      cy.fixture("login.json").then((body) => {
        cy.intercept("POST", "/api/v1/user/accept-invite*", body).as(
          "postAcceptInvite",
        );
      });
      cy.intercept("GET", "/api/v1/user/validate-invite*", {
        body: { valid: true, reason: null },
      }).as("validateInvite");
    });
    it("can prefill email and render different copy for an invited user", () => {
      const data = { username: "testuser", invite_code: "123" };
      const newPassword = "FakePassword123!";
      cy.visit("/login", {
        qs: data,
      });
      cy.wait("@validateInvite");
      cy.getByTestId("input-username").should("be.disabled");
      cy.getByTestId("input-username").should("have.value", data.username);
      cy.get("label").contains("Set new password");
      cy.getByTestId("input-password").type(newPassword);
      cy.get("button").contains("Setup user").click();
      cy.wait("@postAcceptInvite").then((interception) => {
        const { body, url } = interception.request;
        expect(url).to.contain(data.invite_code);
        expect(url).to.contain(data.username);
        expect(body).to.eql({ new_password: newPassword });
      });
      cy.getByTestId("Home");
    });

    it("shows an expired-link message and no password form when the invite is expired", () => {
      cy.intercept("GET", "/api/v1/user/validate-invite*", {
        body: { valid: false, reason: "expired" },
      }).as("validateInviteExpired");
      cy.visit("/login", {
        qs: { username: "testuser", invite_code: "expired" },
      });
      cy.wait("@validateInviteExpired");
      cy.getByTestId("invalid-token-message").should(
        "contain",
        "This link has expired",
      );
      cy.getByTestId("input-password").should("not.exist");
      cy.getByTestId("return-to-login-btn").should("be.visible");
    });

    it("shows an invalid-link message when the invite was already used", () => {
      cy.intercept("GET", "/api/v1/user/validate-invite*", {
        body: { valid: false, reason: "invalid" },
      }).as("validateInviteInvalid");
      cy.visit("/login", {
        qs: { username: "testuser", invite_code: "used" },
      });
      cy.wait("@validateInviteInvalid");
      cy.getByTestId("invalid-token-message").should(
        "contain",
        "This link is no longer valid",
      );
      cy.getByTestId("input-password").should("not.exist");
    });
  });

  describe("password reset user", () => {
    it("shows an expired-link message and a request-new-link CTA when the reset token is expired", () => {
      cy.intercept("GET", "/api/v1/user/validate-reset-token*", {
        body: { valid: false, reason: "expired" },
      }).as("validateResetExpired");
      cy.visit("/login", {
        qs: { username: "testuser", reset_token: "expired" },
      });
      cy.wait("@validateResetExpired");
      cy.getByTestId("invalid-token-message").should(
        "contain",
        "This link has expired",
      );
      cy.getByTestId("input-password").should("not.exist");
      cy.getByTestId("request-new-link-btn").should("be.visible");
    });
  });
});
