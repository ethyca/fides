import {
  diffPolicies,
  extractPolicyFields,
  updateYamlField,
} from "./policy-yaml";
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
    const threeHoursAgo = new Date(
      Date.now() - 3 * 60 * 60 * 1000,
    ).toISOString();
    expect(formatRelativeTime(threeHoursAgo)).toBe("3h ago");
  });

  it("returns days ago for older dates", () => {
    const twoDaysAgo = new Date(
      Date.now() - 2 * 24 * 60 * 60 * 1000,
    ).toISOString();
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

describe("diffPolicies", () => {
  const baseYaml = [
    "name: Sample",
    "decision: ALLOW",
    "match:",
    "  data_use:",
    "    any:",
    "      - marketing",
    "",
  ].join("\n");

  it("returns no changes when both yamls are identical", () => {
    const diff = diffPolicies(baseYaml, baseYaml);
    expect(diff.hasChanges).toBe(false);
    expect(diff.summary).toEqual({ added: [], modified: [], removed: [] });
    expect(diff.policyMetadata).toBe("unchanged");
    expect(diff.action).toBe("unchanged");
  });

  it("treats every section as added when oldYaml is undefined", () => {
    const diff = diffPolicies(undefined, baseYaml);
    expect(diff.hasChanges).toBe(true);
    expect(diff.policyMetadata).toBe("added");
    expect(diff.action).toBe("added");
    expect(diff.conditions.data_use).toBe("added");
    expect(diff.summary.added).toContain("policy details");
    expect(diff.summary.added).toContain("decision");
    expect(diff.summary.added).toContain("data use condition");
  });

  it("flags a newly added condition", () => {
    const newYaml = baseYaml.replace(
      "match:\n  data_use:\n    any:\n      - marketing",
      [
        "match:",
        "  data_use:",
        "    any:",
        "      - marketing",
        "  data_category:",
        "    all:",
        "      - user.behavior",
      ].join("\n"),
    );
    const diff = diffPolicies(baseYaml, newYaml);
    expect(diff.hasChanges).toBe(true);
    expect(diff.conditions.data_category).toBe("added");
    expect(diff.conditions.data_use).toBe("unchanged");
    expect(diff.summary.added).toContain("data category condition");
  });

  it("flags a removed condition via removedConditionProperties", () => {
    const dualYaml = [
      "name: Sample",
      "decision: ALLOW",
      "match:",
      "  data_use:",
      "    any:",
      "      - marketing",
      "  data_category:",
      "    all:",
      "      - user.behavior",
      "",
    ].join("\n");
    const diff = diffPolicies(dualYaml, baseYaml);
    expect(diff.removedConditionProperties).toContain("data_category");
    expect(diff.summary.removed).toContain("data category condition");
  });

  it("flags a modified condition when values change", () => {
    const newYaml = baseYaml.replace("- marketing", "- analytics");
    const diff = diffPolicies(baseYaml, newYaml);
    expect(diff.conditions.data_use).toBe("modified");
    expect(diff.summary.modified).toContain("data use condition");
  });

  it("flags a modified condition when operator changes from any to all", () => {
    const newYaml = baseYaml.replace(
      "  data_use:\n    any:\n      - marketing",
      "  data_use:\n    all:\n      - marketing",
    );
    const diff = diffPolicies(baseYaml, newYaml);
    expect(diff.conditions.data_use).toBe("modified");
  });

  it("flags an added geo_location constraint", () => {
    const newYaml = `${baseYaml}unless:\n  - type: geo_location\n    field: environment.geo_location\n    operator: in\n    values:\n      - US-CA\n`;
    const diff = diffPolicies(baseYaml, newYaml);
    expect(diff.constraints).toEqual([
      { matchKey: "geo_location:environment.geo_location", status: "added" },
    ]);
    expect(diff.summary.added).toContain("geo_location constraint");
  });

  it("flags a modified consent constraint when requirement changes", () => {
    const oldWithConsent = `${baseYaml}unless:\n  - type: consent\n    privacy_notice_key: marketing\n    requirement: opt_in\n`;
    const newWithConsent = `${baseYaml}unless:\n  - type: consent\n    privacy_notice_key: marketing\n    requirement: opt_out\n`;
    const diff = diffPolicies(oldWithConsent, newWithConsent);
    expect(diff.constraints).toEqual([
      { matchKey: "consent:marketing", status: "modified" },
    ]);
    expect(diff.summary.modified).toContain("consent constraint (marketing)");
  });

  it("flags a removed constraint when it disappears", () => {
    const oldWithConstraint = `${baseYaml}unless:\n  - type: geo_location\n    field: environment.geo_location\n    operator: in\n    values:\n      - US-CA\n`;
    const diff = diffPolicies(oldWithConstraint, baseYaml);
    expect(diff.removedConstraintKeys).toContain(
      "geo_location:environment.geo_location",
    );
    expect(diff.summary.removed).toContain("geo_location constraint");
  });

  it("flags policy metadata change when the name changes", () => {
    const newYaml = baseYaml.replace("name: Sample", "name: Renamed");
    const diff = diffPolicies(baseYaml, newYaml);
    expect(diff.policyMetadata).toBe("modified");
    expect(diff.summary.modified).toContain("policy details");
  });

  it("flags action message change", () => {
    const oldDeny = [
      "name: Sample",
      "decision: DENY",
      "match:",
      "  data_use:",
      "    any:",
      "      - marketing",
      "action:",
      "  message: Old reason",
      "",
    ].join("\n");
    const newDeny = oldDeny.replace("Old reason", "New reason");
    const diff = diffPolicies(oldDeny, newDeny);
    expect(diff.action).toBe("modified");
    expect(diff.summary.modified).toContain("action message");
  });

  it("flags decision flip ALLOW → DENY", () => {
    const newDeny = baseYaml.replace("decision: ALLOW", "decision: DENY");
    const diff = diffPolicies(baseYaml, newDeny);
    expect(diff.action).toBe("modified");
    expect(diff.summary.modified.some((s) => s.includes("ALLOW → DENY"))).toBe(
      true,
    );
  });
});
