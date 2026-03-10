import { act, renderHook } from "@testing-library/react";
import _ from "lodash";

import useNodeMap, { mapNodes, mergeNodes, Node, NodeMap } from "./useNodeMap";

describe("Normalized Data Hook", () => {
  it("returns empty array when no data provided", () => {
    const { result } = renderHook(() => useNodeMap());
    const { nodes } = result.current;
    expect([...nodes.values()]).toStrictEqual([]);
  });

  it("adds new data nodes to state when updated", () => {
    const INITIAL_DATA = [{ key: 1, title: "first" }];
    const NEXT_DATA = [{ key: 2, title: "second" }];
    const { result } = renderHook(() => useNodeMap());

    act(() => result.current.update(mapNodes(INITIAL_DATA)));

    expect([...result.current.nodes.values()]).toStrictEqual(INITIAL_DATA);

    act(() => result.current.update(mapNodes(NEXT_DATA)));

    expect([...result.current.nodes.values()]).toStrictEqual([
      ...INITIAL_DATA,
      ...NEXT_DATA,
    ]);
  });

  it("updates existing nodes", () => {
    const INITIAL_DATA = [
      { key: 1, title: "first" },
      { key: 2, title: "second" },
    ];
    const NEXT_DATA = [
      { key: 1, title: "changed" },
      { key: 3, title: "third" },
    ];
    const { result } = renderHook(() => useNodeMap());

    act(() => result.current.update(mapNodes(INITIAL_DATA)));

    expect([...result.current.nodes.values()]).toStrictEqual(INITIAL_DATA);

    act(() => result.current.update(mapNodes(NEXT_DATA)));

    expect([...result.current.nodes.values()]).toStrictEqual([
      { key: 1, title: "changed" },
      { key: 2, title: "second" },
      { key: 3, title: "third" },
    ]);
  });

  it("partially updates an existing node", () => {
    type TestNode = Node<{
      title?: string;
      subtitle?: string;
      list?: string[];
    }>;
    const INITIAL_DATA: NodeMap<TestNode> = mapNodes([
      { key: 1, title: "first", list: [] },
      { key: 2, title: "second", list: ["a", "b"] },
      { key: 3, title: "third", list: ["a", "b", "c"] },
    ]);
    const NEXT_DATA = mapNodes([
      { key: 1, subtitle: "changed", list: ["a", "b", "c"] },
      { key: 3, list: ["a", "c"] },
    ]);

    const { result } = renderHook(() => useNodeMap());

    act(() => result.current.update(INITIAL_DATA));

    expect([...result.current.nodes.values()]).toStrictEqual([
      ...INITIAL_DATA.values(),
    ]);

    act(() => result.current.update(NEXT_DATA));

    expect([...result.current.nodes.values()]).toStrictEqual([
      { key: 1, subtitle: "changed", list: ["a", "b", "c"] },
      { key: 2, title: "second", list: ["a", "b"] },
      { key: 3, list: ["a", "c"] },
    ]);
  });

  it("replaces existing node when partial updates are disabled", () => {
    type TestNode = Node<{ title?: string; subtitle?: string }>;
    const INITIAL_DATA: TestNode[] = [
      { key: 1, title: "first" },
      { key: 2, title: "second" },
    ];
    const NEXT_DATA = mapNodes([{ key: 1, subtitle: "changed" }]);
    const { result } = renderHook(() => useNodeMap(false));

    act(() => result.current.update(mapNodes(INITIAL_DATA)));

    expect([...result.current.nodes.values()]).toStrictEqual(INITIAL_DATA);

    act(() => result.current.update(NEXT_DATA));

    expect([...result.current.nodes.values()]).toStrictEqual([
      { key: 1, subtitle: "changed" },
      { key: 2, title: "second" },
    ]);
  });

  it.skip("removes node value when explicitly removed", () => {
    type TestNodes = NodeMap<{ title?: string; subtitle?: string }>;
    const INITIAL_DATA: TestNodes = mapNodes([
      { key: 1, title: "first", subtitle: "ghost" },
      { key: 2, title: "second" },
    ]);
    const NEXT_DATA = mapNodes([{ key: 1, subtitle: undefined }]);

    const { result } = renderHook(() => useNodeMap());
    const { nodes, update } = result.current;

    expect([...nodes.values()]).toStrictEqual(INITIAL_DATA);

    act(() => update(NEXT_DATA));

    expect([...result.current.nodes.values()]).toStrictEqual([
      { key: 1, title: "first" },
      { key: 2, title: "second" },
    ]);
  });

  it("resetting all nodes", () => {
    const INITIAL_DATA = [
      { key: 1, title: "first" },
      { key: 2, title: "second" },
    ];
    const { result } = renderHook(() => useNodeMap());

    act(() => result.current.update(mapNodes(INITIAL_DATA)));

    expect([...result.current.nodes.values()]).toStrictEqual(INITIAL_DATA);

    act(() => result.current.reset());

    expect([...result.current.nodes.values()]).toStrictEqual([]);
  });
});

describe("mergeNodes", () => {
  it("should recursively merge data", () => {
    const INITIAL_DATA = mapNodes([
      { key: 1, title: "first" },
      { key: 2, subtitle: "exists" },
    ]);

    const NEXT_DATA = mapNodes([
      { key: 1, subtitle: "changed" },
      { key: 3, title: "third" },
    ]);

    const mergedNodes = mergeNodes(INITIAL_DATA, NEXT_DATA);

    expect([...mergedNodes.values()]).toStrictEqual([
      { key: 1, title: "first", subtitle: "changed" },
      { key: 2, subtitle: "exists" },
      { key: 3, title: "third" },
    ]);
  });

  it("should not mutate data references", () => {
    const INITIAL_DATA = mapNodes([
      { key: 1, title: "first" },
      { key: 2, title: "second" },
    ]);
    const INITIAL_DATA_CLONE = _.cloneDeep(INITIAL_DATA);

    const NEXT_DATA = mapNodes([
      { key: 1, title: "changed" },
      { key: 3, title: "third" },
    ]);
    const NEXT_DATA_CLONE = _.cloneDeep(NEXT_DATA);

    /* Check values are cloned correctly */
    expect(INITIAL_DATA).toStrictEqual(INITIAL_DATA_CLONE);
    expect(NEXT_DATA).toStrictEqual(NEXT_DATA_CLONE);

    mergeNodes(INITIAL_DATA, NEXT_DATA);

    /* re-check that the cloned values match */
    expect(INITIAL_DATA).toStrictEqual(INITIAL_DATA_CLONE);
    expect(NEXT_DATA).toStrictEqual(NEXT_DATA_CLONE);
  });
});
