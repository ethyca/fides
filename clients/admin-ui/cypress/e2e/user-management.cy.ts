import { utf8ToB64 } from "~/features/common/utils";

const CYPRESS_USER_ID = "123";
const USER_1_ID = "fid_ee8f54ce-19f7-4640-b311-1cc1e77e7166";

describe("User management", () => {
  beforeEach(() => {
    cy.login();
    cy.intercept("/api/v1/user?*", {
      fixture: "user-management/users.json",
    }).as("getAllUsers");
    cy.intercept("/api/v1/user/*", { fixture: "user-management/user.json" }).as(
      "getUser"
    );
    cy.intercept("/api/v1/user/*/permission", {
      fixture: "user-management/permissions.json",
    }).as("getPermissions");
  });

  describe("View users", () => {
    it("can view all users", () => {
      cy.visit("/user-management");
      cy.wait("@getAllUsers");
      const numUsers = 4;
      cy.getByTestId("user-management-table")
        .find("tbody > tr")
        .then((rows) => {
          expect(rows.length).to.eql(numUsers);
        });
    });
  });

  describe("Password management", () => {
    it("can update their own password", () => {
      cy.intercept("POST", "/api/v1/user/*/reset-password", {
        fixture: "user-management/user.json",
      }).as("postResetPassword");

      const oldPassword = "g00dPassword!";
      const newPassword = "b3tt3rPassword!";
      cy.visit(`/user-management/profile/${CYPRESS_USER_ID}`);
      cy.wait("@getUser");
      cy.wait("@getPermissions");
      cy.getByTestId("update-password-btn").click();
      cy.getByTestId("input-oldPassword").type(oldPassword);
      cy.getByTestId("input-newPassword").type(newPassword);
      cy.getByTestId("submit-btn").click();

      cy.wait("@postResetPassword").then((interception) => {
        const { body, url } = interception.request;
        expect(url).to.contain(CYPRESS_USER_ID);
        expect(body).to.eql({
          old_password: utf8ToB64(oldPassword),
          new_password: utf8ToB64(newPassword),
        });
      });
    });

    it("cannot update another user's password", () => {
      cy.intercept("/api/v1/user/*", {
        body: {
          id: USER_1_ID,
          username: "user_1",
          created_at: "2023-01-26T16:16:49.575653+00:00",
          first_name: "User",
          last_name: "One",
        },
      }).as("getOtherUser");
      cy.visit(`/user-management/profile/${USER_1_ID}`);
      cy.wait("@getOtherUser");
      cy.wait("@getPermissions");
      cy.getByTestId("update-password-btn").should("not.exist");
    });

    it("can reset another user's password", () => {
      const newPassword = "b3tt3rPassword!";
      cy.intercept("/api/v1/user/*", {
        body: {
          id: USER_1_ID,
          username: "user_1",
          created_at: "2023-01-26T16:16:49.575653+00:00",
          first_name: "User",
          last_name: "One",
        },
      }).as("getOtherUser");
      cy.intercept("POST", "/api/v1/user/*/force-reset-password", {
        fixture: "user-management/user.json",
      }).as("postForceResetPassword");

      cy.visit(`/user-management/profile/${USER_1_ID}`);
      cy.wait("@getOtherUser");
      cy.wait("@getPermissions");
      cy.getByTestId("reset-password-btn").click();
      cy.getByTestId("input-password").type(newPassword);
      cy.getByTestId("input-passwordConfirmation").type(newPassword);
      cy.getByTestId("submit-btn").click();

      cy.wait("@postForceResetPassword").then((interception) => {
        const { body, url } = interception.request;
        expect(url).to.contain(USER_1_ID);
        expect(body).to.eql({
          new_password: utf8ToB64(newPassword),
        });
      });
    });

    it("only show reset button if user has the scope for it", () => {
      cy.fixture("user-management/permissions.json").then((permissions) => {
        cy.intercept(`/api/v1/user/${CYPRESS_USER_ID}/permission`, {
          body: {
            ...permissions,
            scopes: permissions.scopes.filter(
              (scope) => scope !== "user:password-reset"
            ),
          },
        }).as("getUserPermissionWithoutPasswordReset");
      });
      cy.intercept("/api/v1/user/*", {
        body: {
          id: USER_1_ID,
          username: "user_1",
          created_at: "2023-01-26T16:16:49.575653+00:00",
          first_name: "User",
          last_name: "One",
        },
      }).as("getOtherUser");

      cy.visit(`/user-management/profile/${USER_1_ID}`);
      cy.wait("@getOtherUser");
      cy.wait("@getUserPermissionWithoutPasswordReset");
      cy.wait("@getPermissions");
      cy.getByTestId("reset-password-btn").should("not.exist");
    });
  });
});
