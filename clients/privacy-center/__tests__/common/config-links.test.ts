import { getEffectivePrivacyCenterLinks } from "~/common/config-links";

describe("getEffectivePrivacyCenterLinks", () => {
  it("returns links when links array is non-empty", () => {
    const result = getEffectivePrivacyCenterLinks({
      links: [
        { label: "Privacy Policy", url: "https://example.com/privacy" },
        { label: "Terms of Service", url: "https://example.com/terms" },
      ],
    });
    expect(result).toEqual([
      { label: "Privacy Policy", url: "https://example.com/privacy" },
      { label: "Terms of Service", url: "https://example.com/terms" },
    ]);
  });

  it("synthesizes a single link from deprecated fields when links is absent", () => {
    const result = getEffectivePrivacyCenterLinks({
      privacy_policy_url: "https://example.com/privacy",
      privacy_policy_url_text: "Privacy Policy",
    });
    expect(result).toEqual([
      { url: "https://example.com/privacy", label: "Privacy Policy" },
    ]);
  });

  it("prefers links over deprecated fields when both are present", () => {
    const result = getEffectivePrivacyCenterLinks({
      links: [{ label: "Terms", url: "https://example.com/terms" }],
      privacy_policy_url: "https://example.com/privacy",
      privacy_policy_url_text: "Privacy Policy",
    });
    expect(result).toEqual([
      { label: "Terms", url: "https://example.com/terms" },
    ]);
  });

  it("returns empty array when links is empty and deprecated fields are absent", () => {
    expect(getEffectivePrivacyCenterLinks({})).toEqual([]);
  });

  it("falls through to deprecated fields when links is an empty array", () => {
    const result = getEffectivePrivacyCenterLinks({
      links: [],
      privacy_policy_url: "https://example.com/privacy",
      privacy_policy_url_text: "Privacy Policy",
    });
    expect(result).toEqual([
      { url: "https://example.com/privacy", label: "Privacy Policy" },
    ]);
  });
});
