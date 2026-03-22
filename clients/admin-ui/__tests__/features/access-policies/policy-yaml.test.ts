import {
  deriveLayoutEdges,
  nodesToYaml,
  parseYaml,
  yamlToNodesAndEdges,
} from "~/features/access-policies/policy-yaml";
import {
  ActionType,
  ConditionOperator,
  ConditionProperty,
  ConsentValue,
  ConstraintType,
  UserOperator,
} from "~/features/access-policies/types";

// ─── parseYaml ───────────────────────────────────────────────────────────────

describe("parseYaml", () => {
  it("returns null for empty string", () => {
    expect(parseYaml("")).toBeNull();
  });

  it("returns null for whitespace-only string", () => {
    expect(parseYaml("   \n  ")).toBeNull();
  });

  it("returns null for invalid YAML", () => {
    expect(parseYaml("{ unclosed: [bracket")).toBeNull();
  });

  it("returns null when parsed value is not an object", () => {
    expect(parseYaml("just a string")).toBeNull();
    expect(parseYaml("42")).toBeNull();
  });

  it("returns null when object is missing name field", () => {
    expect(parseYaml("description: something")).toBeNull();
  });

  it("parses minimal valid YAML", () => {
    const result = parseYaml("name: my_policy");
    expect(result).toEqual({ name: "my_policy" });
  });

  it("parses full YAML with all fields", () => {
    const yaml = `
name: full_policy
description: A complete policy
enabled: true
allow:
  data_use:
    operator: any
    values:
      - essential
`;
    const result = parseYaml(yaml);
    expect(result?.name).toBe("full_policy");
    expect(result?.description).toBe("A complete policy");
    expect(result?.enabled).toBe(true);
    expect(result?.allow?.data_use?.operator).toBe("any");
    expect(result?.allow?.data_use?.values).toEqual(["essential"]);
  });
});

// ─── yamlToNodesAndEdges ─────────────────────────────────────────────────────

describe("yamlToNodesAndEdges", () => {
  it("returns null for invalid YAML", () => {
    expect(yamlToNodesAndEdges("not: [valid")).toBeNull();
  });

  it("returns null for YAML without name", () => {
    expect(yamlToNodesAndEdges("description: no name")).toBeNull();
  });

  it("returns policy node only when no allow/deny block", () => {
    const result = yamlToNodesAndEdges(
      "name: bare_policy\ndescription: no rules",
    );
    expect(result).not.toBeNull();
    expect(result!.nodes).toHaveLength(1);
    expect(result!.nodes[0].id).toBe("policy");
    expect(result!.edges).toHaveLength(0);
  });

  it("creates policy + action + condition for single allow condition", () => {
    const yaml = `
name: simple_allow
allow:
  data_use:
    operator: any
    values:
      - essential
`;
    const result = yamlToNodesAndEdges(yaml);
    expect(result).not.toBeNull();
    const { nodes, edges } = result!;

    expect(nodes).toHaveLength(3); // policy, action, condition
    expect(nodes.find((n) => n.id === "policy")).toBeDefined();
    expect(nodes.find((n) => n.id === "action-1")).toBeDefined();
    expect(nodes.find((n) => n.id === "condition-1")).toBeDefined();

    const actionNode = nodes.find((n) => n.id === "action-1")!;
    expect(actionNode.data.actionType).toBe(ActionType.ALLOW);

    const conditionNode = nodes.find((n) => n.id === "condition-1")!;
    expect(conditionNode.data.property).toBe(ConditionProperty.DATA_USE);
    expect(conditionNode.data.values).toEqual(["essential"]);
    expect(conditionNode.data.operator).toBe(ConditionOperator.ANY);

    // Edges: policy→action (no label), action→condition-1 (when)
    expect(edges).toHaveLength(2);
    const conditionEdge = edges.find((e) => e.target === "condition-1")!;
    expect(conditionEdge.source).toBe("action-1");
    expect(conditionEdge.data?.label).toBe("when");
  });

  it("creates deny action for deny block", () => {
    const yaml = `
name: deny_policy
deny:
  data_use:
    operator: any
    values:
      - marketing.advertising
`;
    const result = yamlToNodesAndEdges(yaml);
    const actionNode = result!.nodes.find((n) => n.id === "action-1")!;
    expect(actionNode.data.actionType).toBe(ActionType.DENY);
  });

  it("chains multiple conditions: first with when, rest with vertical and", () => {
    const yaml = `
name: multi_condition
deny:
  data_use:
    operator: any
    values:
      - marketing
  data_subject:
    operator: any
    values:
      - visitor
`;
    const result = yamlToNodesAndEdges(yaml);
    expect(result).not.toBeNull();
    const { nodes, edges } = result!;

    expect(nodes.filter((n) => n.type === "conditionNode")).toHaveLength(2);

    // First condition: horizontal from action with "when"
    const whenEdge = edges.find((e) => e.data?.label === "when")!;
    expect(whenEdge.source).toBe("action-1");
    expect(whenEdge.target).toBe("condition-1");

    // Second condition: vertical from first with "and"
    const andEdge = edges.find((e) => e.data?.label === "and")!;
    expect(andEdge.source).toBe("condition-1");
    expect(andEdge.target).toBe("condition-2");
    expect(andEdge.sourceHandle).toBe("bottom");
    expect(andEdge.targetHandle).toBe("top");
  });

  it("processes condition properties in fixed order: data_category, data_use, data_subject", () => {
    const yaml = `
name: ordered
allow:
  data_subject:
    values:
      - customer
  data_use:
    values:
      - essential
  data_category:
    values:
      - user.name
`;
    const result = yamlToNodesAndEdges(yaml);
    const conditionNodes = result!.nodes.filter(
      (n) => n.type === "conditionNode",
    );
    expect(conditionNodes[0].data.property).toBe(
      ConditionProperty.DATA_CATEGORIES,
    );
    expect(conditionNodes[1].data.property).toBe(ConditionProperty.DATA_USE);
    expect(conditionNodes[2].data.property).toBe(
      ConditionProperty.DATA_SUBJECTS,
    );
  });

  it("creates constraint from first condition with unless label", () => {
    const yaml = `
name: with_consent_constraint
deny:
  data_category:
    values:
      - user.financial
unless:
  any:
    - consent:
        preference_key:
          - financial_data_processing
        value: opt_in
`;
    const result = yamlToNodesAndEdges(yaml);
    expect(result).not.toBeNull();
    const { nodes, edges } = result!;

    const constraintNode = nodes.find((n) => n.type === "constraintNode")!;
    expect(constraintNode.data.constraintType).toBe(ConstraintType.CONSENT);
    expect(constraintNode.data.preferenceKey).toBe("financial_data_processing");
    expect(constraintNode.data.consentValue).toBe(ConsentValue.OPT_IN);

    // Constraint connects from condition-1 with "unless"
    const constraintEdge = edges.find((e) => e.target === constraintNode.id)!;
    expect(constraintEdge.source).toBe("condition-1");
    expect(constraintEdge.data?.label).toBe("unless");
  });

  it("creates user constraint node from unless block", () => {
    const yaml = `
name: with_user_constraint
deny:
  data_use:
    values:
      - marketing
unless:
  any:
    - user:
        key: age
        value: 18
        operator: less_than
`;
    const result = yamlToNodesAndEdges(yaml);
    const constraintNode = result!.nodes.find(
      (n) => n.type === "constraintNode",
    )!;
    expect(constraintNode.data.constraintType).toBe(ConstraintType.USER);
    expect(constraintNode.data.userKey).toBe("age");
    expect(constraintNode.data.userValue).toBe("18");
    expect(constraintNode.data.userOperator).toBe(UserOperator.LESS_THAN);
  });

  it("chains multiple constraints: first unless, rest vertical and", () => {
    const yaml = `
name: multi_constraint
deny:
  data_use:
    values:
      - marketing
unless:
  any:
    - consent:
        preference_key:
          - marketing_pref
        value: opt_out
    - user:
        key: age
        value: 18
        operator: less_than
`;
    const result = yamlToNodesAndEdges(yaml);
    expect(result).not.toBeNull();
    const { nodes, edges } = result!;

    const constraintNodes = nodes.filter((n) => n.type === "constraintNode");
    expect(constraintNodes).toHaveLength(2);

    // First constraint: from condition-1 with "unless"
    const unlessEdge = edges.find((e) => e.data?.label === "unless")!;
    expect(unlessEdge.source).toBe("condition-1");
    expect(unlessEdge.target).toBe("constraint-1");

    // Second constraint: vertical "and" from first
    const andEdge = edges.find(
      (e) => e.source === "constraint-1" && e.target === "constraint-2",
    )!;
    expect(andEdge.data?.label).toBe("and");
    expect(andEdge.sourceHandle).toBe("bottom");
    expect(andEdge.targetHandle).toBe("top");
  });
});

// ─── nodesToYaml ─────────────────────────────────────────────────────────────

describe("nodesToYaml", () => {
  it("returns empty string when no policy node", () => {
    expect(nodesToYaml([], [])).toBe("");
  });

  it("serializes policy node with name only", () => {
    const nodes = [
      {
        id: "policy",
        type: "policyNode",
        position: { x: 0, y: 0 },
        data: { name: "my_policy", description: "", controlGroupOptions: [] },
      },
    ];
    const result = nodesToYaml(nodes as any, []);
    const parsed = parseYaml(result);
    expect(parsed?.name).toBe("my_policy");
    expect(parsed?.description).toBeUndefined();
  });

  it("includes description when non-empty", () => {
    const nodes = [
      {
        id: "policy",
        type: "policyNode",
        position: { x: 0, y: 0 },
        data: {
          name: "my_policy",
          description: "A description",
          controlGroupOptions: [],
        },
      },
    ];
    const result = nodesToYaml(nodes as any, []);
    const parsed = parseYaml(result);
    expect(parsed?.description).toBe("A description");
  });

  it("serializes allow action with condition", () => {
    const nodes = [
      {
        id: "policy",
        type: "policyNode",
        position: { x: 0, y: 0 },
        data: {
          name: "allow_policy",
          description: "",
          controlGroupOptions: [],
        },
      },
      {
        id: "action-1",
        type: "actionNode",
        position: { x: 0, y: 0 },
        data: { actionType: ActionType.ALLOW },
      },
      {
        id: "condition-1",
        type: "conditionNode",
        position: { x: 0, y: 0 },
        data: {
          property: ConditionProperty.DATA_USE,
          values: ["essential"],
          operator: ConditionOperator.ANY,
        },
      },
    ];
    const edges = [
      {
        id: "e-policy-action-1",
        source: "policy",
        target: "action-1",
        type: "labeledEdge",
      },
      {
        id: "e-action-1-condition-1",
        source: "action-1",
        target: "condition-1",
        type: "labeledEdge",
        data: { label: "when" },
      },
    ];
    const result = nodesToYaml(nodes as any, edges as any);
    const parsed = parseYaml(result);
    expect(parsed?.allow?.data_use?.values).toEqual(["essential"]);
    expect(parsed?.allow?.data_use?.operator).toBe(ConditionOperator.ANY);
    expect(parsed?.deny).toBeUndefined();
  });

  it("serializes deny action", () => {
    const nodes = [
      {
        id: "policy",
        type: "policyNode",
        position: { x: 0, y: 0 },
        data: { name: "deny_policy", description: "", controlGroupOptions: [] },
      },
      {
        id: "action-1",
        type: "actionNode",
        position: { x: 0, y: 0 },
        data: { actionType: ActionType.DENY },
      },
      {
        id: "condition-1",
        type: "conditionNode",
        position: { x: 0, y: 0 },
        data: {
          property: ConditionProperty.DATA_CATEGORIES,
          values: ["user.financial"],
          operator: ConditionOperator.ANY,
        },
      },
    ];
    const edges = [
      { id: "e1", source: "policy", target: "action-1", type: "labeledEdge" },
      {
        id: "e2",
        source: "action-1",
        target: "condition-1",
        type: "labeledEdge",
        data: { label: "when" },
      },
    ];
    const result = nodesToYaml(nodes as any, edges as any);
    const parsed = parseYaml(result);
    expect(parsed?.deny?.data_category?.values).toEqual(["user.financial"]);
    expect(parsed?.allow).toBeUndefined();
  });

  it("skips condition nodes with no property", () => {
    const nodes = [
      {
        id: "policy",
        type: "policyNode",
        position: { x: 0, y: 0 },
        data: { name: "p", description: "", controlGroupOptions: [] },
      },
      {
        id: "action-1",
        type: "actionNode",
        position: { x: 0, y: 0 },
        data: { actionType: ActionType.ALLOW },
      },
      {
        id: "condition-1",
        type: "conditionNode",
        position: { x: 0, y: 0 },
        data: {
          property: undefined,
          values: [],
          operator: ConditionOperator.ANY,
        },
      },
    ];
    const edges = [
      { id: "e1", source: "policy", target: "action-1", type: "labeledEdge" },
      {
        id: "e2",
        source: "action-1",
        target: "condition-1",
        type: "labeledEdge",
        data: { label: "when" },
      },
    ];
    const result = nodesToYaml(nodes as any, edges as any);
    const parsed = parseYaml(result);
    expect(parsed?.allow).toEqual({});
  });

  it("skips condition nodes with empty values", () => {
    const nodes = [
      {
        id: "policy",
        type: "policyNode",
        position: { x: 0, y: 0 },
        data: { name: "p", description: "", controlGroupOptions: [] },
      },
      {
        id: "action-1",
        type: "actionNode",
        position: { x: 0, y: 0 },
        data: { actionType: ActionType.ALLOW },
      },
      {
        id: "condition-1",
        type: "conditionNode",
        position: { x: 0, y: 0 },
        data: {
          property: ConditionProperty.DATA_USE,
          values: [],
          operator: ConditionOperator.ANY,
        },
      },
    ];
    const edges = [
      { id: "e1", source: "policy", target: "action-1", type: "labeledEdge" },
      {
        id: "e2",
        source: "action-1",
        target: "condition-1",
        type: "labeledEdge",
        data: { label: "when" },
      },
    ];
    const result = nodesToYaml(nodes as any, edges as any);
    const parsed = parseYaml(result);
    expect(parsed?.allow).toEqual({});
  });

  it("serializes chained conditions into the condition map", () => {
    const nodes = [
      {
        id: "policy",
        type: "policyNode",
        position: { x: 0, y: 0 },
        data: { name: "p", description: "", controlGroupOptions: [] },
      },
      {
        id: "action-1",
        type: "actionNode",
        position: { x: 0, y: 0 },
        data: { actionType: ActionType.DENY },
      },
      {
        id: "condition-1",
        type: "conditionNode",
        position: { x: 0, y: 0 },
        data: {
          property: ConditionProperty.DATA_USE,
          values: ["marketing"],
          operator: ConditionOperator.ANY,
        },
      },
      {
        id: "condition-2",
        type: "conditionNode",
        position: { x: 0, y: 0 },
        data: {
          property: ConditionProperty.DATA_SUBJECTS,
          values: ["visitor"],
          operator: ConditionOperator.ANY,
        },
      },
    ];
    const edges = [
      { id: "e1", source: "policy", target: "action-1", type: "labeledEdge" },
      {
        id: "e2",
        source: "action-1",
        target: "condition-1",
        type: "labeledEdge",
        data: { label: "when" },
      },
      {
        id: "e3",
        source: "condition-1",
        target: "condition-2",
        sourceHandle: "bottom",
        targetHandle: "top",
        type: "labeledEdge",
        data: { label: "and" },
      },
    ];
    const result = nodesToYaml(nodes as any, edges as any);
    const parsed = parseYaml(result);
    expect(parsed?.deny?.data_use?.values).toEqual(["marketing"]);
    expect(parsed?.deny?.data_subject?.values).toEqual(["visitor"]);
  });

  it("serializes constraint via first condition into unless block", () => {
    const nodes = [
      {
        id: "policy",
        type: "policyNode",
        position: { x: 0, y: 0 },
        data: { name: "p", description: "", controlGroupOptions: [] },
      },
      {
        id: "action-1",
        type: "actionNode",
        position: { x: 0, y: 0 },
        data: { actionType: ActionType.DENY },
      },
      {
        id: "condition-1",
        type: "conditionNode",
        position: { x: 0, y: 0 },
        data: {
          property: ConditionProperty.DATA_USE,
          values: ["marketing"],
          operator: ConditionOperator.ANY,
        },
      },
      {
        id: "constraint-1",
        type: "constraintNode",
        position: { x: 0, y: 0 },
        data: {
          constraintType: ConstraintType.CONSENT,
          preferenceKey: "marketing_pref",
          consentValue: ConsentValue.OPT_OUT,
        },
      },
    ];
    const edges = [
      { id: "e1", source: "policy", target: "action-1", type: "labeledEdge" },
      {
        id: "e2",
        source: "action-1",
        target: "condition-1",
        type: "labeledEdge",
        data: { label: "when" },
      },
      {
        id: "e3",
        source: "condition-1",
        target: "constraint-1",
        type: "labeledEdge",
        data: { label: "unless" },
      },
    ];
    const result = nodesToYaml(nodes as any, edges as any);
    const parsed = parseYaml(result);
    expect(parsed?.unless?.any).toHaveLength(1);
    expect((parsed?.unless?.any?.[0] as any)?.consent?.preference_key).toEqual([
      "marketing_pref",
    ]);
    expect((parsed?.unless?.any?.[0] as any)?.consent?.value).toBe(
      ConsentValue.OPT_OUT,
    );
  });

  it("serializes user constraint into unless block", () => {
    const nodes = [
      {
        id: "policy",
        type: "policyNode",
        position: { x: 0, y: 0 },
        data: { name: "p", description: "", controlGroupOptions: [] },
      },
      {
        id: "action-1",
        type: "actionNode",
        position: { x: 0, y: 0 },
        data: { actionType: ActionType.DENY },
      },
      {
        id: "condition-1",
        type: "conditionNode",
        position: { x: 0, y: 0 },
        data: {
          property: ConditionProperty.DATA_USE,
          values: ["marketing"],
          operator: ConditionOperator.ANY,
        },
      },
      {
        id: "constraint-1",
        type: "constraintNode",
        position: { x: 0, y: 0 },
        data: {
          constraintType: ConstraintType.USER,
          userKey: "age",
          userValue: "18",
          userOperator: UserOperator.LESS_THAN,
        },
      },
    ];
    const edges = [
      { id: "e1", source: "policy", target: "action-1", type: "labeledEdge" },
      {
        id: "e2",
        source: "action-1",
        target: "condition-1",
        type: "labeledEdge",
        data: { label: "when" },
      },
      {
        id: "e3",
        source: "condition-1",
        target: "constraint-1",
        type: "labeledEdge",
        data: { label: "unless" },
      },
    ];
    const result = nodesToYaml(nodes as any, edges as any);
    const parsed = parseYaml(result);
    expect((parsed?.unless?.any?.[0] as any)?.user?.key).toBe("age");
    expect(String((parsed?.unless?.any?.[0] as any)?.user?.value)).toBe("18");
    expect((parsed?.unless?.any?.[0] as any)?.user?.operator).toBe(
      UserOperator.LESS_THAN,
    );
  });

  it("serializes chained constraints into unless block", () => {
    const nodes = [
      {
        id: "policy",
        type: "policyNode",
        position: { x: 0, y: 0 },
        data: { name: "p", description: "", controlGroupOptions: [] },
      },
      {
        id: "action-1",
        type: "actionNode",
        position: { x: 0, y: 0 },
        data: { actionType: ActionType.DENY },
      },
      {
        id: "condition-1",
        type: "conditionNode",
        position: { x: 0, y: 0 },
        data: {
          property: ConditionProperty.DATA_USE,
          values: ["marketing"],
          operator: ConditionOperator.ANY,
        },
      },
      {
        id: "constraint-1",
        type: "constraintNode",
        position: { x: 0, y: 0 },
        data: {
          constraintType: ConstraintType.CONSENT,
          preferenceKey: "marketing_pref",
          consentValue: ConsentValue.OPT_OUT,
        },
      },
      {
        id: "constraint-2",
        type: "constraintNode",
        position: { x: 0, y: 0 },
        data: {
          constraintType: ConstraintType.USER,
          userKey: "age",
          userValue: "18",
          userOperator: UserOperator.LESS_THAN,
        },
      },
    ];
    const edges = [
      { id: "e1", source: "policy", target: "action-1", type: "labeledEdge" },
      {
        id: "e2",
        source: "action-1",
        target: "condition-1",
        type: "labeledEdge",
        data: { label: "when" },
      },
      {
        id: "e3",
        source: "condition-1",
        target: "constraint-1",
        type: "labeledEdge",
        data: { label: "unless" },
      },
      {
        id: "e4",
        source: "constraint-1",
        target: "constraint-2",
        sourceHandle: "bottom",
        targetHandle: "top",
        type: "labeledEdge",
        data: { label: "and" },
      },
    ];
    const result = nodesToYaml(nodes as any, edges as any);
    const parsed = parseYaml(result);
    expect(parsed?.unless?.any).toHaveLength(2);
  });

  it("skips incomplete constraint nodes (no type set)", () => {
    const nodes = [
      {
        id: "policy",
        type: "policyNode",
        position: { x: 0, y: 0 },
        data: { name: "p", description: "", controlGroupOptions: [] },
      },
      {
        id: "action-1",
        type: "actionNode",
        position: { x: 0, y: 0 },
        data: { actionType: ActionType.DENY },
      },
      {
        id: "condition-1",
        type: "conditionNode",
        position: { x: 0, y: 0 },
        data: {
          property: ConditionProperty.DATA_USE,
          values: ["marketing"],
          operator: ConditionOperator.ANY,
        },
      },
      {
        id: "constraint-1",
        type: "constraintNode",
        position: { x: 0, y: 0 },
        data: {},
      },
    ];
    const edges = [
      { id: "e1", source: "policy", target: "action-1", type: "labeledEdge" },
      {
        id: "e2",
        source: "action-1",
        target: "condition-1",
        type: "labeledEdge",
        data: { label: "when" },
      },
      {
        id: "e3",
        source: "condition-1",
        target: "constraint-1",
        type: "labeledEdge",
        data: { label: "unless" },
      },
    ];
    const result = nodesToYaml(nodes as any, edges as any);
    const parsed = parseYaml(result);
    expect(parsed?.unless).toBeUndefined();
  });
});

// ─── deriveLayoutEdges ───────────────────────────────────────────────────────

describe("deriveLayoutEdges", () => {
  it("fans out conditions from action for same dagre rank", () => {
    const nodes = [
      { id: "policy", type: "policyNode", position: { x: 0, y: 0 }, data: {} },
      {
        id: "action-1",
        type: "actionNode",
        position: { x: 0, y: 0 },
        data: {},
      },
      {
        id: "condition-1",
        type: "conditionNode",
        position: { x: 0, y: 0 },
        data: {},
      },
      {
        id: "condition-2",
        type: "conditionNode",
        position: { x: 0, y: 0 },
        data: {},
      },
    ];
    const displayEdges = [
      { id: "e1", source: "policy", target: "action-1", type: "labeledEdge" },
      {
        id: "e2",
        source: "action-1",
        target: "condition-1",
        type: "labeledEdge",
      },
      {
        id: "e3",
        source: "condition-1",
        target: "condition-2",
        type: "labeledEdge",
      },
    ];

    const layout = deriveLayoutEdges(nodes as any, displayEdges as any);

    // Should have: policy→action, action→cond1, action→cond2
    expect(layout).toHaveLength(3);
    expect(layout.filter((e) => e.source === "action-1")).toHaveLength(2);
  });

  it("fans out constraints from first condition for same dagre rank", () => {
    const nodes = [
      { id: "policy", type: "policyNode", position: { x: 0, y: 0 }, data: {} },
      {
        id: "action-1",
        type: "actionNode",
        position: { x: 0, y: 0 },
        data: {},
      },
      {
        id: "condition-1",
        type: "conditionNode",
        position: { x: 0, y: 0 },
        data: {},
      },
      {
        id: "constraint-1",
        type: "constraintNode",
        position: { x: 0, y: 0 },
        data: {},
      },
      {
        id: "constraint-2",
        type: "constraintNode",
        position: { x: 0, y: 0 },
        data: {},
      },
    ];
    const displayEdges = [
      { id: "e1", source: "policy", target: "action-1", type: "labeledEdge" },
      {
        id: "e2",
        source: "action-1",
        target: "condition-1",
        type: "labeledEdge",
      },
      {
        id: "e3",
        source: "condition-1",
        target: "constraint-1",
        type: "labeledEdge",
      },
      {
        id: "e4",
        source: "constraint-1",
        target: "constraint-2",
        type: "labeledEdge",
      },
    ];

    const layout = deriveLayoutEdges(nodes as any, displayEdges as any);

    // Should have: policy→action, action→cond1, cond1→cons1, cond1→cons2
    expect(layout).toHaveLength(4);
    const fromCond1 = layout.filter((e) => e.source === "condition-1");
    expect(fromCond1).toHaveLength(2);
  });
});

// ─── Round-trip tests ─────────────────────────────────────────────────────────

describe("round-trip: yamlToNodesAndEdges → nodesToYaml", () => {
  const roundTrip = (yaml: string) => {
    const result = yamlToNodesAndEdges(yaml);
    if (!result) {
      return null;
    }
    return nodesToYaml(result.nodes, result.edges);
  };

  it("preserves name and description", () => {
    const yaml = "name: my_policy\ndescription: A policy\n";
    const output = roundTrip(yaml);
    const parsed = parseYaml(output!);
    expect(parsed?.name).toBe("my_policy");
    expect(parsed?.description).toBe("A policy");
  });

  it("preserves simple allow with data_use condition", () => {
    const yaml = `
name: allow_essential
allow:
  data_use:
    operator: any
    values:
      - essential
      - essential.service
`;
    const output = roundTrip(yaml);
    const parsed = parseYaml(output!);
    expect(parsed?.allow?.data_use?.values).toEqual([
      "essential",
      "essential.service",
    ]);
    expect(parsed?.allow?.data_use?.operator).toBe("any");
  });

  it("preserves deny with multiple conditions", () => {
    const yaml = `
name: deny_visitor_profiling
deny:
  data_use:
    operator: any
    values:
      - marketing.advertising.profiling
  data_subject:
    operator: any
    values:
      - visitor
      - anonymous_user
`;
    const output = roundTrip(yaml);
    const parsed = parseYaml(output!);
    expect(parsed?.deny?.data_use?.values).toContain(
      "marketing.advertising.profiling",
    );
    expect(parsed?.deny?.data_subject?.values).toContain("visitor");
    expect(parsed?.deny?.data_subject?.values).toContain("anonymous_user");
  });

  it("preserves deny with consent constraint", () => {
    const yaml = `
name: deny_financial
deny:
  data_category:
    operator: any
    values:
      - user.financial
      - user.financial.credit_card
unless:
  any:
    - consent:
        preference_key:
          - financial_data_processing
        value: opt_out
`;
    const output = roundTrip(yaml);
    const parsed = parseYaml(output!);
    expect(parsed?.deny?.data_category?.values).toContain("user.financial");
    expect(parsed?.unless?.any).toHaveLength(1);
    expect((parsed?.unless?.any?.[0] as any)?.consent?.preference_key).toEqual([
      "financial_data_processing",
    ]);
  });

  it("preserves deny with multiple constraints", () => {
    const yaml = `
name: multi_constraint
deny:
  data_use:
    operator: any
    values:
      - marketing
unless:
  any:
    - consent:
        preference_key:
          - marketing_pref
        value: opt_out
    - user:
        key: age
        value: 18
        operator: less_than
`;
    const output = roundTrip(yaml);
    const parsed = parseYaml(output!);
    expect(parsed?.unless?.any).toHaveLength(2);
  });

  it("preserves allow with data_category and data_use", () => {
    const yaml = `
name: allow_payment
allow:
  data_category:
    operator: any
    values:
      - user.financial
      - user.financial.credit_card
  data_use:
    operator: any
    values:
      - essential.service.payment_processing
`;
    const output = roundTrip(yaml);
    const parsed = parseYaml(output!);
    expect(parsed?.allow?.data_category?.values).toContain("user.financial");
    expect(parsed?.allow?.data_use?.values).toContain(
      "essential.service.payment_processing",
    );
  });

  it("preserves allow with data_use and data_subject", () => {
    const yaml = `
name: allow_employment
allow:
  data_use:
    operator: any
    values:
      - employment
      - employment.recruitment
  data_subject:
    operator: any
    values:
      - employee
      - job_applicant
`;
    const output = roundTrip(yaml);
    const parsed = parseYaml(output!);
    expect(parsed?.allow?.data_use?.values).toContain("employment");
    expect(parsed?.allow?.data_subject?.values).toContain("employee");
  });
});
