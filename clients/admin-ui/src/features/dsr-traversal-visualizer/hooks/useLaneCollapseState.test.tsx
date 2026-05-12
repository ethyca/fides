import { act, renderHook, waitFor } from "@testing-library/react";

import { LANE_COLLAPSE_STORAGE_KEY } from "../constants";
import { LaneId } from "../types";
import { useLaneCollapseState } from "./useLaneCollapseState";

describe("useLaneCollapseState", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("starts with the spec-defined defaults (only `skipped` collapsed)", async () => {
    const { result } = renderHook(() => useLaneCollapseState());
    await waitFor(() => {
      expect(result.current.collapse).toEqual({
        [LaneId.IDENTITY]: false,
        [LaneId.REACH]: false,
        [LaneId.GATED]: false,
        [LaneId.SKIPPED]: true,
      });
    });
  });

  it("exposes a `hydrated` flag that flips true after the mount effect", async () => {
    const { result } = renderHook(() => useLaneCollapseState());
    await waitFor(() => {
      expect(result.current.hydrated).toBe(true);
    });
  });

  it("persists toggles to localStorage", async () => {
    const { result } = renderHook(() => useLaneCollapseState());
    // Wait for hydration to settle
    await waitFor(() => {
      expect(result.current.collapse[LaneId.SKIPPED]).toBe(true);
    });
    act(() => {
      result.current.toggle(LaneId.REACH);
    });
    expect(result.current.collapse[LaneId.REACH]).toBe(true);
    const stored = JSON.parse(
      window.localStorage.getItem(LANE_COLLAPSE_STORAGE_KEY)!,
    );
    expect(stored.reach).toBe(true);
  });

  it("hydrates from localStorage on mount", async () => {
    window.localStorage.setItem(
      LANE_COLLAPSE_STORAGE_KEY,
      JSON.stringify({
        [LaneId.IDENTITY]: true,
        [LaneId.REACH]: false,
        [LaneId.GATED]: true,
        [LaneId.SKIPPED]: false,
      }),
    );
    const { result } = renderHook(() => useLaneCollapseState());
    await waitFor(() => {
      expect(result.current.collapse).toEqual({
        [LaneId.IDENTITY]: true,
        [LaneId.REACH]: false,
        [LaneId.GATED]: true,
        [LaneId.SKIPPED]: false,
      });
    });
  });

  it("expand() forces a lane open even if collapsed", async () => {
    const { result } = renderHook(() => useLaneCollapseState());
    // Wait for hydration — skipped starts collapsed
    await waitFor(() => {
      expect(result.current.collapse[LaneId.SKIPPED]).toBe(true);
    });
    act(() => result.current.expand(LaneId.SKIPPED));
    expect(result.current.collapse[LaneId.SKIPPED]).toBe(false);
  });

  it("expand() is idempotent", async () => {
    const { result } = renderHook(() => useLaneCollapseState());
    // Wait for hydration
    await waitFor(() => {
      expect(result.current.collapse[LaneId.SKIPPED]).toBe(true);
    });
    act(() => result.current.expand(LaneId.REACH));
    act(() => result.current.expand(LaneId.REACH));
    expect(result.current.collapse[LaneId.REACH]).toBe(false);
  });
});
