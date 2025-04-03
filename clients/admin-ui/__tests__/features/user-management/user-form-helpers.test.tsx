import {
  isPasswordFieldRequired,
  shouldShowLoginMethodSelector,
  shouldShowPasswordField,
  shouldShowPasswordManagement,
} from "~/features/user-management/user-form-helpers";

describe("UserForm helper functions", () => {
  // Reusable test configurations to make tests more readable
  const NEW_USER = true;
  const EXISTING_USER = false;
  const INVITE_BY_EMAIL = true;
  const NO_EMAIL_INVITE = false;
  const PLUS_ENABLED = true;
  const PLUS_DISABLED = false;
  const SSO_ENABLED = true;
  const SSO_DISABLED = false;
  const USERNAME_PASSWORD_ALLOWED = true;
  const USERNAME_PASSWORD_NOT_ALLOWED = false;
  const LOGIN_USERNAME_PASSWORD = "username_password";
  const LOGIN_SSO = "sso";

  describe("shouldShowLoginMethodSelector", () => {
    it("returns true when all conditions are met", () => {
      expect(
        shouldShowLoginMethodSelector(
          PLUS_ENABLED,
          SSO_ENABLED,
          USERNAME_PASSWORD_ALLOWED,
        ),
      ).toBe(true);
    });

    it("returns false when Plus is disabled", () => {
      expect(
        shouldShowLoginMethodSelector(
          PLUS_DISABLED,
          SSO_ENABLED,
          USERNAME_PASSWORD_ALLOWED,
        ),
      ).toBe(false);
    });

    it("returns false when SSO is disabled", () => {
      expect(
        shouldShowLoginMethodSelector(
          PLUS_ENABLED,
          SSO_DISABLED,
          USERNAME_PASSWORD_ALLOWED,
        ),
      ).toBe(false);
    });

    it("returns false when username/password is not allowed", () => {
      expect(
        shouldShowLoginMethodSelector(
          PLUS_ENABLED,
          SSO_ENABLED,
          USERNAME_PASSWORD_NOT_ALLOWED,
        ),
      ).toBe(false);
    });

    it("handles undefined allowUsernameAndPassword parameter", () => {
      expect(
        shouldShowLoginMethodSelector(PLUS_ENABLED, SSO_ENABLED, undefined),
      ).toBe(false);
    });
  });

  describe("shouldShowPasswordField", () => {
    it("returns false when not a new user", () => {
      expect(
        shouldShowPasswordField(
          EXISTING_USER,
          NO_EMAIL_INVITE,
          PLUS_ENABLED,
          SSO_ENABLED,
          USERNAME_PASSWORD_ALLOWED,
          LOGIN_USERNAME_PASSWORD,
        ),
      ).toBe(false);
    });

    it("returns false when inviting users via email", () => {
      expect(
        shouldShowPasswordField(
          NEW_USER,
          INVITE_BY_EMAIL,
          PLUS_ENABLED,
          SSO_ENABLED,
          USERNAME_PASSWORD_ALLOWED,
          LOGIN_USERNAME_PASSWORD,
        ),
      ).toBe(false);
    });

    it("returns true when Plus is disabled for new users", () => {
      expect(
        shouldShowPasswordField(
          NEW_USER,
          NO_EMAIL_INVITE,
          PLUS_DISABLED,
          SSO_DISABLED,
          USERNAME_PASSWORD_NOT_ALLOWED,
          undefined,
        ),
      ).toBe(true);
    });

    it("returns false when Plus is disabled for new users and email invite is enabled", () => {
      expect(
        shouldShowPasswordField(
          NEW_USER,
          INVITE_BY_EMAIL,
          PLUS_DISABLED,
          SSO_DISABLED,
          USERNAME_PASSWORD_NOT_ALLOWED,
          undefined,
        ),
      ).toBe(false);
    });

    it("returns true when SSO is disabled for new users", () => {
      expect(
        shouldShowPasswordField(
          NEW_USER,
          NO_EMAIL_INVITE,
          PLUS_ENABLED,
          SSO_DISABLED,
          USERNAME_PASSWORD_NOT_ALLOWED,
          undefined,
        ),
      ).toBe(true);
    });

    it("returns true when using username/password login with SSO", () => {
      expect(
        shouldShowPasswordField(
          NEW_USER,
          NO_EMAIL_INVITE,
          PLUS_ENABLED,
          SSO_ENABLED,
          USERNAME_PASSWORD_ALLOWED,
          LOGIN_USERNAME_PASSWORD,
        ),
      ).toBe(true);
    });

    it("returns false when using SSO login", () => {
      expect(
        shouldShowPasswordField(
          NEW_USER,
          NO_EMAIL_INVITE,
          PLUS_ENABLED,
          SSO_ENABLED,
          USERNAME_PASSWORD_ALLOWED,
          LOGIN_SSO,
        ),
      ).toBe(false);
    });

    it("handles undefined loginMethod when other conditions would allow password field", () => {
      expect(
        shouldShowPasswordField(
          NEW_USER,
          NO_EMAIL_INVITE,
          PLUS_ENABLED,
          SSO_ENABLED,
          USERNAME_PASSWORD_ALLOWED,
          undefined,
        ),
      ).toBe(false);
    });

    it("handles undefined allowUsernameAndPassword", () => {
      expect(
        shouldShowPasswordField(
          NEW_USER,
          NO_EMAIL_INVITE,
          PLUS_ENABLED,
          SSO_ENABLED,
          undefined,
          LOGIN_USERNAME_PASSWORD,
        ),
      ).toBe(false);
    });

    it("returns false when Plus and SSO enabled but allowUsernameAndPassword is false", () => {
      expect(
        shouldShowPasswordField(
          NEW_USER,
          NO_EMAIL_INVITE,
          PLUS_ENABLED,
          SSO_ENABLED,
          USERNAME_PASSWORD_NOT_ALLOWED,
          LOGIN_USERNAME_PASSWORD,
        ),
      ).toBe(false);
    });
  });

  describe("shouldShowPasswordManagement", () => {
    it("returns true when Plus is disabled", () => {
      expect(
        shouldShowPasswordManagement(
          PLUS_DISABLED,
          SSO_ENABLED,
          USERNAME_PASSWORD_ALLOWED,
          LOGIN_SSO,
        ),
      ).toBe(true);
    });

    it("returns true when Plus is enabled but SSO is disabled", () => {
      expect(
        shouldShowPasswordManagement(
          PLUS_ENABLED,
          SSO_DISABLED,
          USERNAME_PASSWORD_ALLOWED,
          LOGIN_SSO,
        ),
      ).toBe(true);
    });

    it("returns true when using username/password login with Plus and SSO", () => {
      expect(
        shouldShowPasswordManagement(
          PLUS_ENABLED,
          SSO_ENABLED,
          USERNAME_PASSWORD_ALLOWED,
          LOGIN_USERNAME_PASSWORD,
        ),
      ).toBe(true);
    });

    it("returns false when using SSO login with Plus and SSO", () => {
      expect(
        shouldShowPasswordManagement(
          PLUS_ENABLED,
          SSO_ENABLED,
          USERNAME_PASSWORD_ALLOWED,
          LOGIN_SSO,
        ),
      ).toBe(false);
    });

    it("handles undefined loginMethod parameter", () => {
      expect(
        shouldShowPasswordManagement(
          PLUS_ENABLED,
          SSO_ENABLED,
          USERNAME_PASSWORD_ALLOWED,
          undefined,
        ),
      ).toBe(false);
    });

    it("handles null loginMethod parameter", () => {
      expect(
        shouldShowPasswordManagement(
          PLUS_ENABLED,
          SSO_ENABLED,
          USERNAME_PASSWORD_ALLOWED,
          null,
        ),
      ).toBe(false);
    });

    it("returns false when allowUsernameAndPassword is false with Plus and SSO", () => {
      expect(
        shouldShowPasswordManagement(
          PLUS_ENABLED,
          SSO_ENABLED,
          USERNAME_PASSWORD_NOT_ALLOWED,
          LOGIN_USERNAME_PASSWORD,
        ),
      ).toBe(false);
    });

    it("returns false when allowUsernameAndPassword is undefined with Plus and SSO", () => {
      expect(
        shouldShowPasswordManagement(
          PLUS_ENABLED,
          SSO_ENABLED,
          undefined,
          LOGIN_USERNAME_PASSWORD,
        ),
      ).toBe(false);
    });
  });

  describe("isPasswordFieldRequired", () => {
    it("returns false when not a new user", () => {
      expect(
        isPasswordFieldRequired(
          EXISTING_USER,
          NO_EMAIL_INVITE,
          PLUS_ENABLED,
          SSO_ENABLED,
          USERNAME_PASSWORD_ALLOWED,
          LOGIN_USERNAME_PASSWORD,
        ),
      ).toBe(false);
    });

    it("returns false when inviting users via email", () => {
      expect(
        isPasswordFieldRequired(
          NEW_USER,
          INVITE_BY_EMAIL,
          PLUS_ENABLED,
          SSO_ENABLED,
          USERNAME_PASSWORD_ALLOWED,
          LOGIN_USERNAME_PASSWORD,
        ),
      ).toBe(false);
    });

    it("returns true when Plus is disabled for new users", () => {
      expect(
        isPasswordFieldRequired(
          NEW_USER,
          NO_EMAIL_INVITE,
          PLUS_DISABLED,
          SSO_DISABLED,
          USERNAME_PASSWORD_NOT_ALLOWED,
          undefined,
        ),
      ).toBe(true);
    });

    it("returns true when SSO is disabled for new users", () => {
      expect(
        isPasswordFieldRequired(
          NEW_USER,
          NO_EMAIL_INVITE,
          PLUS_ENABLED,
          SSO_DISABLED,
          USERNAME_PASSWORD_NOT_ALLOWED,
          undefined,
        ),
      ).toBe(true);
    });

    it("returns true when using username/password login with SSO", () => {
      expect(
        isPasswordFieldRequired(
          NEW_USER,
          NO_EMAIL_INVITE,
          PLUS_ENABLED,
          SSO_ENABLED,
          USERNAME_PASSWORD_ALLOWED,
          LOGIN_USERNAME_PASSWORD,
        ),
      ).toBe(true);
    });

    it("returns false when using SSO login", () => {
      expect(
        isPasswordFieldRequired(
          NEW_USER,
          NO_EMAIL_INVITE,
          PLUS_ENABLED,
          SSO_ENABLED,
          USERNAME_PASSWORD_ALLOWED,
          LOGIN_SSO,
        ),
      ).toBe(false);
    });

    it("handles undefined loginMethod when other conditions would require password", () => {
      expect(
        isPasswordFieldRequired(
          NEW_USER,
          NO_EMAIL_INVITE,
          PLUS_ENABLED,
          SSO_ENABLED,
          USERNAME_PASSWORD_ALLOWED,
          undefined,
        ),
      ).toBe(false);
    });

    it("returns false when all conditions are true except allowUsernameAndPassword is false", () => {
      expect(
        isPasswordFieldRequired(
          NEW_USER,
          NO_EMAIL_INVITE,
          PLUS_ENABLED,
          SSO_ENABLED,
          USERNAME_PASSWORD_NOT_ALLOWED,
          LOGIN_USERNAME_PASSWORD,
        ),
      ).toBe(false);
    });
  });
});
