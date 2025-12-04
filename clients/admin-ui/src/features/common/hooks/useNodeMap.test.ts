import { act, renderHook } from "@testing-library/react";

import useNodeMap, { mapNodes, Node, NodeMap } from "./useNodeMap";

describe("Normalized Data Hook", () => {
  it("returns empty array when no data provided", () => {
    const { result } = renderHook(() => useNodeMap());
    const { nodes } = result.current;
    expect([...nodes.values()]).toStrictEqual([]);
  });

  it("adds new data nodes to state when updated", () => {
    const INITIAL_DATA = [{ key: 1, title: "first" }];
    const NEXT_DATA = [{ key: 2, title: "second" }];
    const { result } = renderHook((props) => useNodeMap(props), {
      initialProps: mapNodes(INITIAL_DATA),
    });
    const { nodes, update } = result.current;

    expect([...nodes.values()]).toStrictEqual(INITIAL_DATA);

    act(() => update(mapNodes(NEXT_DATA)));

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
    const { result } = renderHook((props) => useNodeMap(props), {
      initialProps: mapNodes(INITIAL_DATA),
    });
    const { nodes, update } = result.current;

    expect([...nodes.values()]).toStrictEqual(INITIAL_DATA);

    act(() => update(mapNodes(NEXT_DATA)));

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
    const INITIAL_DATA: TestNode[] = [
      { key: 1, title: "first", list: [] },
      { key: 2, title: "second", list: ["a", "b"] },
    ];
    const NEXT_DATA = mapNodes([
      { key: 1, subtitle: "changed", list: ["a", "b"] },
    ]);
    const { result } = renderHook((props) => useNodeMap(props), {
      initialProps: mapNodes(INITIAL_DATA),
    });
    const { nodes, update } = result.current;

    expect([...nodes.values()]).toStrictEqual(INITIAL_DATA);

    act(() => update(NEXT_DATA));

    expect([...result.current.nodes.values()]).toStrictEqual([
      { key: 1, title: "first", subtitle: "changed", list: ["a", "b"] },
      { key: 2, title: "second", list: ["a", "b"] },
    ]);
  });

  it("partially updates an existing node via update function", () => {
    type TestNode = Node<{
      title?: string;
      subtitle?: string;
      list?: string[];
    }>;
    const INITIAL_DATA: TestNode[] = [
      { key: 1, title: "first", list: [] },
      { key: 2, title: "second", list: ["a", "b"] },
    ];
    const NEXT_DATA = mapNodes([
      { key: 1, subtitle: "changed", list: ["a", "b"] },
    ]);
    const { result } = renderHook(() => useNodeMap());

    const { update } = result.current;

    act(() => update(mapNodes(INITIAL_DATA)));

    expect([...result.current.nodes.values()]).toStrictEqual(INITIAL_DATA);

    act(() => result.current.update(NEXT_DATA));

    expect([...result.current.nodes.values()]).toStrictEqual([
      { key: 1, title: "first", subtitle: "changed", list: ["a", "b"] },
      { key: 2, title: "second", list: ["a", "b"] },
    ]);
  });

  it("replaces existing node when partial updates are disabled", () => {
    type TestNode = Node<{ title?: string; subtitle?: string }>;
    const INITIAL_DATA: TestNode[] = [
      { key: 1, title: "first" },
      { key: 2, title: "second" },
    ];
    const NEXT_DATA = mapNodes([{ key: 1, subtitle: "changed" }]);
    const { result } = renderHook((props) => useNodeMap(props, false), {
      initialProps: mapNodes(INITIAL_DATA),
    });
    const { nodes, update } = result.current;

    expect([...nodes.values()]).toStrictEqual(INITIAL_DATA);

    act(() => update(NEXT_DATA));

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

    const { result } = renderHook((props) => useNodeMap(props), {
      initialProps: INITIAL_DATA,
    });
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
    const { result } = renderHook((props) => useNodeMap(props), {
      initialProps: mapNodes(INITIAL_DATA),
    });
    const { nodes, reset } = result.current;

    expect([...nodes.values()]).toStrictEqual(INITIAL_DATA);

    act(() => reset());

    expect([...result.current.nodes.values()]).toStrictEqual([]);
  });
});
