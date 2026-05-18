import type { Node } from "@xyflow/react";

import {
  buildUnionGraph,
  extractPolicyFields,
  nodeContentId,
  tagNodesWithDiff,
  updateYamlField,
  yamlToNodesAndEdges,
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

const BASE_YAML = [
  "name: Sample",
  "decision: ALLOW",
  "match:",
  "  data_use:",
  "    any:",
  "      - marketing",
  "unless:",
  "  - type: geo_location",
  "    field: data_subject.geo_location",
  "    operator: in",
  "    values:",
  "      - us_ca",
  "",
].join("\n");

describe("nodeContentId", () => {
  const built = yamlToNodesAndEdges(BASE_YAML)!;

  it("returns 'policy' for the policy node", () => {
    const policy = built.nodes.find((n) => n.type === "policyNode")!;
    expect(nodeContentId(policy)).toBe("policy");
  });

  it("returns 'action' for the action node", () => {
    const action = built.nodes.find((n) => n.type === "actionNode")!;
    expect(nodeContentId(action)).toBe("action");
  });

  it("returns 'condition:<dimension>' for a condition node", () => {
    const condition = built.nodes.find((n) => n.type === "conditionNode")!;
    expect(nodeContentId(condition)).toBe("condition:data_use");
  });

  it("returns 'constraint:<type>:<discriminator>' for a constraint node", () => {
    const constraint = built.nodes.find((n) => n.type === "constraintNode")!;
    expect(nodeContentId(constraint)).toBe(
      "constraint:geo_location:data_subject.geo_location",
    );
  });

  it("returns null when a constraint node has no constraintType yet", () => {
    const blank: Node = {
      id: "constraint-99",
      type: "constraintNode",
      position: { x: 0, y: 0 },
      data: {},
    };
    expect(nodeContentId(blank)).toBeNull();
  });
});

describe("tagNodesWithDiff", () => {
  const built = yamlToNodesAndEdges(BASE_YAML)!;

  it("does not mutate nodes when no ids match", () => {
    const tagged = tagNodesWithDiff(built.nodes, built.edges, [], [], 1);
    tagged.nodes.forEach((n, i) => {
      expect(n.className).toBe(built.nodes[i].className);
    });
  });

  it("applies diffStatus-added to nodes whose content id is in `added`", () => {
    const tagged = tagNodesWithDiff(
      built.nodes,
      built.edges,
      ["constraint:geo_location:data_subject.geo_location"],
      [],
      3,
    );
    const constraint = tagged.nodes.find((n) => n.type === "constraintNode")!;
    expect(constraint.className).toContain("diffStatus-added");
    expect(constraint.className).toContain("diffKey-3");
  });

  it("applies diffStatus-modified for ids in `changed`", () => {
    const tagged = tagNodesWithDiff(
      built.nodes,
      built.edges,
      [],
      ["condition:data_use"],
      5,
    );
    const condition = tagged.nodes.find((n) => n.type === "conditionNode")!;
    expect(condition.className).toContain("diffStatus-modified");
    expect(condition.className).toContain("diffKey-5");
  });

  it("applies diffStatus-removed to ghost nodes (id starting with 'removed-')", () => {
    const ghost: Node = {
      id: "removed-condition-data_use",
      type: "conditionNode",
      position: { x: 0, y: 0 },
      data: { property: "data_use" },
    };
    const tagged = tagNodesWithDiff([ghost], [], [], [], 1);
    expect(tagged.nodes[0].className).toContain("diffStatus-removed");
  });

  it("propagates removed status to incident edges", () => {
    const ghost: Node = {
      id: "removed-condition-data_use",
      type: "conditionNode",
      position: { x: 0, y: 0 },
      data: { property: "data_use" },
    };
    const tagged = tagNodesWithDiff(
      [ghost],
      [
        {
          id: "e-x",
          source: "action-1",
          target: "removed-condition-data_use",
        },
      ],
      [],
      [],
      1,
    );
    expect(tagged.edges[0].className).toContain("diffStatus-removed");
  });
});

describe("buildUnionGraph", () => {
  it("returns the new graph as-is when there are no removed ids", () => {
    const built = buildUnionGraph(BASE_YAML, BASE_YAML, []);
    expect(built.nodes.every((n) => !n.id.startsWith("removed-"))).toBe(true);
  });

  it("synthesizes ghost nodes for removed condition ids", () => {
    const oldYaml = `${BASE_YAML}\n# trailing`;
    const newYamlWithoutCondition = [
      "name: Sample",
      "decision: ALLOW",
      "match:",
      "  data_category:",
      "    all:",
      "      - user.behavior",
      "",
    ].join("\n");
    const built = buildUnionGraph(oldYaml, newYamlWithoutCondition, [
      "condition:data_use",
    ]);
    const ghost = built.nodes.find((n) =>
      n.id.startsWith("removed-condition_data_use"),
    );
    expect(ghost).toBeDefined();
    expect(ghost?.selectable).toBe(false);
  });

  it("synthesizes ghost nodes for removed constraint ids", () => {
    const newYaml = [
      "name: Sample",
      "decision: ALLOW",
      "match:",
      "  data_use:",
      "    any:",
      "      - marketing",
      "",
    ].join("\n");
    const built = buildUnionGraph(BASE_YAML, newYaml, [
      "constraint:geo_location:data_subject.geo_location",
    ]);
    expect(built.nodes.some((n) => n.id.startsWith("removed-constraint"))).toBe(
      true,
    );
  });

  it("ignores unknown removed ids without throwing", () => {
    const built = buildUnionGraph(BASE_YAML, BASE_YAML, [
      "constraint:consent:nonexistent",
      "garbage",
    ]);
    expect(built.nodes.every((n) => !n.id.startsWith("removed-"))).toBe(true);
  });
});
