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
  ConsentRequirement,
  ConstraintType,
  DataFlowDirection,
  DataFlowOperator,
  GeoOperator,
} from "~/features/access-policies/types";

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

  it("returns null when object has neither decision nor name", () => {
    expect(parseYaml("enabled: true")).toBeNull();
  });

  it("parses minimal valid YAML with name", () => {
    const result = parseYaml("name: my_policy");
    expect(result).toEqual({ name: "my_policy" });
  });

  it("parses full PRD-format YAML", () => {
    const yamlStr = `
fides_key: test_policy
name: Test Policy
description: A complete policy
enabled: true
priority: 100
decision: ALLOW
match:
  data_use:
    any:
      - essential
`;
    const result = parseYaml(yamlStr);
    expect(result?.name).toBe("Test Policy");
    expect(result?.fides_key).toBe("test_policy");
    expect(result?.description).toBe("A complete policy");
    expect(result?.enabled).toBe(true);
    expect(result?.priority).toBe(100);
    expect(result?.decision).toBe("ALLOW");
    expect(result?.match?.data_use?.any).toEqual(["essential"]);
  });
});

describe("yamlToNodesAndEdges", () => {
  it("returns null for invalid YAML", () => {
    expect(yamlToNodesAndEdges("not: [valid")).toBeNull();
  });

  it("returns null for YAML without name or decision", () => {
    expect(yamlToNodesAndEdges("enabled: true")).toBeNull();
  });

  it("returns policy node only when no decision/match block", () => {
    const result = yamlToNodesAndEdges(
      "name: bare_policy\ndescription: no rules",
    );
    expect(result).not.toBeNull();
    expect(result!.nodes).toHaveLength(1);
    expect(result!.nodes[0].id).toBe("policy");
    expect(result!.edges).toHaveLength(0);
  });

  it("creates policy + action + condition for ALLOW with match", () => {
    const yamlStr = `
fides_key: simple_allow
name: Simple Allow
decision: ALLOW
match:
  data_use:
    any:
      - essential
`;
    const result = yamlToNodesAndEdges(yamlStr);
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

  it("creates DENY action for decision: DENY", () => {
    const yamlStr = `
name: deny_policy
decision: DENY
match:
  data_use:
    any:
      - marketing.advertising
`;
    const result = yamlToNodesAndEdges(yamlStr);
    const actionNode = result!.nodes.find((n) => n.id === "action-1")!;
    expect(actionNode.data.actionType).toBe(ActionType.DENY);
  });

  it("uses ALL operator when match uses all", () => {
    const yamlStr = `
name: all_operator
decision: ALLOW
match:
  data_category:
    all:
      - user.contact
      - user.contact.email
`;
    const result = yamlToNodesAndEdges(yamlStr);
    const condNode = result!.nodes.find((n) => n.id === "condition-1")!;
    expect(condNode.data.operator).toBe(ConditionOperator.ALL);
    expect(condNode.data.values).toEqual([
      "user.contact",
      "user.contact.email",
    ]);
  });

  it("chains multiple conditions: first with when, rest with vertical and", () => {
    const yamlStr = `
name: multi_condition
decision: DENY
match:
  data_use:
    any:
      - marketing
  data_subject:
    any:
      - visitor
`;
    const result = yamlToNodesAndEdges(yamlStr);
    expect(result).not.toBeNull();
    const { nodes, edges } = result!;

    expect(nodes.filter((n) => n.type === "conditionNode")).toHaveLength(2);

    const whenEdge = edges.find((e) => e.data?.label === "when")!;
    expect(whenEdge.source).toBe("action-1");
    expect(whenEdge.target).toBe("condition-1");

    const andEdge = edges.find((e) => e.data?.label === "and")!;
    expect(andEdge.source).toBe("condition-1");
    expect(andEdge.target).toBe("condition-2");
    expect(andEdge.sourceHandle).toBe("bottom");
    expect(andEdge.targetHandle).toBe("top");
  });

  it("processes condition properties in fixed order: data_category, data_use, data_subject", () => {
    const yamlStr = `
name: ordered
decision: ALLOW
match:
  data_subject:
    any:
      - customer
  data_use:
    any:
      - essential
  data_category:
    any:
      - user.name
`;
    const result = yamlToNodesAndEdges(yamlStr);
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

  it("creates consent constraint from unless block", () => {
    const yamlStr = `
name: with_consent_constraint
decision: DENY
match:
  data_category:
    any:
      - user.financial
unless:
  - type: consent
    privacy_notice_key: financial_data_processing
    requirement: opt_in
`;
    const result = yamlToNodesAndEdges(yamlStr);
    expect(result).not.toBeNull();
    const { nodes, edges } = result!;

    const constraintNode = nodes.find((n) => n.type === "constraintNode")!;
    expect(constraintNode.data.constraintType).toBe(ConstraintType.CONSENT);
    expect(constraintNode.data.privacyNoticeKey).toBe(
      "financial_data_processing",
    );
    expect(constraintNode.data.consentRequirement).toBe(
      ConsentRequirement.OPT_IN,
    );

    const constraintEdge = edges.find((e) => e.target === constraintNode.id)!;
    expect(constraintEdge.source).toBe("condition-1");
    expect(constraintEdge.data?.label).toBe("unless");
  });

  it("creates geo_location constraint from unless block", () => {
    const yamlStr = `
name: with_geo_constraint
decision: ALLOW
match:
  data_use:
    any:
      - marketing
unless:
  - type: geo_location
    field: environment.geo_location
    operator: in
    values:
      - US-CA
      - EU
`;
    const result = yamlToNodesAndEdges(yamlStr);
    const constraintNode = result!.nodes.find(
      (n) => n.type === "constraintNode",
    )!;
    expect(constraintNode.data.constraintType).toBe(
      ConstraintType.GEO_LOCATION,
    );
    expect(constraintNode.data.geoField).toBe("environment.geo_location");
    expect(constraintNode.data.geoOperator).toBe(GeoOperator.IN);
    expect(constraintNode.data.geoValues).toEqual(["US-CA", "EU"]);
  });

  it("creates data_flow constraint from unless block", () => {
    const yamlStr = `
name: with_data_flow_constraint
decision: DENY
match:
  data_use:
    any:
      - marketing
unless:
  - type: data_flow
    direction: ingress
    operator: none_of
    systems:
      - third_party_data_broker
      - external_data_vendor
`;
    const result = yamlToNodesAndEdges(yamlStr);
    const constraintNode = result!.nodes.find(
      (n) => n.type === "constraintNode",
    )!;
    expect(constraintNode.data.constraintType).toBe(ConstraintType.DATA_FLOW);
    expect(constraintNode.data.dataFlowDirection).toBe(
      DataFlowDirection.INGRESS,
    );
    expect(constraintNode.data.dataFlowOperator).toBe(DataFlowOperator.NONE_OF);
    expect(constraintNode.data.dataFlowSystems).toEqual([
      "third_party_data_broker",
      "external_data_vendor",
    ]);
  });

  it("chains multiple constraints: first unless, rest vertical and", () => {
    const yamlStr = `
name: multi_constraint
decision: ALLOW
match:
  data_use:
    any:
      - marketing
unless:
  - type: consent
    privacy_notice_key: marketing_pref
    requirement: not_opt_in
  - type: geo_location
    field: environment.geo_location
    operator: in
    values:
      - US-CA
      - EU
`;
    const result = yamlToNodesAndEdges(yamlStr);
    expect(result).not.toBeNull();
    const { nodes, edges } = result!;

    const constraintNodes = nodes.filter((n) => n.type === "constraintNode");
    expect(constraintNodes).toHaveLength(2);

    const unlessEdge = edges.find((e) => e.data?.label === "unless")!;
    expect(unlessEdge.source).toBe("condition-1");
    expect(unlessEdge.target).toBe("constraint-1");

    const andEdge = edges.find(
      (e) => e.source === "constraint-1" && e.target === "constraint-2",
    )!;
    expect(andEdge.data?.label).toBe("and");
    expect(andEdge.sourceHandle).toBe("bottom");
    expect(andEdge.targetHandle).toBe("top");
  });

  it("populates policy node metadata fields", () => {
    const yamlStr = `
fides_key: meta_test
name: Metadata Test
description: Testing metadata fields
enabled: false
priority: 50
controls:
  - gdpr_article_9
  - ccpa_compliance
decision: ALLOW
match:
  data_use:
    any:
      - essential
action:
  message: Blocked for compliance reasons.
`;
    const result = yamlToNodesAndEdges(yamlStr);
    const policyNode = result!.nodes.find((n) => n.id === "policy")!;
    expect(policyNode.data.fidesKey).toBe("meta_test");
    expect(policyNode.data.enabled).toBe(false);
    expect(policyNode.data.priority).toBe(50);
    expect(policyNode.data.control).toBe("gdpr_article_9");
    expect(policyNode.data.actionMessage).toBe(
      "Blocked for compliance reasons.",
    );
  });
});

describe("nodesToYaml", () => {
  it("returns empty string when no policy node", () => {
    expect(nodesToYaml([], [])).toBe("");
  });

  it("serializes policy node with name only (no action)", () => {
    const nodes = [
      {
        id: "policy",
        type: "policyNode",
        position: { x: 0, y: 0 },
        data: {
          name: "my_policy",
          description: "",
          fidesKey: "",
          enabled: true,
          priority: 0,
          controls: [],
          controlOptions: [],
          actionMessage: "",
        },
      },
    ];
    const result = nodesToYaml(nodes as any, []);
    const parsed = parseYaml(result);
    expect(parsed?.name).toBe("my_policy");
    expect(parsed?.description).toBeUndefined();
    // enabled defaults to true, so it should not be in output
    expect(parsed?.enabled).toBeUndefined();
  });

  it("includes fides_key, priority, controls when set", () => {
    const nodes = [
      {
        id: "policy",
        type: "policyNode",
        position: { x: 0, y: 0 },
        data: {
          name: "my_policy",
          description: "",
          fidesKey: "my_key",
          enabled: true,
          priority: 100,
          control: "gdpr_article_9",
          controlOptions: [],
          actionMessage: "",
        },
      },
    ];
    const result = nodesToYaml(nodes as any, []);
    const parsed = parseYaml(result);
    expect(parsed?.fides_key).toBe("my_key");
    expect(parsed?.priority).toBe(100);
    expect(parsed?.controls).toEqual(["gdpr_article_9"]);
  });

  it("includes enabled: false when disabled", () => {
    const nodes = [
      {
        id: "policy",
        type: "policyNode",
        position: { x: 0, y: 0 },
        data: {
          name: "disabled_policy",
          description: "",
          fidesKey: "",
          enabled: false,
          priority: 0,
          controls: [],
          controlOptions: [],
          actionMessage: "",
        },
      },
    ];
    const result = nodesToYaml(nodes as any, []);
    const parsed = parseYaml(result);
    expect(parsed?.enabled).toBe(false);
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
          fidesKey: "",
          enabled: true,
          priority: 0,
          controls: [],
          controlOptions: [],
          actionMessage: "",
        },
      },
    ];
    const result = nodesToYaml(nodes as any, []);
    const parsed = parseYaml(result);
    expect(parsed?.description).toBe("A description");
  });

  it("serializes ALLOW decision with match block", () => {
    const nodes = [
      {
        id: "policy",
        type: "policyNode",
        position: { x: 0, y: 0 },
        data: {
          name: "allow_policy",
          description: "",
          fidesKey: "",
          enabled: true,
          priority: 0,
          controls: [],
          controlOptions: [],
          actionMessage: "",
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
    expect(parsed?.decision).toBe("ALLOW");
    expect(parsed?.match?.data_use?.any).toEqual(["essential"]);
    expect((parsed as any)?.allow).toBeUndefined();
  });

  it("serializes DENY decision", () => {
    const nodes = [
      {
        id: "policy",
        type: "policyNode",
        position: { x: 0, y: 0 },
        data: {
          name: "deny_policy",
          description: "",
          fidesKey: "",
          enabled: true,
          priority: 0,
          controls: [],
          controlOptions: [],
          actionMessage: "",
        },
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
    expect(parsed?.decision).toBe("DENY");
    expect(parsed?.match?.data_category?.any).toEqual(["user.financial"]);
    expect((parsed as any)?.deny).toBeUndefined();
  });

  it("uses all operator in match when condition operator is ALL", () => {
    const nodes = [
      {
        id: "policy",
        type: "policyNode",
        position: { x: 0, y: 0 },
        data: {
          name: "p",
          description: "",
          fidesKey: "",
          enabled: true,
          priority: 0,
          controls: [],
          controlOptions: [],
          actionMessage: "",
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
          property: ConditionProperty.DATA_CATEGORIES,
          values: ["user.contact", "user.contact.email"],
          operator: ConditionOperator.ALL,
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
    expect(parsed?.match?.data_category?.all).toEqual([
      "user.contact",
      "user.contact.email",
    ]);
    expect(parsed?.match?.data_category?.any).toBeUndefined();
  });

  it("skips condition nodes with no property", () => {
    const nodes = [
      {
        id: "policy",
        type: "policyNode",
        position: { x: 0, y: 0 },
        data: {
          name: "p",
          description: "",
          fidesKey: "",
          enabled: true,
          priority: 0,
          controls: [],
          controlOptions: [],
          actionMessage: "",
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
    expect(parsed?.match).toEqual({});
  });

  it("serializes chained conditions into the match block", () => {
    const nodes = [
      {
        id: "policy",
        type: "policyNode",
        position: { x: 0, y: 0 },
        data: {
          name: "p",
          description: "",
          fidesKey: "",
          enabled: true,
          priority: 0,
          controls: [],
          controlOptions: [],
          actionMessage: "",
        },
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
    expect(parsed?.match?.data_use?.any).toEqual(["marketing"]);
    expect(parsed?.match?.data_subject?.any).toEqual(["visitor"]);
  });

  it("serializes consent constraint into flat unless array", () => {
    const nodes = [
      {
        id: "policy",
        type: "policyNode",
        position: { x: 0, y: 0 },
        data: {
          name: "p",
          description: "",
          fidesKey: "",
          enabled: true,
          priority: 0,
          controls: [],
          controlOptions: [],
          actionMessage: "",
        },
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
          privacyNoticeKey: "marketing_pref",
          consentRequirement: ConsentRequirement.OPT_OUT,
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
    expect(parsed?.unless).toHaveLength(1);
    expect(parsed?.unless?.[0]).toEqual({
      type: "consent",
      privacy_notice_key: "marketing_pref",
      requirement: "opt_out",
    });
  });

  it("serializes geo_location constraint into unless array", () => {
    const nodes = [
      {
        id: "policy",
        type: "policyNode",
        position: { x: 0, y: 0 },
        data: {
          name: "p",
          description: "",
          fidesKey: "",
          enabled: true,
          priority: 0,
          controls: [],
          controlOptions: [],
          actionMessage: "",
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
          values: ["marketing"],
          operator: ConditionOperator.ANY,
        },
      },
      {
        id: "constraint-1",
        type: "constraintNode",
        position: { x: 0, y: 0 },
        data: {
          constraintType: ConstraintType.GEO_LOCATION,
          geoField: "environment.geo_location",
          geoOperator: GeoOperator.IN,
          geoValues: ["US-CA", "EU"],
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
    expect(parsed?.unless?.[0]).toEqual({
      type: "geo_location",
      field: "environment.geo_location",
      operator: "in",
      values: ["US-CA", "EU"],
    });
  });

  it("serializes data_flow constraint into unless array", () => {
    const nodes = [
      {
        id: "policy",
        type: "policyNode",
        position: { x: 0, y: 0 },
        data: {
          name: "p",
          description: "",
          fidesKey: "",
          enabled: true,
          priority: 0,
          controls: [],
          controlOptions: [],
          actionMessage: "",
        },
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
          constraintType: ConstraintType.DATA_FLOW,
          dataFlowDirection: DataFlowDirection.INGRESS,
          dataFlowOperator: DataFlowOperator.NONE_OF,
          dataFlowSystems: ["third_party_data_broker", "external_data_vendor"],
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
    expect(parsed?.unless?.[0]).toEqual({
      type: "data_flow",
      direction: "ingress",
      operator: "none_of",
      systems: ["third_party_data_broker", "external_data_vendor"],
    });
  });

  it("serializes chained constraints into unless array", () => {
    const nodes = [
      {
        id: "policy",
        type: "policyNode",
        position: { x: 0, y: 0 },
        data: {
          name: "p",
          description: "",
          fidesKey: "",
          enabled: true,
          priority: 0,
          controls: [],
          controlOptions: [],
          actionMessage: "",
        },
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
          privacyNoticeKey: "marketing_pref",
          consentRequirement: ConsentRequirement.OPT_OUT,
        },
      },
      {
        id: "constraint-2",
        type: "constraintNode",
        position: { x: 0, y: 0 },
        data: {
          constraintType: ConstraintType.GEO_LOCATION,
          geoField: "environment.geo_location",
          geoOperator: GeoOperator.IN,
          geoValues: ["US-CA"],
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
    expect(parsed?.unless).toHaveLength(2);
  });

  it("includes action.message in YAML output", () => {
    const nodes = [
      {
        id: "policy",
        type: "policyNode",
        position: { x: 0, y: 0 },
        data: {
          name: "p",
          description: "",
          fidesKey: "",
          enabled: true,
          priority: 0,
          controls: [],
          controlOptions: [],
          actionMessage: "",
        },
      },
      {
        id: "action-1",
        type: "actionNode",
        position: { x: 0, y: 0 },
        data: {
          actionType: ActionType.DENY,
          actionMessage: "Access denied due to policy.",
        },
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
    expect(parsed?.action?.message).toBe("Access denied due to policy.");
  });

  it("skips incomplete constraint nodes (no type set)", () => {
    const nodes = [
      {
        id: "policy",
        type: "policyNode",
        position: { x: 0, y: 0 },
        data: {
          name: "p",
          description: "",
          fidesKey: "",
          enabled: true,
          priority: 0,
          controls: [],
          controlOptions: [],
          actionMessage: "",
        },
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

    expect(layout).toHaveLength(4);
    const fromCond1 = layout.filter((e) => e.source === "condition-1");
    expect(fromCond1).toHaveLength(2);
  });
});

describe("round-trip: yamlToNodesAndEdges → nodesToYaml", () => {
  const roundTrip = (yamlStr: string) => {
    const result = yamlToNodesAndEdges(yamlStr);
    if (!result) {
      return null;
    }
    return nodesToYaml(result.nodes, result.edges);
  };

  it("preserves name and description", () => {
    const yamlStr = "name: my_policy\ndescription: A policy\n";
    const output = roundTrip(yamlStr);
    const parsed = parseYaml(output!);
    expect(parsed?.name).toBe("my_policy");
    expect(parsed?.description).toBe("A policy");
  });

  it("PRD 4.1: Default Deny (catch-all)", () => {
    const yamlStr = `
fides_key: default_deny
name: Default Deny All
description: Baseline policy that denies all unmatched data processing.
decision: DENY
match: {}
action:
  message: No policy explicitly permits this data use.
`;
    const output = roundTrip(yamlStr);
    const parsed = parseYaml(output!);
    expect(parsed?.decision).toBe("DENY");
    expect(parsed?.fides_key).toBe("default_deny");
    expect(parsed?.action?.message).toBe(
      "No policy explicitly permits this data use.",
    );
  });

  it("PRD 4.2: CCPA Sale Blocker (ALLOW + unless consent)", () => {
    const yamlStr = `
fides_key: ccpa_sale_blocker
name: CCPA Commercial Data Restriction
description: Allow commercial data use unless the user has opted out of data sales.
priority: 100
controls:
  - ccpa_compliance
decision: ALLOW
match:
  data_use:
    any:
      - commercial
unless:
  - type: consent
    privacy_notice_key: ccpa_do_not_sell
    requirement: opt_out
action:
  message: User has opted out of the sale/sharing of their personal data.
`;
    const output = roundTrip(yamlStr);
    const parsed = parseYaml(output!);
    expect(parsed?.decision).toBe("ALLOW");
    expect(parsed?.priority).toBe(100);
    expect(parsed?.controls).toEqual(["ccpa_compliance"]);
    expect(parsed?.match?.data_use?.any).toContain("commercial");
    expect(parsed?.unless).toHaveLength(1);
    expect(parsed?.unless?.[0]).toEqual({
      type: "consent",
      privacy_notice_key: "ccpa_do_not_sell",
      requirement: "opt_out",
    });
    expect(parsed?.action?.message).toBe(
      "User has opted out of the sale/sharing of their personal data.",
    );
  });

  it("PRD 4.4: Unconditional DENY", () => {
    const yamlStr = `
fides_key: block_third_party_ads
name: Block Third-Party Advertising
priority: 200
decision: DENY
match:
  data_use:
    any:
      - marketing.advertising.third_party
action:
  message: Third-party targeted advertising is not permitted.
`;
    const output = roundTrip(yamlStr);
    const parsed = parseYaml(output!);
    expect(parsed?.decision).toBe("DENY");
    expect(parsed?.priority).toBe(200);
    expect(parsed?.match?.data_use?.any).toContain(
      "marketing.advertising.third_party",
    );
  });

  it("PRD 4.6: Conditional DENY (DENY + unless data_flow)", () => {
    const yamlStr = `
fides_key: block_data_broker_ingress
name: Block Data Broker Sources
priority: 150
decision: DENY
match:
  data_use:
    any:
      - marketing
unless:
  - type: data_flow
    direction: ingress
    operator: none_of
    systems:
      - third_party_data_broker
      - external_data_vendor
action:
  message: Marketing data sourced from unapproved data brokers is not permitted.
`;
    const output = roundTrip(yamlStr);
    const parsed = parseYaml(output!);
    expect(parsed?.decision).toBe("DENY");
    expect(parsed?.unless).toHaveLength(1);
    expect(parsed?.unless?.[0]).toEqual({
      type: "data_flow",
      direction: "ingress",
      operator: "none_of",
      systems: ["third_party_data_broker", "external_data_vendor"],
    });
  });

  it("PRD 4.7: Layered — consent + geo_location unless", () => {
    const yamlStr = `
fides_key: retention_phone_access
name: Retention Campaign Phone Access
priority: 100
decision: ALLOW
match:
  data_subject:
    all:
      - customer
  data_category:
    all:
      - user.contact.phone
  data_use:
    all:
      - marketing.retention
unless:
  - type: consent
    privacy_notice_key: marketing_phone_calls
    requirement: not_opt_in
  - type: geo_location
    field: environment.geo_location
    operator: in
    values:
      - US-CA
      - EU
action:
  message: Phone marketing requires consent and is restricted in certain regions.
`;
    const output = roundTrip(yamlStr);
    const parsed = parseYaml(output!);
    expect(parsed?.decision).toBe("ALLOW");
    expect(parsed?.match?.data_subject?.all).toEqual(["customer"]);
    expect(parsed?.match?.data_category?.all).toEqual(["user.contact.phone"]);
    expect(parsed?.match?.data_use?.all).toEqual(["marketing.retention"]);
    expect(parsed?.unless).toHaveLength(2);
    expect(parsed?.unless?.[0]).toEqual({
      type: "consent",
      privacy_notice_key: "marketing_phone_calls",
      requirement: "not_opt_in",
    });
    expect(parsed?.unless?.[1]).toEqual({
      type: "geo_location",
      field: "environment.geo_location",
      operator: "in",
      values: ["US-CA", "EU"],
    });
  });
});
