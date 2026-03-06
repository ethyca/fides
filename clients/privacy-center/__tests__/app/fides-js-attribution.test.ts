import type { AttributionOptions } from "fides-js";

import { getClientSettings } from "~/app/server-environment";

describe("fides-js attribution config", () => {
  const originalEnv = process.env;

  beforeEach(() => {
    process.env = { ...originalEnv };
  });

  afterEach(() => {
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

/**
 * Tests the config-building logic used in the /api/fides-js handler.
 * This mirrors the ternary in pages/api/fides-js.ts that maps
 * PrivacyCenterClientSettings -> FidesConfig.options.attribution.
 */
describe("fides-js handler attribution config building", () => {
  const originalEnv = process.env;

  beforeEach(() => {
    process.env = { ...originalEnv };
  });

  afterEach(() => {
    process.env = originalEnv;
  });

  function buildAttributionFromSettings(): AttributionOptions | undefined {
    const settings = getClientSettings();
    return settings.ATTRIBUTION_ENABLED
      ? {
          anchorText: settings.ATTRIBUTION_ANCHOR_TEXT,
          destinationUrl: settings.ATTRIBUTION_DESTINATION_URL,
          nofollow: settings.ATTRIBUTION_NOFOLLOW,
        }
      : undefined;
  }

  it("produces undefined attribution when disabled", () => {
    delete process.env.FIDES_PRIVACY_CENTER__ATTRIBUTION_ENABLED;
    expect(buildAttributionFromSettings()).toBeUndefined();
  });

  it("produces attribution object with defaults when enabled", () => {
    process.env.FIDES_PRIVACY_CENTER__ATTRIBUTION_ENABLED = "true";
    expect(buildAttributionFromSettings()).toEqual({
      anchorText: "Consent powered by Ethyca",
      destinationUrl: "https://ethyca.com/consent",
      nofollow: false,
    });
  });

  it("produces attribution object with custom values when overridden", () => {
    process.env.FIDES_PRIVACY_CENTER__ATTRIBUTION_ENABLED = "true";
    process.env.FIDES_PRIVACY_CENTER__ATTRIBUTION_ANCHOR_TEXT = "Powered by X";
    process.env.FIDES_PRIVACY_CENTER__ATTRIBUTION_DESTINATION_URL =
      "https://x.example.com";
    process.env.FIDES_PRIVACY_CENTER__ATTRIBUTION_NOFOLLOW = "true";
    expect(buildAttributionFromSettings()).toEqual({
      anchorText: "Powered by X",
      destinationUrl: "https://x.example.com",
      nofollow: true,
    });
  });

  it("serializes cleanly to JSON without attribution when disabled", () => {
    delete process.env.FIDES_PRIVACY_CENTER__ATTRIBUTION_ENABLED;
    const attribution = buildAttributionFromSettings();
    const options = { attribution, otherField: true };
    const parsed = JSON.parse(JSON.stringify(options));
    expect(parsed).not.toHaveProperty("attribution");
  });

  it("serializes attribution to JSON when enabled", () => {
    process.env.FIDES_PRIVACY_CENTER__ATTRIBUTION_ENABLED = "true";
    const attribution = buildAttributionFromSettings();
    const options = { attribution, otherField: true };
    const parsed = JSON.parse(JSON.stringify(options));
    expect(parsed.attribution).toEqual({
      anchorText: "Consent powered by Ethyca",
      destinationUrl: "https://ethyca.com/consent",
      nofollow: false,
    });
  });
});
