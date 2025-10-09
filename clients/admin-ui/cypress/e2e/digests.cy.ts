import { stubPlus } from "cypress/support/stubs";

import { RoleRegistryEnum } from "~/types/api";

describe("Digests", () => {
  beforeEach(() => {
    cy.login();
    stubPlus(true);

    cy.intercept("/api/v1/config?api_set=false", {});
  });

  describe("List page", () => {
    it("should display and interact with digest list", () => {
      cy.intercept("GET", "/api/v1/plus/digest-config?*", {
        fixture: "digests/list.json",
      }).as("getDigestConfigs");

      cy.visit("/notifications/digests");
      cy.assumeRole(RoleRegistryEnum.OWNER);
      cy.wait("@getDigestConfigs");

      // Verify page loads with correct elements
      cy.getByTestId("digests-management").should("be.visible");
      cy.get('[data-testid="add-digest-btn"]').should("be.visible");
      cy.get(".ant-list-item").should("have.length", 3);

      // Verify first digest details
      cy.get(".ant-list-item")
        .first()
        .within(() => {
          cy.contains("Weekly Manual Tasks Digest").should("be.visible");
          cy.contains("Manual Tasks").should("be.visible");
          cy.get('[data-testid="toggle-enabled-switch"]').should(
            "have.attr",
            "aria-checked",
            "true",
          );
        });

      // Test search functionality
      cy.getByTestId("search-input").type("Daily");
      cy.get(".ant-list-item").should("have.length", 1);
      cy.contains("Daily Task Summary").should("be.visible");
    });

    it("should display empty state", () => {
      cy.intercept("GET", "/api/v1/plus/digest-config?*", {
        fixture: "digests/empty-list.json",
      }).as("getEmptyDigestConfigs");

      cy.visit("/notifications/digests");
      cy.wait("@getEmptyDigestConfigs");

      cy.contains("No digest configurations yet").should("be.visible");
    });
  });

  describe("Toggle enabled/disabled", () => {
    it("should toggle digest enabled status with correct request", () => {
      cy.intercept("GET", "/api/v1/plus/digest-config?*", {
        fixture: "digests/list.json",
      }).as("getDigestConfigs");

      cy.intercept("PUT", "/api/v1/plus/digest-config/*", {
        statusCode: 200,
        body: { message: "Digest configuration updated" },
      }).as("updateDigestConfig");

      cy.visit("/notifications/digests");
      cy.assumeRole(RoleRegistryEnum.OWNER);
      cy.wait("@getDigestConfigs");

      // Toggle the first digest (currently enabled -> disabled)
      cy.get(".ant-list-item")
        .first()
        .within(() => {
          cy.get('[data-testid="toggle-enabled-switch"]').click();
        });

      cy.wait("@updateDigestConfig").then((interception) => {
        expect(interception.request.body).to.have.property("enabled", false);
        expect(interception.request.body).to.have.property(
          "name",
          "Weekly Manual Tasks Digest",
        );
        expect(interception.request.body).to.have.property(
          "digest_type",
          "manual_tasks",
        );
        expect(interception.request.url).to.contain(
          "dig_26937d32-fb6e-4b60-ad7e-85180e4c9d38",
        );
        expect(interception.request.url).to.contain(
          "digest_config_type=manual_tasks",
        );
      });

      cy.contains("successfully").should("be.visible");
    });
  });

  describe("Create digest", () => {
    it("should create a new digest with correct request parameters", () => {
      cy.intercept("POST", "/api/v1/plus/digest-config?*", {
        statusCode: 201,
        fixture: "digests/created-digest.json",
      }).as("createDigestConfig");

      cy.visit("/notifications/digests/new");
      cy.assumeRole(RoleRegistryEnum.OWNER);

      // Fill in the form
      cy.getByTestId("input-name").type("New Test Digest");
      cy.getByTestId("select-digest-type").should(
        "have.class",
        "ant-select-disabled",
      );

      // Change schedule to daily
      cy.getByTestId("select-frequency").antSelect("Daily");

      cy.getByTestId("submit-btn").click();

      cy.wait("@createDigestConfig").then((interception) => {
        expect(interception.request.body.name).to.equal("New Test Digest");
        expect(interception.request.body.digest_type).to.equal("manual_tasks");
        expect(interception.request.body.cron_expression).to.equal("0 9 * * *");
        expect(interception.request.url).to.contain(
          "digest_config_type=manual_tasks",
        );
      });

      cy.contains("created successfully").should("be.visible");
    });

    it("should validate required fields", () => {
      cy.visit("/notifications/digests/new");
      cy.assumeRole(RoleRegistryEnum.OWNER);
      cy.getByTestId("submit-btn").click();
      cy.contains("Please enter a name").should("be.visible");
    });
  });

  describe("Edit digest", () => {
    it("should load and update digest with correct request parameters", () => {
      cy.intercept("GET", "/api/v1/plus/digest-config/*", {
        fixture: "digests/detail.json",
      }).as("getDigestDetail");

      cy.intercept("PUT", "/api/v1/plus/digest-config/*", {
        statusCode: 200,
        body: { message: "Digest configuration updated" },
      }).as("updateDigestConfig");

      cy.visit(
        "/notifications/digests/dig_26937d32-fb6e-4b60-ad7e-85180e4c9d38",
      );
      cy.assumeRole(RoleRegistryEnum.OWNER);
      cy.wait("@getDigestDetail");

      // Verify form is populated
      cy.getByTestId("input-name").should(
        "have.value",
        "Weekly Manual Tasks Digest",
      );
      cy.getByTestId("submit-btn").should("contain", "Update");

      // Update the name and schedule
      cy.getByTestId("input-name").clear().type("Updated Weekly Digest");
      cy.getByTestId("select-frequency").antSelect("Daily");

      cy.getByTestId("submit-btn").click();

      cy.wait("@updateDigestConfig").then((interception) => {
        expect(interception.request.body.name).to.equal(
          "Updated Weekly Digest",
        );
        expect(interception.request.body.cron_expression).to.equal("0 9 * * *");
        expect(interception.request.url).to.contain(
          "dig_26937d32-fb6e-4b60-ad7e-85180e4c9d38",
        );
      });

      cy.contains("updated successfully").should("be.visible");
    });
  });

  describe("Delete digest", () => {
    it("should delete digest after confirmation with correct request", () => {
      cy.intercept("GET", "/api/v1/plus/digest-config/*", {
        fixture: "digests/detail.json",
      }).as("getDigestDetail");

      cy.intercept("DELETE", "/api/v1/plus/digest-config/*", {
        statusCode: 204,
      }).as("deleteDigestConfig");

      cy.visit(
        "/notifications/digests/dig_26937d32-fb6e-4b60-ad7e-85180e4c9d38",
      );
      cy.assumeRole(RoleRegistryEnum.OWNER);
      cy.wait("@getDigestDetail");

      cy.getByTestId("delete-btn").click();
      cy.contains("Delete digest configuration").should("be.visible");
      cy.getByTestId("continue-btn").click();

      cy.wait("@deleteDigestConfig").then((interception) => {
        expect(interception.request.url).to.contain(
          "dig_26937d32-fb6e-4b60-ad7e-85180e4c9d38",
        );
        expect(interception.request.url).to.contain(
          "digest_config_type=manual_tasks",
        );
      });
    });
  });

  describe("Test email", () => {
    it("should send test email with correct request parameters", () => {
      cy.intercept("GET", "/api/v1/plus/digest-config/*", {
        fixture: "digests/detail.json",
      }).as("getDigestDetail");

      cy.intercept("POST", "/api/v1/plus/digest-config/test?*", {
        statusCode: 200,
        body: {
          message: "Test digest email sent",
          test_email: "test@example.com",
          status: "success",
        },
      }).as("sendTestEmail");

      cy.visit(
        "/notifications/digests/dig_26937d32-fb6e-4b60-ad7e-85180e4c9d38",
      );
      cy.assumeRole(RoleRegistryEnum.OWNER);
      cy.wait("@getDigestDetail");

      cy.getByTestId("test-email-btn").click();
      cy.getByTestId("test-email-input").type("test@example.com");
      cy.getByTestId("send-test-btn").click();

      cy.wait("@sendTestEmail").then((interception) => {
        expect(interception.request.url).to.contain(
          "digest_config_id=dig_26937d32-fb6e-4b60-ad7e-85180e4c9d38",
        );
        expect(interception.request.url).to.contain(
          "test_email=test%40example.com",
        );
      });

      cy.contains("Test email sent").should("be.visible");
    });
  });

  describe("Schedule configuration", () => {
    it("should configure different schedule frequencies", () => {
      cy.intercept("POST", "/api/v1/plus/digest-config?*", {
        statusCode: 201,
        fixture: "digests/created-digest.json",
      }).as("createDigestConfig");

      // Test weekly (default)
      cy.visit("/notifications/digests/new");
      cy.assumeRole(RoleRegistryEnum.OWNER);

      cy.getByTestId("input-name").type("Weekly Test");
      cy.getByTestId("select-frequency")
        .find(".ant-select-selection-item")
        .should("contain", "Weekly");
      cy.getByTestId("submit-btn").click();
      cy.wait("@createDigestConfig").then((interception) => {
        expect(interception.request.body.cron_expression).to.equal("0 9 * * 1");
      });

      // Test monthly with custom day
      cy.visit("/notifications/digests/new");
      cy.assumeRole(RoleRegistryEnum.OWNER);

      cy.getByTestId("input-name").type("Monthly Test");
      cy.getByTestId("select-frequency").antSelect("Monthly");
      cy.getByTestId("input-day-of-month").clear().type("15");
      cy.getByTestId("submit-btn").click();
      cy.wait("@createDigestConfig").then((interception) => {
        expect(interception.request.body.cron_expression).to.equal(
          "0 9 15 * *",
        );
      });
    });
  });
});
