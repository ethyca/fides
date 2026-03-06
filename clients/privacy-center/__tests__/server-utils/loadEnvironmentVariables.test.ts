import loadEnvironmentVariables from "~/app/server-utils/loadEnvironmentVariables";

describe("loadEnvironmentVariables", () => {
  const originalEnv = process.env;

  beforeEach(() => {
    jest.resetModules();
    process.env = { ...originalEnv };
  });

  afterAll(() => {
    process.env = originalEnv;
  });

  describe("ATTRIBUTION_ENABLED", () => {
    it("defaults to false when not set", () => {
      delete process.env.FIDES_PRIVACY_CENTER__ATTRIBUTION_ENABLED;
      const settings = loadEnvironmentVariables();
      expect(settings.ATTRIBUTION_ENABLED).toBe(false);
    });

    it('is true when set to "true"', () => {
      process.env.FIDES_PRIVACY_CENTER__ATTRIBUTION_ENABLED = "true";
      const settings = loadEnvironmentVariables();
      expect(settings.ATTRIBUTION_ENABLED).toBe(true);
    });

    it("is false for any other value", () => {
      process.env.FIDES_PRIVACY_CENTER__ATTRIBUTION_ENABLED = "yes";
      const settings = loadEnvironmentVariables();
      expect(settings.ATTRIBUTION_ENABLED).toBe(false);
    });
  });

  describe("ATTRIBUTION_ANCHOR_TEXT", () => {
    it('defaults to "Consent powered by Ethyca"', () => {
      delete process.env.FIDES_PRIVACY_CENTER__ATTRIBUTION_ANCHOR_TEXT;
      const settings = loadEnvironmentVariables();
      expect(settings.ATTRIBUTION_ANCHOR_TEXT).toBe(
        "Consent powered by Ethyca",
      );
    });

    it("can be overridden", () => {
      process.env.FIDES_PRIVACY_CENTER__ATTRIBUTION_ANCHOR_TEXT =
        "Custom text";
      const settings = loadEnvironmentVariables();
      expect(settings.ATTRIBUTION_ANCHOR_TEXT).toBe("Custom text");
    });
  });

  describe("ATTRIBUTION_DESTINATION_URL", () => {
    it('defaults to "https://ethyca.com/consent"', () => {
      delete process.env.FIDES_PRIVACY_CENTER__ATTRIBUTION_DESTINATION_URL;
      const settings = loadEnvironmentVariables();
      expect(settings.ATTRIBUTION_DESTINATION_URL).toBe(
        "https://ethyca.com/consent",
      );
    });

    it("can be overridden", () => {
      process.env.FIDES_PRIVACY_CENTER__ATTRIBUTION_DESTINATION_URL =
        "https://custom.example.com";
      const settings = loadEnvironmentVariables();
      expect(settings.ATTRIBUTION_DESTINATION_URL).toBe(
        "https://custom.example.com",
      );
    });
  });

  describe("ATTRIBUTION_NOFOLLOW", () => {
    it("defaults to false when not set", () => {
      delete process.env.FIDES_PRIVACY_CENTER__ATTRIBUTION_NOFOLLOW;
      const settings = loadEnvironmentVariables();
      expect(settings.ATTRIBUTION_NOFOLLOW).toBe(false);
    });

    it('is true when set to "true"', () => {
      process.env.FIDES_PRIVACY_CENTER__ATTRIBUTION_NOFOLLOW = "true";
      const settings = loadEnvironmentVariables();
      expect(settings.ATTRIBUTION_NOFOLLOW).toBe(true);
    });

    it("is false for any other value", () => {
      process.env.FIDES_PRIVACY_CENTER__ATTRIBUTION_NOFOLLOW = "yes";
      const settings = loadEnvironmentVariables();
      expect(settings.ATTRIBUTION_NOFOLLOW).toBe(false);
    });
  });
});
