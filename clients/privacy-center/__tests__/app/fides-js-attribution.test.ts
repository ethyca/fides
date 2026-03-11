import type { AttributionOptions } from "fides-js";

import {
  buildAttributionOptions,
  getClientSettings,
} from "~/app/server-environment";
import {
  DEFAULT_ATTRIBUTION_ANCHOR_TEXT,
  DEFAULT_ATTRIBUTION_DESTINATION_URL,
} from "~/app/server-utils/loadEnvironmentVariables";

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
      DEFAULT_ATTRIBUTION_ANCHOR_TEXT,
    );
    expect(settings.ATTRIBUTION_DESTINATION_URL).toBe(
      DEFAULT_ATTRIBUTION_DESTINATION_URL,
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
 * Tests the config-building logic used in the /api/fides-js handler
 * via the shared buildAttributionOptions helper.
 */
describe("fides-js handler attribution config building", () => {
  const originalEnv = process.env;

  beforeEach(() => {
    process.env = { ...originalEnv };
  });

  afterEach(() => {
    process.env = originalEnv;
  });

  it("produces undefined attribution when disabled", () => {
    delete process.env.FIDES_PRIVACY_CENTER__ATTRIBUTION_ENABLED;
    expect(buildAttributionOptions(getClientSettings())).toBeUndefined();
  });

  it("produces attribution object with defaults when enabled", () => {
    process.env.FIDES_PRIVACY_CENTER__ATTRIBUTION_ENABLED = "true";
    expect(buildAttributionOptions(getClientSettings())).toEqual({
      anchorText: DEFAULT_ATTRIBUTION_ANCHOR_TEXT,
      destinationUrl: DEFAULT_ATTRIBUTION_DESTINATION_URL,
      nofollow: false,
    });
  });

  it("produces attribution object with custom values when overridden", () => {
    process.env.FIDES_PRIVACY_CENTER__ATTRIBUTION_ENABLED = "true";
    process.env.FIDES_PRIVACY_CENTER__ATTRIBUTION_ANCHOR_TEXT = "Powered by X";
    process.env.FIDES_PRIVACY_CENTER__ATTRIBUTION_DESTINATION_URL =
      "https://x.example.com";
    process.env.FIDES_PRIVACY_CENTER__ATTRIBUTION_NOFOLLOW = "true";
    expect(buildAttributionOptions(getClientSettings())).toEqual({
      anchorText: "Powered by X",
      destinationUrl: "https://x.example.com",
      nofollow: true,
    });
  });

  it("serializes cleanly to JSON without attribution when disabled", () => {
    delete process.env.FIDES_PRIVACY_CENTER__ATTRIBUTION_ENABLED;
    const attribution = buildAttributionOptions(getClientSettings());
    const options = { attribution, otherField: true };
    const parsed = JSON.parse(JSON.stringify(options));
    expect(parsed).not.toHaveProperty("attribution");
  });

  it("serializes attribution to JSON when enabled", () => {
    process.env.FIDES_PRIVACY_CENTER__ATTRIBUTION_ENABLED = "true";
    const attribution = buildAttributionOptions(getClientSettings());
    const options = { attribution, otherField: true };
    const parsed = JSON.parse(JSON.stringify(options));
    expect(parsed.attribution).toEqual({
      anchorText: DEFAULT_ATTRIBUTION_ANCHOR_TEXT,
      destinationUrl: DEFAULT_ATTRIBUTION_DESTINATION_URL,
      nofollow: false,
    });
  });
});

describe("AttributionLink component rendering logic", () => {
  const buildRelAttribute = (attribution: AttributionOptions): string =>
    `noopener noreferrer${attribution.nofollow ? " nofollow" : ""}`;

  it("produces correct rel attribute without nofollow", () => {
    const attribution: AttributionOptions = {
      anchorText: "Powered by Ethyca",
      destinationUrl: "https://ethyca.com",
      nofollow: false,
    };
    expect(buildRelAttribute(attribution)).toBe("noopener noreferrer");
  });

  it("produces correct rel attribute with nofollow", () => {
    const attribution: AttributionOptions = {
      anchorText: "Powered by Ethyca",
      destinationUrl: "https://ethyca.com",
      nofollow: true,
    };
    expect(buildRelAttribute(attribution)).toBe("noopener noreferrer nofollow");
  });

  it("uses custom anchor text and destination URL", () => {
    process.env.FIDES_PRIVACY_CENTER__ATTRIBUTION_ENABLED = "true";
    process.env.FIDES_PRIVACY_CENTER__ATTRIBUTION_ANCHOR_TEXT =
      "Privacy by Custom";
    process.env.FIDES_PRIVACY_CENTER__ATTRIBUTION_DESTINATION_URL =
      "https://custom.example.com";
    const attribution = buildAttributionOptions(getClientSettings());
    expect(attribution).toBeDefined();
    expect(attribution!.anchorText).toBe("Privacy by Custom");
    expect(attribution!.destinationUrl).toBe("https://custom.example.com");
  });
});
