import { getClientSettings } from "~/app/server-environment";

describe("fides-js attribution config", () => {
  const originalEnv = process.env;

  beforeEach(() => {
    jest.resetModules();
    process.env = { ...originalEnv };
  });

  afterAll(() => {
    process.env = originalEnv;
  });

  it("does not include attribution fields when ATTRIBUTION_ENABLED is false", () => {
    delete process.env.FIDES_PRIVACY_CENTER__ATTRIBUTION_ENABLED;
    const settings = getClientSettings();
    expect(settings.ATTRIBUTION_ENABLED).toBe(false);
  });

  it("includes attribution fields when ATTRIBUTION_ENABLED is true", () => {
    process.env.FIDES_PRIVACY_CENTER__ATTRIBUTION_ENABLED = "true";
    const settings = getClientSettings();
    expect(settings.ATTRIBUTION_ENABLED).toBe(true);
    expect(settings.ATTRIBUTION_ANCHOR_TEXT).toBe(
      "Consent powered by Ethyca",
    );
    expect(settings.ATTRIBUTION_DESTINATION_URL).toBe(
      "https://ethyca.com/consent",
    );
    expect(settings.ATTRIBUTION_NOFOLLOW).toBe(false);
  });

  it("includes custom attribution values when overridden", () => {
    process.env.FIDES_PRIVACY_CENTER__ATTRIBUTION_ENABLED = "true";
    process.env.FIDES_PRIVACY_CENTER__ATTRIBUTION_ANCHOR_TEXT =
      "Privacy by Acme";
    process.env.FIDES_PRIVACY_CENTER__ATTRIBUTION_DESTINATION_URL =
      "https://acme.example.com";
    process.env.FIDES_PRIVACY_CENTER__ATTRIBUTION_NOFOLLOW = "true";
    const settings = getClientSettings();
    expect(settings.ATTRIBUTION_ENABLED).toBe(true);
    expect(settings.ATTRIBUTION_ANCHOR_TEXT).toBe("Privacy by Acme");
    expect(settings.ATTRIBUTION_DESTINATION_URL).toBe(
      "https://acme.example.com",
    );
    expect(settings.ATTRIBUTION_NOFOLLOW).toBe(true);
  });

  it("preserves SHOW_BRAND_LINK regardless of attribution state", () => {
    process.env.FIDES_PRIVACY_CENTER__ATTRIBUTION_ENABLED = "true";
    const settingsEnabled = getClientSettings();
    expect(settingsEnabled.SHOW_BRAND_LINK).toBeDefined();

    delete process.env.FIDES_PRIVACY_CENTER__ATTRIBUTION_ENABLED;
    const settingsDisabled = getClientSettings();
    expect(settingsDisabled.SHOW_BRAND_LINK).toBeDefined();
  });
});
