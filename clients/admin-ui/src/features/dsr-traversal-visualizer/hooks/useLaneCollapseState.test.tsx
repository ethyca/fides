import { act, renderHook, waitFor } from "@testing-library/react";

import { LANE_COLLAPSE_STORAGE_KEY } from "../constants";
import { useLaneCollapseState } from "./useLaneCollapseState";

describe("useLaneCollapseState", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("starts with the spec-defined defaults (only `skipped` collapsed)", async () => {
    const { result } = renderHook(() => useLaneCollapseState());
    await waitFor(() => {
      expect(result.current.collapse).toEqual({
        identity: false,
        reach: false,
        gated: false,
        skipped: true,
      });
    });
  });

  it("persists toggles to localStorage", async () => {
    const { result } = renderHook(() => useLaneCollapseState());
    // Wait for hydration to settle
    await waitFor(() => {
      expect(result.current.collapse.skipped).toBe(true);
    });
    act(() => {
      result.current.toggle("reach");
    });
    expect(result.current.collapse.reach).toBe(true);
    const stored = JSON.parse(
      window.localStorage.getItem(LANE_COLLAPSE_STORAGE_KEY)!,
    );
    expect(stored.reach).toBe(true);
  });

  it("hydrates from localStorage on mount", async () => {
    window.localStorage.setItem(
      LANE_COLLAPSE_STORAGE_KEY,
      JSON.stringify({
        identity: true,
        reach: false,
        gated: true,
        skipped: false,
      }),
    );
    const { result } = renderHook(() => useLaneCollapseState());
    await waitFor(() => {
      expect(result.current.collapse).toEqual({
        identity: true,
        reach: false,
        gated: true,
        skipped: false,
      });
    });
  });

  it("expand() forces a lane open even if collapsed", async () => {
    const { result } = renderHook(() => useLaneCollapseState());
    // Wait for hydration — skipped starts collapsed
    await waitFor(() => {
      expect(result.current.collapse.skipped).toBe(true);
    });
    act(() => result.current.expand("skipped"));
    expect(result.current.collapse.skipped).toBe(false);
  });

  it("expand() is idempotent", async () => {
    const { result } = renderHook(() => useLaneCollapseState());
    // Wait for hydration
    await waitFor(() => {
      expect(result.current.collapse.skipped).toBe(true);
    });
    act(() => result.current.expand("reach"));
    act(() => result.current.expand("reach"));
    expect(result.current.collapse.reach).toBe(false);
  });
});
