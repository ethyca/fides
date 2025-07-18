import {
  stubOpenIdProviders,
  stubPlus,
  stubUserManagement,
} from "cypress/support/stubs";

import { utf8ToB64 } from "~/features/common/utils";
import { RoleRegistryEnum } from "~/types/api";

const CYPRESS_USER_ID = "123";
const USER_1_ID = "fid_ee8f54ce-19f7-4640-b311-1cc1e77e7166";

describe("User management", () => {
  beforeEach(() => {
    cy.intercept("GET", "/api/v1/messaging/email-invite/status", {
      body: {
        enabled: false,
      },
    });
    stubOpenIdProviders();
    stubUserManagement();
    cy.login();
    cy.intercept("/api/v1/user/*/permission", {
      fixture: "user-management/permissions.json",
    }).as("getPermissions");
  });

  describe("permissions", () => {
    describe("viewers", () => {
      beforeEach(() => {
        cy.assumeRole(RoleRegistryEnum.VIEWER);
        cy.intercept("PUT", "/api/v1/user/*", {
          fixture: "user-management/user.json",
        }).as("updateUser");
      });

      it("cannot add new users", () => {
        cy.visit("/user-management");
        cy.wait("@getAllUsers");
        cy.getByTestId("add-new-user-btn").should("not.exist");
      });

      it("can access their own profile but not their permissions", () => {
        cy.visit("/user-management");
        cy.wait("@getAllUsers");
        cy.getByTestId(`row-${CYPRESS_USER_ID}`).click();
        cy.url().should(
          "contain",
          `/user-management/profile/${CYPRESS_USER_ID}`,
        );

        // can edit their name
        cy.getByTestId("input-first_name").type("edit");
        cy.getByTestId("save-user-btn").click();
        cy.wait("@updateUser").then((interception) => {
          const { body } = interception.request;
          expect(body.first_name).to.equal("Cypressedit");
        });

        cy.getAntTab("Permissions").should(
          "have.attr",
          "aria-disabled",
          "true",
        );
      });

      it("cannot access another user's profile", () => {
        cy.visit("/user-management");
        cy.wait("@getAllUsers");

        // try via clicking the row
        cy.getByTestId(`row-${USER_1_ID}`).click();
        cy.url().should("not.contain", "profile");
        // should still be on the table view
        cy.getByTestId("user-management-table");
      });

      it("cannot go directly to a different user's profile", () => {
        cy.fixture("user-management/user.json").then((user) => {
          // have to change the user ID so that we are going to a different user
          const user1 = { ...user, id: USER_1_ID };
          cy.intercept("/api/v1/user/*", { body: user1 }).as("getUser1");
        });
        cy.visit(`/user-management/profile/${USER_1_ID}`);
        // should be redirected to the home page
        cy.url().should("eq", "http://localhost:3000/");
      });
    });
  });

  describe("View users", () => {
    it("can view all users", () => {
      cy.intercept("/api/v1/user/*/system-manager", {
        fixture: "systems/systems.json",
      });
      cy.visit("/user-management");
      cy.wait("@getAllUsers");
      const numUsers = 4;
      cy.getByTestId("user-management-table")
        .find("tbody > tr")
        .then((rows) => {
          expect(rows.length).to.eql(numUsers);
        })
        .first();
      cy.getByTestId("user-systems-badge");
      cy.contains("4");
    });

    it("can see invite sent field", () => {
      cy.visit("/user-management");
      cy.wait("@getAllUsers");
      cy.getByTestId(`row-${USER_1_ID}`).within(() => {
        cy.getByTestId("invite-sent-badge");
      });
      cy.getByTestId(`row-${CYPRESS_USER_ID}`).within(() => {
        cy.getByTestId("invite-sent-badge").should("not.exist");
      });
    });
  });

  describe("Create users", () => {
    it("can set a user's password if email messaging is not configured", () => {
      cy.visit(`/user-management/new`);
      cy.getByTestId("input-password");
    });

    it("cannot set a user's password if email messaging is enabled", () => {
      cy.intercept("GET", "/api/v1/messaging/email-invite/status", {
        body: {
          enabled: true,
        },
      });
      cy.visit(`/user-management/new`);
      cy.getByTestId("input-email_address");
      cy.getByTestId("input-password").should("not.exist");
    });

    it("shows password login toggle when Plus and SSO are enabled with username/password login allowed", () => {
      stubPlus(true);

      // Setup: Enable SSO providers, and username/password login option
      cy.intercept("GET", "/api/v1/openid/provider", {
        body: [{ id: "test-provider" }],
      }).as("getOpenIdProviders");

      cy.intercept("GET", "/api/v1/config*", {
        body: {
          plus_security_settings: { allow_username_password_login: true },
        },
      }).as("getConfigSettings");

      // Intercept messaging status to ensure email invite is disabled
      cy.intercept("GET", "/api/v1/messaging/email-invite/status", {
        body: {
          enabled: false, // Ensure inviteUsersViaEmail = false
        },
      }).as("getEmailInviteStatus");

      cy.log("Visiting user management new page");
      cy.visit("/user-management/new");

      // Wait for key API calls to complete
      cy.wait("@getOpenIdProviders");
      cy.wait("@getConfigSettings");
      cy.wait("@getEmailInviteStatus");

      // Check for the toggle
      cy.getByTestId("input-password_login_enabled").should("exist");
    });

    it("hides password login toggle when Plus is disabled", () => {
      // Setup: Disable Plus feature
      stubPlus(false);

      // Intercept messaging status to ensure email invite is disabled
      cy.intercept("GET", "/api/v1/messaging/email-invite/status", {
        body: {
          enabled: false,
        },
      }).as("getEmailInviteStatus");

      cy.visit("/user-management/new");
      cy.wait("@getEmailInviteStatus");

      // The toggle should not exist when Plus is disabled
      cy.getByTestId("input-password_login_enabled").should("not.exist");

      // But the password field should always exist when Plus is disabled
      cy.getByTestId("input-password").should("exist");
    });

    it("can create a user with password login disabled", () => {
      // Setup Plus with SSO and username/password login allowed
      stubPlus(true);
      cy.intercept("GET", "/api/v1/openid/provider", {
        body: [{ id: "test-provider" }],
      }).as("getOpenIdProviders");
      cy.intercept("GET", "/api/v1/config?api_set=false", {
        body: {
          plus_security_settings: { allow_username_password_login: true },
        },
      }).as("getConfigSettings");

      // Intercept messaging status to ensure email invite is disabled
      cy.intercept("GET", "/api/v1/messaging/email-invite/status", {
        body: {
          enabled: false,
        },
      }).as("getEmailInviteStatus");

      // Setup intercept for POST request
      cy.intercept("POST", "/api/v1/user", {
        statusCode: 200,
        body: {
          id: "new-user-123",
          username: "testuser",
          email_address: "test@example.com",
          first_name: "Test",
          last_name: "User",
        },
      }).as("createUser");

      cy.visit("/user-management/new");
      cy.wait("@getOpenIdProviders");
      cy.wait("@getConfigSettings");
      cy.wait("@getEmailInviteStatus");

      // Verify toggle exists and ensure it's initially checked (enabled)
      cy.getByTestId("input-password_login_enabled").should("exist");
      cy.getByTestId("input-password_login_enabled").click();
      cy.getByTestId("input-password").should("exist");
      cy.getByTestId("input-password_login_enabled").click();

      // Password field should be hidden once toggle is disabled
      cy.getByTestId("input-password").should("not.exist");

      // Fill form
      cy.getByTestId("input-username").type("testuser");
      cy.getByTestId("input-email_address").type("test@example.com");
      cy.getByTestId("input-first_name").type("Test");
      cy.getByTestId("input-last_name").type("User");

      // Submit form
      cy.getByTestId("save-user-btn").click();

      // Verify request payload
      cy.wait("@createUser").then((interception) => {
        const { body } = interception.request;
        expect(body).to.include({
          username: "testuser",
          email_address: "test@example.com",
          first_name: "Test",
          last_name: "User",
          password_login_enabled: false,
        });
        expect(body.password).to.be.undefined;
      });

      // Verify success toast
      cy.getByTestId("toast-success-msg");
    });

    it("can create a user with password login enabled", () => {
      // Setup Plus with SSO and username/password login allowed
      stubPlus(true);
      cy.intercept("GET", "/api/v1/openid/provider", {
        body: [{ id: "test-provider" }],
      }).as("getOpenIdProviders");
      cy.intercept("GET", "/api/v1/config?api_set=false", {
        body: {
          plus_security_settings: { allow_username_password_login: true },
        },
      }).as("getConfigSettings");

      // Intercept messaging status to ensure email invite is disabled
      cy.intercept("GET", "/api/v1/messaging/email-invite/status", {
        body: {
          enabled: false,
        },
      }).as("getEmailInviteStatus");

      // Setup intercept for POST request
      cy.intercept("POST", "/api/v1/user", {
        statusCode: 200,
        body: {
          id: "new-user-123",
          username: "testuser",
          email_address: "test@example.com",
          first_name: "Test",
          last_name: "User",
        },
      }).as("createUser");

      cy.visit("/user-management/new");
      cy.wait("@getOpenIdProviders");
      cy.wait("@getConfigSettings");
      cy.wait("@getEmailInviteStatus");

      // Verify toggle exists and ensure it's checked
      cy.getByTestId("input-password_login_enabled").should("exist");
      cy.getByTestId("input-password_login_enabled").click();

      // Verify the password field is visible
      cy.getByTestId("input-password").should("exist");

      // Fill form with password login enabled
      cy.getByTestId("input-username").type("testuser");
      cy.getByTestId("input-email_address").type("test@example.com");
      cy.getByTestId("input-first_name").type("Test");
      cy.getByTestId("input-last_name").type("User");
      cy.getByTestId("input-password").type("P@ssw0rd123");

      // Submit form
      cy.getByTestId("save-user-btn").click();

      // Verify request payload
      cy.wait("@createUser").then((interception) => {
        const { body } = interception.request;
        expect(body).to.include({
          username: "testuser",
          email_address: "test@example.com",
          first_name: "Test",
          last_name: "User",
          password_login_enabled: true,
        });
        expect(body.password).to.exist;
      });

      // Verify success toast
      cy.getByTestId("toast-success-msg");
    });

    it("prevents submission with invalid email format", () => {
      // Intercept messaging status to ensure email invite is disabled
      cy.intercept("GET", "/api/v1/messaging/email-invite/status", {
        body: {
          enabled: false,
        },
      }).as("getEmailInviteStatus");

      cy.visit("/user-management/new");
      cy.wait("@getEmailInviteStatus");

      // Fill form with invalid email
      cy.getByTestId("input-username").type("testuser");
      cy.getByTestId("input-email_address").type("invalid-email");
      cy.getByTestId("input-password").type("P@ssw0rd123");

      // Try to submit (should be disabled)
      cy.getByTestId("save-user-btn").should("be.disabled");

      // Fix email and verify button becomes enabled
      cy.getByTestId("input-email_address").clear().type("valid@example.com");
      cy.getByTestId("save-user-btn").should("not.be.disabled");
    });

    it("validates password complexity requirements", () => {
      // Intercept messaging status to ensure email invite is disabled
      cy.intercept("GET", "/api/v1/messaging/email-invite/status", {
        body: {
          enabled: false,
        },
      }).as("getEmailInviteStatus");
      cy.intercept("GET", "/api/v1/config?api_set=false", {
        body: {
          plus_security_settings: { allow_username_password_login: true },
        },
      }).as("getConfigSettings");

      cy.visit("/user-management/new");
      cy.wait("@getEmailInviteStatus");
      cy.wait("@getConfigSettings");
      cy.getByTestId("input-username").type("testuser");
      cy.getByTestId("input-email_address").type("test@example.com");
      cy.getByTestId("input-password").type("simple");

      // Trigger validation by clicking elsewhere
      cy.getByTestId("input-username").click();

      // Button should be disabled due to invalid password
      cy.getByTestId("save-user-btn").should("be.disabled");

      // Enter valid password
      cy.getByTestId("input-password").clear().type("P@ssw0rd123");
      cy.getByTestId("save-user-btn").should("not.be.disabled");
    });

    it("displays error message when user creation fails", () => {
      // Intercept messaging status to ensure email invite is disabled
      cy.intercept("GET", "/api/v1/messaging/email-invite/status", {
        body: {
          enabled: false,
        },
      }).as("getEmailInviteStatus");

      // Setup intercept for error response
      cy.intercept("POST", "/api/v1/user", {
        statusCode: 400,
        body: {
          detail: "Username already exists",
        },
      }).as("createUserError");

      cy.visit("/user-management/new");
      cy.wait("@getEmailInviteStatus");

      // Fill form
      cy.getByTestId("input-username").type("testuser");
      cy.getByTestId("input-email_address").type("test@example.com");
      cy.getByTestId("input-password").type("P@ssw0rd123");

      // Submit form
      cy.getByTestId("save-user-btn").click();

      // Verify error toast
      cy.wait("@createUserError");
      cy.getByTestId("toast-error-msg").contains("Username already exists");
    });

    it("cancels user creation and returns to user management page", () => {
      cy.visit("/user-management/new");

      // Fill some form fields first
      cy.getByTestId("input-username").type("testuser");

      // Click cancel button
      cy.getByTestId("cancel-btn").click();

      // Verify redirection
      cy.url().should("eq", "http://localhost:3000/user-management");
    });

    it("does not show password field when SSO is enabled but username/password login is not allowed", () => {
      // Setup: Enable Plus & SSO providers, but disable username/password login
      stubPlus(true);
      cy.intercept("GET", "/api/v1/openid/provider", {
        body: [{ id: "test-provider" }],
      }).as("getOpenIdProviders");
      cy.intercept("GET", "/api/v1/config?api_set=false", {
        body: {
          plus_security_settings: { allow_username_password_login: false },
        },
      }).as("getConfigSettings");

      // Intercept messaging status to ensure email invite is disabled
      cy.intercept("GET", "/api/v1/messaging/email-invite/status", {
        body: {
          enabled: false,
        },
      }).as("getEmailInviteStatus");

      cy.visit("/user-management/new");
      cy.wait("@getOpenIdProviders");
      cy.wait("@getConfigSettings");
      cy.wait("@getEmailInviteStatus");

      // Verify toggle is not shown
      cy.getByTestId("input-password_login_enabled").should("not.exist");

      // Verify password field is not shown
      cy.getByTestId("input-password").should("not.exist");
    });

    it("immediately updates UI when password login toggle is clicked", () => {
      // Setup Plus with SSO and username/password login allowed
      stubPlus(true);
      cy.intercept("GET", "/api/v1/openid/provider", {
        body: [{ id: "test-provider" }],
      }).as("getOpenIdProviders");
      cy.intercept("GET", "/api/v1/config?api_set=false", {
        body: {
          plus_security_settings: { allow_username_password_login: true },
        },
      }).as("getConfigSettings");

      // Intercept messaging status to ensure email invite is disabled
      cy.intercept("GET", "/api/v1/messaging/email-invite/status", {
        body: {
          enabled: false,
        },
      }).as("getEmailInviteStatus");

      cy.visit("/user-management/new");
      cy.wait("@getOpenIdProviders");
      cy.wait("@getConfigSettings");
      cy.wait("@getEmailInviteStatus");

      // Get the toggle and verify it exists
      cy.getByTestId("input-password_login_enabled").should("exist");

      // Enable password login
      cy.getByTestId("input-password_login_enabled").click();
      cy.getByTestId("input-password").should("exist");

      // Disable password login
      cy.getByTestId("input-password_login_enabled").click();
      cy.getByTestId("input-password").should("not.exist");

      // Re-enable password login
      cy.getByTestId("input-password_login_enabled").click();
      cy.getByTestId("input-password").should("exist");
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
            total_scopes: permissions.total_scopes.filter(
              (scope) => scope !== "user:password-reset",
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

  describe("Delete user", () => {
    beforeEach(() => {
      cy.intercept("DELETE", "/api/v1/user/*", { body: {} }).as("deleteUser");
    });
    it("can delete a user via the menu", () => {
      cy.visit("/user-management");
      cy.getByTestId(`row-${USER_1_ID}`).within(() => {
        cy.getByTestId("delete-user-btn").click();
      });
      cy.getByTestId("delete-user-modal");
      cy.getByTestId("submit-btn").should("be.disabled");

      // type mismatching username
      cy.getByTestId("input-usernameConfirmation").type("user_one");
      // trigger blur event
      cy.getByTestId("input-usernameConfirmation").blur();
      cy.getByTestId("submit-btn").should("be.disabled");
      cy.getByTestId("error-usernameConfirmation").contains(
        "Confirmation input must match the username",
      );

      // now enter the proper thing
      cy.getByTestId("input-usernameConfirmation").clear().type("user_1");
      cy.getByTestId("submit-btn").should("be.enabled");
      cy.getByTestId("submit-btn").click();

      cy.wait("@deleteUser").then((interception) => {
        const { url } = interception.request;
        expect(url).to.contain(USER_1_ID);
      });
      cy.getByTestId("toast-success-msg");
    });

    it("can delete a user via the user's profile", () => {
      cy.intercept("GET", "/api/v1/user/*", {
        body: { id: "fid", username: "user_1" },
      }).as("getUser1");
      cy.visit(`/user-management/profile/${USER_1_ID}`);
      cy.wait("@getUser1");
      cy.getByTestId("delete-user-btn").click();

      cy.getByTestId("delete-user-modal").within(() => {
        cy.getByTestId("input-usernameConfirmation").type("user_1");
        cy.getByTestId("submit-btn").should("be.enabled");
        cy.getByTestId("submit-btn").click();
      });
      cy.wait("@deleteUser");
      cy.getByTestId("toast-success-msg");
      cy.url().should("match", /user-management$/);
    });
  });

  describe("Permission assignment", () => {
    beforeEach(() => {
      cy.intercept("PUT", "/api/v1/user/*/permission", { body: {} }).as(
        "updatePermission",
      );
    });

    it("can assign a role to a user", () => {
      cy.visit(`/user-management/profile/${USER_1_ID}`);
      cy.getAntTab("Permissions").click({ force: true });
      cy.getByTestId("selected").contains("Owner");

      cy.getByTestId("role-option-Viewer").click();
      cy.getByTestId("selected").contains("Viewer");
      cy.getByTestId("save-btn").click();

      cy.wait("@updatePermission").then((interception) => {
        const { body } = interception.request;
        expect(body.roles).to.eql(["viewer"]);
      });
    });

    describe("permissions", () => {
      it("contributors cannot assign permissions to an owner", () => {
        // assign USER_1_ID to the intercept (otherwise we will get our own, logged in user)
        cy.fixture("user-management/user.json").then((userData) => {
          cy.intercept(`/api/v1/user/${USER_1_ID}`, {
            body: { ...userData, id: USER_1_ID },
          }).as("getOwner");
        });

        // the logged in user is a contributor
        cy.assumeRole(RoleRegistryEnum.CONTRIBUTOR);
        cy.intercept(`/api/v1/user/${USER_1_ID}/permission`, {
          fixture: "user-management/permissions.json",
        }).as("getPermissions");
        cy.visit(`/user-management/profile/${USER_1_ID}`);
        cy.getAntTab("Permissions").click({ force: true });

        // they should get a message about having insufficient access
        cy.getByTestId("insufficient-access");
      });

      it("contributors cannot make a user an owner", () => {
        // assign USER_1_ID to the intercept (otherwise we will get our own, logged in user)
        cy.fixture("user-management/user.json").then((userData) => {
          cy.intercept(`/api/v1/user/${USER_1_ID}`, {
            body: { ...userData, id: USER_1_ID },
          }).as("getOwner");
        });

        // the logged in user is a contributor
        cy.assumeRole(RoleRegistryEnum.CONTRIBUTOR);
        // the user we are editing has the role of a viewer
        cy.fixture("user-management/permissions.json").then((permissions) => {
          cy.intercept(`/api/v1/user/${USER_1_ID}/permission`, {
            body: { ...permissions, roles: ["viewer"] },
          });
        });
        cy.visit(`/user-management/profile/${USER_1_ID}`);
        cy.getAntTab("Permissions").click({ force: true });

        // they should see role options available to click but owner should be disabled
        cy.getByTestId("role-options");
        cy.getByTestId("role-option-Owner").should("be.disabled");
      });
    });

    describe("system managers", () => {
      const systems = [
        "fidesctl_system",
        "demo_analytics_system",
        "demo_marketing_system",
      ];

      beforeEach(() => {
        cy.intercept("/api/v1/user/*/system-manager", {
          fixture: "systems/systems.json",
        }).as("getUserManagedSystems");
        cy.intercept("PUT", "/api/v1/user/*/system-manager", {
          fixture: "systems/systems.json",
        }).as("updateUserManagedSystems");
        cy.intercept("GET", "/api/v1/system", {
          fixture: "systems/systems.json",
        }).as("getSystems");
      });

      describe("approver cannot have systems", () => {
        beforeEach(() => {
          cy.visit(`/user-management/profile/${USER_1_ID}`);
          cy.getAntTab("Permissions").click({ force: true });
          cy.wait("@getUserManagedSystems");
        });

        it("can warn when assigning an approver", () => {
          cy.getByTestId("role-option-Approver").click();
          cy.getByTestId("save-btn").click();
          cy.getByTestId("downgrade-to-approver-confirmation-modal").within(
            () => {
              cy.getByTestId("continue-btn").click();
            },
          );
          cy.wait("@updatePermission");
        });
      });

      describe("in role option", () => {
        beforeEach(() => {
          cy.visit(`/user-management/profile/${USER_1_ID}`);
          cy.getAntTab("Permissions").click({ force: true });
          cy.wait("@getUserManagedSystems");
          cy.getByTestId("assign-systems-delete-table");
        });
        it("shows assigned systems in the role option", () => {
          systems.forEach((system) => {
            cy.getByTestId(`row-${system}`);
          });
        });

        it("can remove systems via the role option", () => {
          cy.getByTestId("row-fidesctl_system").within(() => {
            cy.getByTestId("unassign-btn").click();
          });
          cy.getByTestId("save-btn").click();

          cy.wait("@updateUserManagedSystems").then((interception) => {
            const { body } = interception.request;
            expect(body).to.eql([
              "demo_analytics_system",
              "demo_marketing_system",
            ]);
          });
        });
      });

      describe("in modal", () => {
        beforeEach(() => {
          cy.visit(`/user-management/profile/${USER_1_ID}`);
          cy.getAntTab("Permissions").click({ force: true });
          cy.wait("@getUserManagedSystems");

          cy.getByTestId("assign-systems-delete-table").should("exist"); // ensure the data is added to the React state before proceeding
          cy.getByTestId("assign-systems-btn").click();
          cy.wait("@getSystems");
        });

        it("can toggle one system", () => {
          cy.getByTestId("assign-systems-modal-body").within(() => {
            cy.getByTestId("row-fidesctl_system").within(() => {
              cy.getByTestId("assign-switch").click();
            });

            // the select all toggle should no longer be selected
            cy.getByTestId("assign-all-systems-toggle").should(
              "have.attr",
              "aria-checked",
              "false",
            );
          });
          cy.getByTestId("confirm-btn").click();
          cy.getByTestId("save-btn").click();

          cy.wait("@updatePermission");
          cy.wait("@updateUserManagedSystems").then((interception) => {
            const { body } = interception.request;
            expect(body).to.eql([
              "demo_analytics_system",
              "demo_marketing_system",
            ]);
          });
        });

        it("can use the select all toggle to unassign systems", () => {
          cy.getByTestId("assign-all-systems-toggle").should(
            "have.attr",
            "aria-checked",
            "true",
          );
          // all toggles in every row should be checked

          cy.getByTestId("assign-systems-modal-body").within(() => {
            systems.forEach((fidesKey) => {
              cy.getByTestId(`row-${fidesKey}`).within(() => {
                cy.getByTestId("assign-switch").should(
                  "have.attr",
                  "aria-checked",
                  "true",
                );
              });
            });
          });

          cy.getByTestId("assign-all-systems-toggle").click();
          // all toggles in every row should be unchecked
          cy.getByTestId("assign-systems-modal-body").within(() => {
            systems.forEach((fidesKey) => {
              cy.getByTestId(`row-${fidesKey}`).within(() => {
                cy.getByTestId("assign-switch").should(
                  "have.attr",
                  "aria-checked",
                  "false",
                );
              });
            });
          });

          cy.getByTestId("confirm-btn").click();
          cy.getByTestId("save-btn").click();
          cy.wait("@updatePermission");
          cy.wait("@updateUserManagedSystems").then((interception) => {
            const { body } = interception.request;
            expect(body).to.eql([]);
          });
        });

        it("can search while respecting the all toggle", () => {
          cy.getByTestId("assign-systems-modal-body").within(() => {
            cy.getByTestId("system-search").type("demo");
            cy.getByTestId("row-fidesctl_system").should("not.exist");

            // toggling "all systems" when we are filtered should only toggle the filtered ones
            cy.getByTestId("assign-all-systems-toggle").click();
            ["demo_marketing_system", "demo_analytics_system"].forEach(
              (fidesKey) => {
                cy.getByTestId(`row-${fidesKey}`).within(() => {
                  cy.getByTestId("assign-switch").should(
                    "have.attr",
                    "aria-checked",
                    "false",
                  );
                });
              },
            );

            // the one that was not in the search should not have been affected
            cy.getByTestId("system-search").clear();
            cy.getByTestId(`row-fidesctl_system`).within(() => {
              cy.getByTestId("assign-switch").should(
                "have.attr",
                "aria-checked",
                "true",
              );
            });
            cy.getByTestId("assign-all-systems-toggle").should(
              "have.attr",
              "aria-checked",
              "false",
            );

            // now do the reverse: toggle on while filtered
            // toggle everyone off by clicking on the all toggle twice
            cy.getByTestId("assign-all-systems-toggle").click();
            cy.getByTestId("assign-all-systems-toggle").click();

            cy.getByTestId("system-search").type("demo");
            cy.getByTestId("assign-all-systems-toggle").click();
            cy.getByTestId("system-search").clear();
            cy.getByTestId(`row-fidesctl_system`).within(() => {
              cy.getByTestId("assign-switch").should(
                "have.attr",
                "aria-checked",
                "false",
              );
            });
          });
        });
      });
    });
  });
});
