import { ExecutionGraphNode, ExecutionGraphNodeStatus } from "../../types";
import { buildDatasetGraph, DatasetGraphNodeType } from "../buildDatasetGraph";
import { STATUS_PRIORITY } from "../execution-graph.constants";

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

describe("buildDatasetGraph", () => {
  it("returns empty graph for empty input", () => {
    const { nodes, edges } = buildDatasetGraph([]);
    expect(nodes).toHaveLength(0);
    expect(edges).toHaveLength(0);
  });

  it("groups collections by dataset_name into a single dataset node", () => {
    const graphNodes = [
      makeNode({
        collection_address: "ds_a:users",
        dataset_name: "ds_a",
        collection_name: "users",
        status: "complete",
      }),
      makeNode({
        collection_address: "ds_a:orders",
        dataset_name: "ds_a",
        collection_name: "orders",
        status: "pending",
      }),
    ];
    const { nodes } = buildDatasetGraph(graphNodes);
    expect(nodes).toHaveLength(1);
    expect(nodes[0].id).toBe("ds_a");
    expect(nodes[0].data.totalCollections).toBe(2);
    expect(nodes[0].data.completedCollections).toBe(1);
  });

  it("creates separate dataset nodes for different datasets", () => {
    const graphNodes = [
      makeNode({
        collection_address: "ds_a:users",
        dataset_name: "ds_a",
        status: "complete",
      }),
      makeNode({
        collection_address: "ds_b:items",
        dataset_name: "ds_b",
        status: "executing",
      }),
    ];
    const { nodes } = buildDatasetGraph(graphNodes);
    expect(nodes).toHaveLength(2);
    const ids = nodes.map((n: DatasetGraphNodeType) => n.id);
    expect(ids).toContain("ds_a");
    expect(ids).toContain("ds_b");
  });

  it("computes aggregate status as worst-of across collections", () => {
    const graphNodes = [
      makeNode({
        collection_address: "ds_a:t1",
        dataset_name: "ds_a",
        status: "complete",
      }),
      makeNode({
        collection_address: "ds_a:t2",
        dataset_name: "ds_a",
        status: "error",
      }),
      makeNode({
        collection_address: "ds_a:t3",
        dataset_name: "ds_a",
        status: "executing",
      }),
    ];
    const { nodes } = buildDatasetGraph(graphNodes);
    expect(nodes[0].data.status).toBe("error");
  });

  it("tracks error and executing counts", () => {
    const graphNodes = [
      makeNode({
        collection_address: "ds_a:t1",
        dataset_name: "ds_a",
        status: "error",
      }),
      makeNode({
        collection_address: "ds_a:t2",
        dataset_name: "ds_a",
        status: "executing",
      }),
      makeNode({
        collection_address: "ds_a:t3",
        dataset_name: "ds_a",
        status: "executing",
      }),
    ];
    const { nodes } = buildDatasetGraph(graphNodes);
    expect(nodes[0].data.errorCount).toBe(1);
    expect(nodes[0].data.executingCount).toBe(2);
  });

  it("creates cross-dataset edges from downstream_tasks", () => {
    const graphNodes = [
      makeNode({
        collection_address: "ds_a:users",
        dataset_name: "ds_a",
        downstream_tasks: ["ds_b:orders"],
      }),
      makeNode({
        collection_address: "ds_b:orders",
        dataset_name: "ds_b",
        upstream_tasks: ["ds_a:users"],
      }),
    ];
    const { edges } = buildDatasetGraph(graphNodes);
    expect(edges).toHaveLength(1);
    expect(edges[0].source).toBe("ds_a");
    expect(edges[0].target).toBe("ds_b");
  });

  it("does not create edges for intra-dataset references", () => {
    const graphNodes = [
      makeNode({
        collection_address: "ds_a:users",
        dataset_name: "ds_a",
        downstream_tasks: ["ds_a:orders"],
      }),
      makeNode({
        collection_address: "ds_a:orders",
        dataset_name: "ds_a",
        upstream_tasks: ["ds_a:users"],
      }),
    ];
    const { edges } = buildDatasetGraph(graphNodes);
    expect(edges).toHaveLength(0);
  });

  it("deduplicates cross-dataset edges", () => {
    const graphNodes = [
      makeNode({
        collection_address: "ds_a:t1",
        dataset_name: "ds_a",
        downstream_tasks: ["ds_b:t1"],
      }),
      makeNode({
        collection_address: "ds_a:t2",
        dataset_name: "ds_a",
        downstream_tasks: ["ds_b:t2"],
      }),
      makeNode({
        collection_address: "ds_b:t1",
        dataset_name: "ds_b",
      }),
      makeNode({
        collection_address: "ds_b:t2",
        dataset_name: "ds_b",
      }),
    ];
    const { edges } = buildDatasetGraph(graphNodes);
    expect(edges).toHaveLength(1);
    expect(edges[0].id).toBe("ds_a->ds_b");
  });

  it("filters out internal nodes", () => {
    const graphNodes = [
      makeNode({
        collection_address: "__ROOT__:__ROOT__",
        dataset_name: "__ROOT__",
        downstream_tasks: ["ds_a:users"],
      }),
      makeNode({
        collection_address: "ds_a:users",
        dataset_name: "ds_a",
        upstream_tasks: ["__ROOT__:__ROOT__"],
      }),
      makeNode({
        collection_address: "__TERMINATE__:__TERMINATE__",
        dataset_name: "__TERMINATE__",
      }),
    ];
    const { nodes } = buildDatasetGraph(graphNodes);
    expect(nodes).toHaveLength(1);
    expect(nodes[0].id).toBe("ds_a");
  });

  it("assigns dagre layout positions to nodes", () => {
    const graphNodes = [
      makeNode({
        collection_address: "ds_a:users",
        dataset_name: "ds_a",
      }),
    ];
    const { nodes } = buildDatasetGraph(graphNodes);
    expect(typeof nodes[0].position.x).toBe("number");
    expect(typeof nodes[0].position.y).toBe("number");
  });
});

describe("STATUS_PRIORITY", () => {
  it("ranks error as highest priority", () => {
    const statuses = Object.keys(STATUS_PRIORITY) as ExecutionGraphNodeStatus[];
    const maxStatus = statuses.reduce((a, b) =>
      STATUS_PRIORITY[a] > STATUS_PRIORITY[b] ? a : b,
    );
    expect(maxStatus).toBe("error");
  });

  it("ranks skipped as lowest priority", () => {
    const statuses = Object.keys(STATUS_PRIORITY) as ExecutionGraphNodeStatus[];
    const minStatus = statuses.reduce((a, b) =>
      STATUS_PRIORITY[a] < STATUS_PRIORITY[b] ? a : b,
    );
    expect(minStatus).toBe("skipped");
  });
});
