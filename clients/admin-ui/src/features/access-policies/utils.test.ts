import { extractPolicyFields, updateYamlField } from "./policy-yaml";
import { formatRelativeTime } from "./utils";

describe("formatRelativeTime", () => {
  it("returns em dash for undefined", () => {
    expect(formatRelativeTime(undefined)).toBe("—");
  });

  it("returns 'Just now' for a date less than 1 minute ago", () => {
    const recent = new Date(Date.now() - 30 * 1000).toISOString();
    expect(formatRelativeTime(recent)).toBe("Just now");
  });

  it("returns minutes ago for dates within the hour", () => {
    const thirtyMinAgo = new Date(Date.now() - 30 * 60 * 1000).toISOString();
    expect(formatRelativeTime(thirtyMinAgo)).toBe("30m ago");
  });

  it("returns hours ago for dates within the day", () => {
    const threeHoursAgo = new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString();
    expect(formatRelativeTime(threeHoursAgo)).toBe("3h ago");
  });

  it("returns days ago for older dates", () => {
    const twoDaysAgo = new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString();
    expect(formatRelativeTime(twoDaysAgo)).toBe("2d ago");
  });
});

describe("extractPolicyFields", () => {
  it("returns defaults when yaml is undefined", () => {
    expect(extractPolicyFields(undefined)).toEqual({
      enabled: true,
      priority: 0,
      decision: undefined,
    });
  });

  it("returns defaults when yaml is invalid", () => {
    expect(extractPolicyFields("not: valid: yaml: [[")).toEqual({
      enabled: true,
      priority: 0,
      decision: undefined,
    });
  });

  it("extracts enabled, priority, and decision from valid yaml", () => {
    const yamlString =
      "fides_key: test\nname: Test\nenabled: false\npriority: 200\ndecision: DENY\nmatch:\n  data_use:\n    any:\n      - marketing\n";
    expect(extractPolicyFields(yamlString)).toEqual({
      enabled: false,
      priority: 200,
      decision: "DENY",
    });
  });

  it("defaults enabled to true when not present in yaml", () => {
    const yamlString =
      "fides_key: test\nname: Test\npriority: 100\ndecision: ALLOW\nmatch:\n  data_use:\n    any:\n      - essential\n";
    const result = extractPolicyFields(yamlString);
    expect(result.enabled).toBe(true);
  });

  it("defaults priority to 0 when not present in yaml", () => {
    const yamlString =
      "fides_key: test\nname: Test\ndecision: ALLOW\nmatch:\n  data_use:\n    any:\n      - essential\n";
    const result = extractPolicyFields(yamlString);
    expect(result.priority).toBe(0);
  });
});

describe("updateYamlField", () => {
  const baseYaml =
    "fides_key: test\nname: Test Policy\nenabled: true\npriority: 100\n";

  it("updates an existing boolean field", () => {
    const result = updateYamlField(baseYaml, "enabled", false);
    expect(result).toContain("enabled: false");
  });

  it("updates an existing numeric field", () => {
    const result = updateYamlField(baseYaml, "priority", 500);
    expect(result).toContain("priority: 500");
  });

  it("adds a new field that did not exist", () => {
    const result = updateYamlField(baseYaml, "decision", "DENY");
    expect(result).toContain("decision: DENY");
  });

  it("returns the original string when yaml is unparseable", () => {
    const invalid = "not: valid: yaml: [[";
    expect(updateYamlField(invalid, "enabled", false)).toBe(invalid);
  });

  it("preserves other fields when updating one", () => {
    const result = updateYamlField(baseYaml, "priority", 999);
    expect(result).toContain("fides_key: test");
    expect(result).toContain("name: Test Policy");
    expect(result).toContain("enabled: true");
  });
});
