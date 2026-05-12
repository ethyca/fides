import { useCallback, useEffect, useState } from "react";

import { LANE_COLLAPSE_STORAGE_KEY } from "../constants";
import { LaneCollapseMap, LaneId } from "../types";

const DEFAULTS: LaneCollapseMap = {
  [LaneId.IDENTITY]: false,
  [LaneId.REACH]: false,
  [LaneId.GATED]: false,
  [LaneId.SKIPPED]: true,
};

const readFromStorage = (): LaneCollapseMap => {
  if (typeof window === "undefined") {
    return DEFAULTS;
  }
  try {
    const raw = window.localStorage.getItem(LANE_COLLAPSE_STORAGE_KEY);
    if (!raw) {
      return DEFAULTS;
    }
    const parsed = JSON.parse(raw) as Partial<LaneCollapseMap>;
    return { ...DEFAULTS, ...parsed };
  } catch {
    return DEFAULTS;
  }
};

const writeToStorage = (state: LaneCollapseMap) => {
  if (typeof window === "undefined") {
    return;
  }
  try {
    window.localStorage.setItem(
      LANE_COLLAPSE_STORAGE_KEY,
      JSON.stringify(state),
    );
  } catch {
    // localStorage may be disabled (private browsing); silently no-op.
  }
};

export const useLaneCollapseState = () => {
  const [collapse, setCollapse] = useState<LaneCollapseMap>(DEFAULTS);
  // `hydrated` flips true once the localStorage read in the mount effect
  // settles. Consumers can use this to gate first paint and avoid the
  // visible lane-snap that would otherwise happen when stored prefs
  // differ from `DEFAULTS`.
  const [hydrated, setHydrated] = useState(false);

  // Hydrate after mount to avoid SSR/CSR mismatches in Next.js.
  useEffect(() => {
    setCollapse(readFromStorage());
    setHydrated(true);
  }, []);

  const toggle = useCallback((lane: LaneId) => {
    setCollapse((prev) => {
      const next = { ...prev, [lane]: !prev[lane] };
      writeToStorage(next);
      return next;
    });
  }, []);

  const expand = useCallback((lane: LaneId) => {
    setCollapse((prev) => {
      if (!prev[lane]) {
        return prev;
      }
      const next = { ...prev, [lane]: false };
      writeToStorage(next);
      return next;
    });
  }, []);

  return { collapse, toggle, expand, hydrated };
};
