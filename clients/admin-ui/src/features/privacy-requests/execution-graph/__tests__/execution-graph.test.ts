import { ExecutionGraphNode, ExecutionGraphNodeStatus } from "../../types";
import {
  EXECUTION_GRAPH_STATUS_LABELS,
  isInternalNode,
  isRootNode,
  isTerminatorNode,
} from "../execution-graph.constants";
import { buildGraph } from "../ExecutionGraphView";

const makeNode = (
  overrides: Partial<ExecutionGraphNode> = {},
): ExecutionGraphNode => ({
  id: "test-id",
  collection_address: "test_dataset:test_collection",
  dataset_name: "test_dataset",
  collection_name: "test_collection",
  status: "pending",
  action_type: "access",
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
  upstream_tasks: [],
  downstream_tasks: [],
  message: null,
  ...overrides,
});

describe("isInternalNode", () => {
  it("identifies __ROOT__ as internal", () => {
    expect(isInternalNode("__ROOT__:__ROOT__")).toBe(true);
  });

  it("identifies __TERMINATE__ as internal", () => {
    expect(isInternalNode("__TERMINATE__:__TERMINATE__")).toBe(true);
  });

  it("identifies collection nodes as not internal", () => {
    expect(isInternalNode("my_dataset:users")).toBe(false);
  });
});

describe("isRootNode", () => {
  it("identifies __ROOT__ as root", () => {
    expect(isRootNode("__ROOT__:__ROOT__")).toBe(true);
  });

  it("does not identify other nodes as root", () => {
    expect(isRootNode("my_dataset:users")).toBe(false);
    expect(isRootNode("__TERMINATE__:__TERMINATE__")).toBe(false);
  });
});

describe("isTerminatorNode", () => {
  it("identifies __TERMINATE__ as terminator", () => {
    expect(isTerminatorNode("__TERMINATE__:__TERMINATE__")).toBe(true);
  });

  it("does not identify other nodes as terminator", () => {
    expect(isTerminatorNode("my_dataset:users")).toBe(false);
    expect(isTerminatorNode("__ROOT__:__ROOT__")).toBe(false);
  });
});

describe("EXECUTION_GRAPH_STATUS_LABELS", () => {
  const expectedLabels: Record<ExecutionGraphNodeStatus, string> = {
    pending: "Pending",
    executing: "Executing",
    complete: "Complete",
    error: "Error",
    skipped: "Skipped",
    retrying: "Retrying",
    paused: "Paused",
    polling: "Polling",
  };

  it.each(Object.entries(expectedLabels))(
    "maps %s to %s",
    (status, label) => {
      expect(
        EXECUTION_GRAPH_STATUS_LABELS[status as ExecutionGraphNodeStatus],
      ).toBe(label);
    },
  );
});

describe("buildGraph", () => {
  it("returns empty graph for empty input", () => {
    const { nodes, edges } = buildGraph([]);
    expect(nodes).toHaveLength(0);
    expect(edges).toHaveLength(0);
  });

  it("includes root node but filters out terminator", () => {
    const graphNodes = [
      makeNode({
        collection_address: "__ROOT__:__ROOT__",
        id: "root",
        downstream_tasks: ["db:users"],
      }),
      makeNode({
        collection_address: "db:users",
        id: "users",
        upstream_tasks: ["__ROOT__:__ROOT__"],
        downstream_tasks: ["__TERMINATE__:__TERMINATE__"],
      }),
      makeNode({
        collection_address: "__TERMINATE__:__TERMINATE__",
        id: "term",
      }),
    ];
    const { nodes, edges } = buildGraph(graphNodes);
    expect(nodes).toHaveLength(2);
    expect(nodes.map((n) => n.id)).toContain("__ROOT__:__ROOT__");
    expect(nodes.map((n) => n.id)).toContain("db:users");
    expect(edges).toHaveLength(1);
    expect(edges[0].source).toBe("__ROOT__:__ROOT__");
    expect(edges[0].target).toBe("db:users");
  });

  it("creates edges from downstream_tasks", () => {
    const graphNodes = [
      makeNode({
        collection_address: "db:users",
        id: "1",
        downstream_tasks: ["db:orders"],
      }),
      makeNode({
        collection_address: "db:orders",
        id: "2",
        upstream_tasks: ["db:users"],
        downstream_tasks: [],
      }),
    ];
    const { edges } = buildGraph(graphNodes);
    expect(edges).toHaveLength(1);
    expect(edges[0].source).toBe("db:users");
    expect(edges[0].target).toBe("db:orders");
  });

  it("skips edges to terminator node", () => {
    const graphNodes = [
      makeNode({
        collection_address: "db:users",
        id: "1",
        downstream_tasks: ["__TERMINATE__:__TERMINATE__"],
      }),
    ];
    const { edges } = buildGraph(graphNodes);
    expect(edges).toHaveLength(0);
  });

  it("deduplicates edges", () => {
    const graphNodes = [
      makeNode({
        collection_address: "db:users",
        id: "1",
        downstream_tasks: ["db:orders", "db:orders"],
      }),
      makeNode({
        collection_address: "db:orders",
        id: "2",
        upstream_tasks: ["db:users"],
      }),
    ];
    const { edges } = buildGraph(graphNodes);
    expect(edges).toHaveLength(1);
  });

  it("animates edges from executing nodes", () => {
    const graphNodes = [
      makeNode({
        collection_address: "db:users",
        id: "1",
        status: "executing",
        downstream_tasks: ["db:orders"],
      }),
      makeNode({
        collection_address: "db:orders",
        id: "2",
        upstream_tasks: ["db:users"],
      }),
    ];
    const { edges } = buildGraph(graphNodes);
    expect(edges[0].animated).toBe(true);
  });

  it("does not animate edges from non-executing nodes", () => {
    const graphNodes = [
      makeNode({
        collection_address: "db:users",
        id: "1",
        status: "complete",
        downstream_tasks: ["db:orders"],
      }),
      makeNode({
        collection_address: "db:orders",
        id: "2",
        upstream_tasks: ["db:users"],
      }),
    ];
    const { edges } = buildGraph(graphNodes);
    expect(edges[0].animated).toBe(false);
  });
});
