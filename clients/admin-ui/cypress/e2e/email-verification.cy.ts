import { STORAGE_ROOT_KEY } from "~/constants";

type CypressUser = {
  id: string;
  username: string;
  created_at: string;
  email_address?: string | null;
  first_name?: string | null;
  last_name?: string | null;
  email_verified_at?: string | null;
  password_login_enabled?: boolean | null;
};

const writeAuthState = (user: CypressUser) => {
  cy.window().then((win) => {
    win.localStorage.setItem(
      STORAGE_ROOT_KEY,
      JSON.stringify({
        auth: JSON.stringify({
          user,
          token: "super_secret",
        }),
      }),
    );
  });
};

// `id` is intentionally not prefixed with "fid_" so the user is treated as a
// root user by `isRootUserId`, matching the convention in cypress/fixtures/login.json.
// Without this, `useNav` returns no active route for the synthetic user and
// `ProtectedRoute` renders null, so `cy.getByTestId("Home")` would time out.
const baseUser: CypressUser = {
  id: "123",
  username: "cypress-user",
  created_at: "2026-01-01T00:00:00.000Z",
  email_address: "cypress-user@ethyca.com",
  email_verified_at: null,
  password_login_enabled: true,
};

const stubLoggedInRequests = () => {
  cy.intercept("/api/v1/user/*/permission", {
    fixture: "user-management/permissions.json",
  }).as("getUserPermission");
  cy.intercept("GET", "/api/v1/system", { body: [] });
};

const snoozeKeyFor = (user: CypressUser) =>
  `fides:email-verification-banner-snooze:${user.id}:${user.email_address ?? "none"}`;

describe("Email verification banner", () => {
  beforeEach(() => {
    stubLoggedInRequests();
  });

  it("does not render when the user's email is already verified", () => {
    cy.intercept("GET", "/api/v1/messaging/email-invite/status", {
      body: { enabled: true },
    }).as("getEmailInviteStatus");
    cy.visit("/", {
      onBeforeLoad: () =>
        writeAuthState({
          ...baseUser,
          email_verified_at: "2026-01-02T00:00:00.000Z",
        }),
    });
    cy.getByTestId("Home");
    cy.get("[data-testid^='email-verification-banner-']").should("not.exist");
  });

  it("does not render when email invites are disabled", () => {
    cy.intercept("GET", "/api/v1/messaging/email-invite/status", {
      body: { enabled: false },
    }).as("getEmailInviteStatus");
    cy.visit("/", {
      onBeforeLoad: () => writeAuthState(baseUser),
    });
    cy.getByTestId("Home");
    cy.get("[data-testid^='email-verification-banner-']").should("not.exist");
  });

  it("does not render for SSO-only users (password_login_enabled=false)", () => {
    cy.intercept("GET", "/api/v1/messaging/email-invite/status", {
      body: { enabled: true },
    }).as("getEmailInviteStatus");
    cy.visit("/", {
      onBeforeLoad: () =>
        writeAuthState({ ...baseUser, password_login_enabled: false }),
    });
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

    cy.visit("/", {
      onBeforeLoad: () => writeAuthState(baseUser),
    });
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
      body: { ...baseUser, email_address: null },
    }).as("getUser");

    const noEmailUser = { ...baseUser, email_address: null };
    cy.visit("/", {
      onBeforeLoad: () => writeAuthState(noEmailUser),
    });
    cy.getByTestId("Home");
    cy.getByTestId("email-verification-banner-no-email").should("be.visible");
    cy.getByTestId("email-verification-banner-add-email-btn").click();
    cy.location("pathname").should(
      "eq",
      `/user-management/profile/${noEmailUser.id}`,
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

    cy.visit("/", {
      onBeforeLoad: () => writeAuthState(baseUser),
    });
    cy.getByTestId("Home");
    cy.getByTestId("email-verification-banner-unverified")
      .find("[aria-label='Close']")
      .click();
    cy.get("[data-testid^='email-verification-banner-']").should("not.exist");

    // Reload — still snoozed.
    cy.reload();
    cy.getByTestId("Home");
    cy.get("[data-testid^='email-verification-banner-']").should("not.exist");

    // Fast-forward the snooze timestamp to 8 days ago and reload.
    cy.window().then((win) => {
      const eightDaysAgo = Date.now() - 8 * 24 * 60 * 60 * 1000;
      win.localStorage.setItem(snoozeKeyFor(baseUser), String(eightDaysAgo));
    });
    cy.reload();
    cy.getByTestId("Home");
    cy.getByTestId("email-verification-banner-unverified").should("be.visible");
  });

  it("invalidates the snooze when the user's email_address changes", () => {
    cy.intercept("GET", "/api/v1/messaging/email-invite/status", {
      body: { enabled: true },
    }).as("getEmailInviteStatus");

    // Snooze the banner for the current email.
    cy.visit("/", {
      onBeforeLoad: () => {
        writeAuthState(baseUser);
      },
    });
    cy.getByTestId("Home");
    cy.getByTestId("email-verification-banner-unverified")
      .find("[aria-label='Close']")
      .click();
    cy.get("[data-testid^='email-verification-banner-']").should("not.exist");

    // Now simulate the user editing their email — banner should reappear
    // because the snooze key is keyed on (userId, email_address).
    cy.visit("/", {
      onBeforeLoad: () =>
        writeAuthState({
          ...baseUser,
          email_address: "new-email@ethyca.com",
        }),
    });
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
