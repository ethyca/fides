import { stubPlus } from "cypress/support/stubs";

import { STORAGE_ROOT_KEY } from "~/constants";

type UserOverrides = {
  email_address?: string | null;
  email_verified_at?: string | null;
  password_login_enabled?: boolean | null;
};

// Mirrors the canonical `cy.login()` pattern from cypress/support/commands.ts:
// writes the persisted redux auth state to localStorage via the cypress command
// queue (not via `onBeforeLoad`) and stubs the user-permission endpoint, then
// allows test-by-test overrides on the user fields the banner cares about.
const loginAs = (overrides: UserOverrides = {}) => {
  cy.fixture("login.json").then((body) => {
    const authState = {
      user: { ...body.user_data, ...overrides },
      token: body.token_data.access_token,
    };
    cy.window().then((win) => {
      win.localStorage.setItem(
        STORAGE_ROOT_KEY,
        JSON.stringify({ auth: JSON.stringify(authState) }),
      );
    });
  });
  cy.intercept("/api/v1/user/*/permission", {
    fixture: "user-management/permissions.json",
  }).as("getUserPermission");
};

const baseLoginUserId = "123"; // matches login.json fixture
const baseLoginEmail = "cypress-user@ethyca.com";

const stubLoggedInRequests = () => {
  stubPlus(true);
  cy.intercept("GET", "/api/v1/system", { body: [] });
};

const snoozeKeyFor = (email: string | null) =>
  `fides:email-verification-banner-snooze:${baseLoginUserId}:${email ?? "none"}`;

describe("Email verification banner", () => {
  beforeEach(() => {
    stubLoggedInRequests();
  });

  it("does not render when the user's email is already verified", () => {
    cy.intercept("GET", "/api/v1/messaging/email-invite/status", {
      body: { enabled: true },
    }).as("getEmailInviteStatus");
    loginAs({
      email_address: baseLoginEmail,
      email_verified_at: "2026-01-02T00:00:00.000Z",
    });
    cy.visit("/");
    cy.getByTestId("Home");
    cy.get("[data-testid^='email-verification-banner-']").should("not.exist");
  });

  it("does not render when email invites are disabled", () => {
    cy.intercept("GET", "/api/v1/messaging/email-invite/status", {
      body: { enabled: false },
    }).as("getEmailInviteStatus");
    loginAs({ email_address: baseLoginEmail, email_verified_at: null });
    cy.visit("/");
    cy.getByTestId("Home");
    cy.get("[data-testid^='email-verification-banner-']").should("not.exist");
  });

  it("does not render for SSO-only users (password_login_enabled=false)", () => {
    cy.intercept("GET", "/api/v1/messaging/email-invite/status", {
      body: { enabled: true },
    }).as("getEmailInviteStatus");
    loginAs({
      email_address: baseLoginEmail,
      email_verified_at: null,
      password_login_enabled: false,
    });
    cy.visit("/");
    cy.getByTestId("Home");
    cy.get("[data-testid^='email-verification-banner-']").should("not.exist");
  });

  it("prompts unverified users and dispatches a verification email on click", () => {
    cy.intercept("GET", "/api/v1/messaging/email-invite/status", {
      body: { enabled: true },
    }).as("getEmailInviteStatus");
    cy.intercept("POST", "/api/v1/user/request-email-verification", {
      body: {
        detail:
          "If your account is eligible, a verification email has been sent.",
      },
    }).as("requestEmailVerification");

    loginAs({ email_address: baseLoginEmail, email_verified_at: null });
    cy.visit("/");
    cy.getByTestId("Home");
    cy.getByTestId("email-verification-banner-unverified").should("be.visible");
    cy.getByTestId("email-verification-banner-send-btn").click();
    cy.wait("@requestEmailVerification");
    cy.getByTestId("email-verification-banner-sent").should("be.visible");
  });

  it("routes no-email users to the profile edit page with #email_address", () => {
    cy.intercept("GET", "/api/v1/messaging/email-invite/status", {
      body: { enabled: true },
    }).as("getEmailInviteStatus");
    cy.intercept("/api/v1/user/*", {
      fixture: "user-management/user.json",
    }).as("getUser");

    loginAs({ email_address: null, email_verified_at: null });
    cy.visit("/");
    cy.getByTestId("Home");
    cy.getByTestId("email-verification-banner-no-email").should("be.visible");
    cy.getByTestId("email-verification-banner-add-email-btn").click();
    cy.location("pathname").should(
      "eq",
      `/user-management/profile/${baseLoginUserId}`,
    );
    cy.location("hash").should("eq", "#email_address");
    // The form should auto-focus the email field; we don't strictly need to
    // assert focus (jsdom/cypress can be flaky for focus assertions across
    // smooth-scroll timing) but verify it rendered.
    cy.getByTestId("input-email_address");
  });

  it("hides the banner when dismissed and re-shows it after the snooze TTL expires", () => {
    cy.intercept("GET", "/api/v1/messaging/email-invite/status", {
      body: { enabled: true },
    }).as("getEmailInviteStatus");

    loginAs({ email_address: baseLoginEmail, email_verified_at: null });
    cy.visit("/");
    cy.getByTestId("Home");
    cy.getByTestId("email-verification-banner-unverified")
      .find(".ant-alert-close-icon")
      .click();
    cy.get("[data-testid^='email-verification-banner-']").should("not.exist");

    // Reload — still snoozed.
    cy.reload();
    cy.getByTestId("Home");
    cy.get("[data-testid^='email-verification-banner-']").should("not.exist");

    // Fast-forward the snooze timestamp to 8 days ago and reload.
    cy.window().then((win) => {
      const eightDaysAgo = Date.now() - 8 * 24 * 60 * 60 * 1000;
      win.localStorage.setItem(
        snoozeKeyFor(baseLoginEmail),
        String(eightDaysAgo),
      );
    });
    cy.reload();
    cy.getByTestId("Home");
    cy.getByTestId("email-verification-banner-unverified").should("be.visible");
  });

  it("invalidates the snooze when the user's email_address changes", () => {
    cy.intercept("GET", "/api/v1/messaging/email-invite/status", {
      body: { enabled: true },
    }).as("getEmailInviteStatus");

    // Snooze the banner for the original email.
    loginAs({ email_address: baseLoginEmail, email_verified_at: null });
    cy.visit("/");
    cy.getByTestId("Home");
    cy.getByTestId("email-verification-banner-unverified")
      .find(".ant-alert-close-icon")
      .click();
    cy.get("[data-testid^='email-verification-banner-']").should("not.exist");

    // Now simulate the user editing their email — banner should reappear
    // because the snooze key is keyed on (userId, email_address).
    loginAs({
      email_address: "new-email@ethyca.com",
      email_verified_at: null,
    });
    cy.visit("/");
    cy.getByTestId("Home");
    cy.getByTestId("email-verification-banner-unverified").should("be.visible");
  });
});

describe("Verify email landing page", () => {
  it("verifies the email and redirects to the dashboard on success", () => {
    cy.fixture("login.json").then((body) => {
      cy.intercept("POST", "/api/v1/user/verify-email-with-token", body).as(
        "verifyEmail",
      );
    });
    cy.intercept("/api/v1/user/*/permission", {
      fixture: "user-management/permissions.json",
    }).as("getUserPermission");
    cy.intercept("GET", "/api/v1/system", { body: [] });

    cy.visit("/verify-email?username=cypress-user&token=valid-token");
    cy.wait("@verifyEmail").then((interception) => {
      expect(interception.request.body).to.eql({
        username: "cypress-user",
        token: "valid-token",
      });
    });
    cy.location("pathname").should("eq", "/");
  });

  it("shows an error state when the token is rejected", () => {
    cy.intercept("POST", "/api/v1/user/verify-email-with-token", {
      statusCode: 400,
      body: { detail: "Invalid or expired verification token." },
    }).as("verifyEmail");

    cy.visit("/verify-email?username=cypress-user&token=bad");
    cy.wait("@verifyEmail");
    cy.getByTestId("verify-email-error").should("be.visible");
    cy.getByTestId("back-to-login-btn").should("be.visible");
  });

  it("shows an error state when the URL is missing parameters", () => {
    cy.visit("/verify-email");
    cy.getByTestId("verify-email-error").should("be.visible");
  });
});
