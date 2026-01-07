import { act, renderHook } from "@testing-library/react";

import { useSelection } from "./useSelection";

describe("useSelection", () => {
  describe("basic selection functionality", () => {
    it("initializes with empty selection", () => {
      const { result } = renderHook(() => useSelection());

      expect(result.current.selectedIds).toEqual([]);
    });

    it("allows setting selected ids", () => {
      const { result } = renderHook(() => useSelection());

      act(() => {
        result.current.setSelectedIds(["1", "2", "3"]);
      });

      expect(result.current.selectedIds).toEqual(["1", "2", "3"]);
    });

    it("clears selected ids", () => {
      const { result } = renderHook(() => useSelection());

      act(() => {
        result.current.setSelectedIds(["1", "2", "3"]);
      });

      expect(result.current.selectedIds).toEqual(["1", "2", "3"]);

      act(() => {
        result.current.clearSelectedIds();
      });

      expect(result.current.selectedIds).toEqual([]);
    });
  });

  describe("select all functionality", () => {
    it("returns unchecked state when no items are selected", () => {
      const { result } = renderHook(() =>
        useSelection({
          currentPageKeys: ["1", "2", "3"],
        }),
      );

      expect(result.current.checkboxSelectState).toBe("unchecked");
    });

    it("returns checked state when all current page items are selected", () => {
      const { result } = renderHook(() =>
        useSelection({
          currentPageKeys: ["1", "2", "3"],
        }),
      );

      act(() => {
        result.current.setSelectedIds(["1", "2", "3"]);
      });

      expect(result.current.checkboxSelectState).toBe("checked");
    });

    it("returns indeterminate state when some current page items are selected", () => {
      const { result } = renderHook(() =>
        useSelection({
          currentPageKeys: ["1", "2", "3"],
        }),
      );

      act(() => {
        result.current.setSelectedIds(["1", "2"]);
      });

      expect(result.current.checkboxSelectState).toBe("indeterminate");
    });

    it("returns unchecked state when currentPageKeys is empty", () => {
      const { result } = renderHook(() =>
        useSelection({
          currentPageKeys: [],
        }),
      );

      expect(result.current.checkboxSelectState).toBe("unchecked");
    });

    it("returns unchecked state when currentPageKeys is not provided", () => {
      const { result } = renderHook(() => useSelection());

      expect(result.current.checkboxSelectState).toBe("unchecked");
    });

    it("handles select all - selects all current page items", () => {
      const { result } = renderHook(() =>
        useSelection({
          currentPageKeys: ["1", "2", "3"],
        }),
      );

      act(() => {
        result.current.handleSelectAll(true);
      });

      expect(result.current.selectedIds).toEqual(["1", "2", "3"]);
      expect(result.current.checkboxSelectState).toBe("checked");
    });

    it("handles deselect all - deselects all current page items", () => {
      const { result } = renderHook(() =>
        useSelection({
          currentPageKeys: ["1", "2", "3"],
        }),
      );

      act(() => {
        result.current.setSelectedIds(["1", "2", "3"]);
      });

      expect(result.current.checkboxSelectState).toBe("checked");

      act(() => {
        result.current.handleSelectAll(false);
      });

      expect(result.current.selectedIds).toEqual([]);
      expect(result.current.checkboxSelectState).toBe("unchecked");
    });

    it("preserves selections from other pages when selecting current page", () => {
      const { result } = renderHook(() =>
        useSelection({
          currentPageKeys: ["4", "5", "6"],
        }),
      );

      // Pre-select items from a different page
      act(() => {
        result.current.setSelectedIds(["1", "2", "3"]);
      });

      // Select all items on current page
      act(() => {
        result.current.handleSelectAll(true);
      });

      expect(result.current.selectedIds).toEqual(
        expect.arrayContaining(["1", "2", "3", "4", "5", "6"]),
      );
      expect(result.current.selectedIds).toHaveLength(6);
    });

    it("only deselects current page items when deselecting all", () => {
      const { result } = renderHook(() =>
        useSelection({
          currentPageKeys: ["4", "5", "6"],
        }),
      );

      // Select items from different pages
      act(() => {
        result.current.setSelectedIds(["1", "2", "3", "4", "5", "6"]);
      });

      // Deselect all items on current page
      act(() => {
        result.current.handleSelectAll(false);
      });

      expect(result.current.selectedIds).toEqual(["1", "2", "3"]);
    });

    it("shows checked state when all current page items are selected even with other selections", () => {
      const { result } = renderHook(() =>
        useSelection({
          currentPageKeys: ["4", "5", "6"],
        }),
      );

      // Select items from different pages including current page
      act(() => {
        result.current.setSelectedIds(["1", "2", "3", "4", "5", "6"]);
      });

      expect(result.current.checkboxSelectState).toBe("checked");
    });

    it("shows indeterminate state when only some current page items are selected with other selections", () => {
      const { result } = renderHook(() =>
        useSelection({
          currentPageKeys: ["4", "5", "6"],
        }),
      );

      // Select some items from current page and some from other pages
      act(() => {
        result.current.setSelectedIds(["1", "2", "3", "4", "5"]);
      });

      expect(result.current.checkboxSelectState).toBe("indeterminate");
    });

    it("does nothing when handleSelectAll is called without currentPageKeys", () => {
      const { result } = renderHook(() => useSelection());

      act(() => {
        result.current.handleSelectAll(true);
      });

      expect(result.current.selectedIds).toEqual([]);
    });
  });
});
