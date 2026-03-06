import loadEnvironmentVariables, {
  DEFAULT_ATTRIBUTION_ANCHOR_TEXT,
  DEFAULT_ATTRIBUTION_DESTINATION_URL,
} from "~/app/server-utils/loadEnvironmentVariables";

describe("loadEnvironmentVariables", () => {
  const originalEnv = process.env;

  beforeEach(() => {
    process.env = { ...originalEnv };
  });

  afterEach(() => {
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
    it("defaults to DEFAULT_ATTRIBUTION_ANCHOR_TEXT", () => {
      delete process.env.FIDES_PRIVACY_CENTER__ATTRIBUTION_ANCHOR_TEXT;
      const settings = loadEnvironmentVariables();
      expect(settings.ATTRIBUTION_ANCHOR_TEXT).toBe(
        DEFAULT_ATTRIBUTION_ANCHOR_TEXT,
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
    it("defaults to DEFAULT_ATTRIBUTION_DESTINATION_URL", () => {
      delete process.env.FIDES_PRIVACY_CENTER__ATTRIBUTION_DESTINATION_URL;
      const settings = loadEnvironmentVariables();
      expect(settings.ATTRIBUTION_DESTINATION_URL).toBe(
        DEFAULT_ATTRIBUTION_DESTINATION_URL,
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
