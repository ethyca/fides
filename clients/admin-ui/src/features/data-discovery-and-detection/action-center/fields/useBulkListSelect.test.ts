import { act, renderHook } from "@testing-library/react";

import { useBulkListSelect } from "./useBulkListSelect";

describe("useBulkListSelect", () => {
  const DEFAULT_INITIAL_STATE: Partial<ReturnType<typeof useBulkListSelect>> = {
    selectedKeys: [],
    excludedKeys: [],
    listSelectMode: "inclusive",
  };

  it("correct initial states", () => {
    const { result } = renderHook(() => useBulkListSelect([]));
    const {
      resetListSelect,
      updateListSelectMode,
      updateSelectedListItem,
      checkboxProps,
      ...listState
    } = result.current;

    expect(listState).toStrictEqual(DEFAULT_INITIAL_STATE);
  });

  it("should update select mode when calling update function", () => {
    const { result } = renderHook(() => useBulkListSelect([]));

    expect(result.current.listSelectMode).toBe("inclusive");

    act(() => result.current.updateListSelectMode("exclusive"));

    expect(result.current.listSelectMode).toBe("exclusive");
  });

  it("should update selected keys when in inclusive mode", () => {
    const { result } = renderHook(() => useBulkListSelect([]));
    const { selectedKeys, excludedKeys, listSelectMode } = result.current;

    expect(listSelectMode).toBe("inclusive");
    expect(selectedKeys).toStrictEqual([]);
    expect(excludedKeys).toStrictEqual([]);

    act(() => result.current.updateSelectedListItem(1, true));

    expect(result.current.selectedKeys).toStrictEqual([1]);
    expect(result.current.excludedKeys).toStrictEqual([]);

    act(() => result.current.updateSelectedListItem(1, false));

    expect(result.current.selectedKeys).toStrictEqual([]);
    expect(result.current.excludedKeys).toStrictEqual([]);
  });

  it("should update excluded keys when in exclusive mode", () => {
    const { result } = renderHook(() => useBulkListSelect([], {}, "exclusive"));
    const { selectedKeys, excludedKeys, listSelectMode } = result.current;

    expect(listSelectMode).toBe("exclusive");
    expect(selectedKeys).toStrictEqual([]);
    expect(excludedKeys).toStrictEqual([]);

    act(() => result.current.updateSelectedListItem(1, false));

    expect(result.current.selectedKeys).toStrictEqual([]);
    expect(result.current.excludedKeys).toStrictEqual([1]);

    act(() => result.current.updateSelectedListItem(1, true));

    expect(result.current.selectedKeys).toStrictEqual([]);
    expect(result.current.excludedKeys).toStrictEqual([]);
  });

  it("resets to the correct initial state", () => {
    const { result } = renderHook(() => useBulkListSelect([], {}));
    const {
      updateSelectedListItem,
      updateListSelectMode,
      resetListSelect,
      checkboxProps,
      ...listState
    } = result.current;

    expect(listState).toStrictEqual(DEFAULT_INITIAL_STATE);

    act(() => result.current.updateSelectedListItem(1, true));
    act(() => result.current.updateListSelectMode("exclusive"));
    act(() => result.current.updateSelectedListItem(2, false));

    expect(result.current.selectedKeys).toStrictEqual([]);
    expect(result.current.excludedKeys).toStrictEqual([2]);

    act(() => result.current.resetListSelect());

    expect(result.current.listSelectMode).toBe("inclusive");
    expect(result.current.selectedKeys).toStrictEqual([]);
    expect(result.current.excludedKeys).toStrictEqual([]);
  });

  it("resets when changing mode", () => {
    const { result } = renderHook(() => useBulkListSelect([], {}));
    const {
      updateSelectedListItem,
      updateListSelectMode,
      resetListSelect,
      checkboxProps,
      ...listState
    } = result.current;

    expect(listState).toStrictEqual(DEFAULT_INITIAL_STATE);

    act(() => result.current.updateSelectedListItem(1, true));
    act(() => result.current.updateSelectedListItem(2, true));
    act(() => result.current.updateSelectedListItem(3, true));
    act(() => result.current.updateSelectedListItem(2, false));
    act(() => result.current.updateListSelectMode("exclusive"));

    expect(result.current.listSelectMode).toStrictEqual("exclusive");
    expect(result.current.selectedKeys).toStrictEqual([]);
    expect(result.current.excludedKeys).toStrictEqual([]);

    act(() => result.current.updateSelectedListItem(1, false));
    act(() => result.current.updateSelectedListItem(2, false));
    act(() => result.current.updateSelectedListItem(3, false));
    act(() => result.current.updateSelectedListItem(2, true));
    act(() => result.current.updateListSelectMode("inclusive"));

    expect(result.current.listSelectMode).toStrictEqual("inclusive");
    expect(result.current.selectedKeys).toStrictEqual([]);
    expect(result.current.excludedKeys).toStrictEqual([]);
  });
});
