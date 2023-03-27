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
            total_scopes: permissions.total_scopes.filter(
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

  describe("Delete user", () => {
    beforeEach(() => {
      cy.intercept("DELETE", "/api/v1/user/*", { body: {} }).as("deleteUser");
    });
    it("can delete a user via the menu", () => {
      cy.visit("/user-management");
      cy.getByTestId(`row-${USER_1_ID}`).within(() => {
        cy.getByTestId("menu-btn").click();
      });
      cy.getByTestId(`menu-${USER_1_ID}`).within(() => {
        cy.getByTestId("delete-btn").click();
      });
      cy.getByTestId("delete-user-modal");
      cy.getByTestId("submit-btn").should("be.disabled");

      // type mismatching usernames
      cy.getByTestId("input-username").type("user_1");
      cy.getByTestId("input-usernameConfirmation").type("user_one");
      // trigger blur event
      cy.getByTestId("delete-user-modal").click();
      cy.getByTestId("delete-user-modal").contains("Usernames must match");
      cy.getByTestId("submit-btn").should("be.disabled");

      // type matching but incorrect username
      cy.getByTestId("input-username").clear().type("user_one");
      cy.getByTestId("input-usernameConfirmation").clear().type("user_one");
      cy.getByTestId("delete-user-modal").contains(
        "Username must match this user's"
      );
      cy.getByTestId("submit-btn").should("be.disabled");

      // now enter the proper thing
      cy.getByTestId("input-username").clear().type("user_1");
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
        cy.getByTestId("input-username").type("user_1");
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
        "updatePermission"
      );
    });

    it("can assign a role to a user", () => {
      cy.visit(`/user-management/profile/${USER_1_ID}`);
      cy.getByTestId("tab-Permissions").click();
      cy.getByTestId("selected").contains("Owner");

      cy.getByTestId("role-option-Viewer").click();
      cy.getByTestId("selected").contains("Viewer");
      cy.getByTestId("save-btn").click();

      cy.wait("@updatePermission").then((interception) => {
        const { body } = interception.request;
        expect(body.roles).to.eql(["viewer"]);
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

      describe("in role option", () => {
        beforeEach(() => {
          cy.visit(`/user-management/profile/${USER_1_ID}`);
          cy.getByTestId("tab-Permissions").click();
          cy.wait("@getSystems");
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
            expect(body).to.eql(["demo_analytics_system", "demo_marketing_system"]);
          });
        });
      });

      describe("in modal", () => {
        beforeEach(() => {
          cy.visit(`/user-management/profile/${USER_1_ID}`);
          cy.getByTestId("tab-Permissions").click();

          cy.getByTestId("assign-systems-btn").click();
          cy.wait("@getSystems");
          cy.wait("@getUserManagedSystems");
        });

        it("can toggle one system", () => {
          cy.getByTestId("assign-systems-modal-body").within(() => {
            cy.getByTestId("row-fidesctl_system").within(() => {
              cy.getByTestId("assign-switch").click();
            });

            // the select all toggle should no longer be selected
            cy.getByTestId("assign-all-systems-toggle").within(() => {
              cy.get("span").should("not.have.attr", "data-checked");
            });
          });
          cy.getByTestId("confirm-btn").click();
          cy.getByTestId("save-btn").click();

          cy.wait("@updatePermission")
          cy.wait("@updateUserManagedSystems").then((interception) => {
            const { body } = interception.request;
            expect(body).to.eql([
              "demo_analytics_system",
              "demo_marketing_system",
            ]);
          });
        });

        it("can use the select all toggle to unassign systems", () => {
          cy.getByTestId("assign-all-systems-toggle").within(() => {
            cy.get("span").should("have.attr", "data-checked");
          });
          // all toggles in every row should be checked

          cy.getByTestId("assign-systems-modal-body").within(() => {
            systems.forEach((fidesKey) => {
              cy.getByTestId(`row-${fidesKey}`).within(() => {
                cy.getByTestId("assign-switch").within(() => {
                  cy.get("span").should("have.attr", "data-checked");
                });
              });
            });
          });

          cy.getByTestId("assign-all-systems-toggle").click();
          // all toggles in every row should be unchecked
          cy.getByTestId("assign-systems-modal-body").within(() => {
            systems.forEach((fidesKey) => {
              cy.getByTestId(`row-${fidesKey}`).within(() => {
                cy.getByTestId("assign-switch").within(() => {
                  cy.get("span").should("not.have.attr", "data-checked");
                });
              });
            });
          });

          cy.getByTestId("confirm-btn").click();
          cy.getByTestId("save-btn").click();
          cy.wait("@updatePermission")
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
                  cy.getByTestId("assign-switch").within(() => {
                    cy.get("span").should("not.have.attr", "data-checked");
                  });
                });
              }
            );

            // the one that was not in the search should not have been affected
            cy.getByTestId("system-search").clear();
            cy.getByTestId(`row-fidesctl_system`).within(() => {
              cy.getByTestId("assign-switch").within(() => {
                cy.get("span").should("have.attr", "data-checked");
              });
            });
            cy.getByTestId("assign-all-systems-toggle").within(() => {
              cy.get("span").should("not.have.attr", "data-checked");
            });

            // now do the reverse: toggle on while filtered
            // toggle everyone off by clicking on the all toggle twice
            cy.getByTestId("assign-all-systems-toggle").click();
            cy.getByTestId("assign-all-systems-toggle").click();

            cy.getByTestId("system-search").type("demo");
            cy.getByTestId("assign-all-systems-toggle").click();
            cy.getByTestId("system-search").clear();
            cy.getByTestId(`row-fidesctl_system`).within(() => {
              cy.getByTestId("assign-switch").within(() => {
                cy.get("span").should("not.have.attr", "data-checked");
              });
            });
          });
        });
      });
    });
  });
});
