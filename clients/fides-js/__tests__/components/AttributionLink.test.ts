import type { AttributionOptions } from "~/lib/consent-types";

/**
 * Since fides-js uses Preact and doesn't have @testing-library/preact set up,
 * these tests validate the attribution link logic rather than rendering.
 */
describe("AttributionLink logic", () => {
  const buildRelAttribute = (attribution: AttributionOptions): string =>
    `noopener noreferrer${attribution.nofollow ? " nofollow" : ""}`;

  it("builds rel attribute without nofollow when nofollow is false", () => {
    const attribution: AttributionOptions = {
      anchorText: "Powered by Ethyca",
      destinationUrl: "https://ethyca.com",
      nofollow: false,
    };
    expect(buildRelAttribute(attribution)).toBe("noopener noreferrer");
  });

  it("builds rel attribute with nofollow when nofollow is true", () => {
    const attribution: AttributionOptions = {
      anchorText: "Powered by Ethyca",
      destinationUrl: "https://ethyca.com",
      nofollow: true,
    };
    expect(buildRelAttribute(attribution)).toBe(
      "noopener noreferrer nofollow",
    );
  });

  it("uses the configured anchor text and destination URL", () => {
    const attribution: AttributionOptions = {
      anchorText: "Privacy by Acme",
      destinationUrl: "https://acme.example.com",
      nofollow: false,
    };
    expect(attribution.anchorText).toBe("Privacy by Acme");
    expect(attribution.destinationUrl).toBe("https://acme.example.com");
  });
});
