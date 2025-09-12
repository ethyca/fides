import { useCallback, useEffect, useState } from "react";

// Global state for showCompleted
let globalShowCompleted = false;
let listeners: Set<(value: boolean) => void> = new Set();

// Global function to toggle showCompleted (exposed to console)
const showCompleted = (value?: boolean) => {
  if (value !== undefined) {
    globalShowCompleted = value;
  } else {
    globalShowCompleted = !globalShowCompleted;
  }

  // Notify all listeners
  listeners.forEach(listener => listener(globalShowCompleted));

  console.log(`showCompleted is now: ${globalShowCompleted}`);
  return globalShowCompleted;
};

// Expose to global window object for console access
if (typeof window !== "undefined") {
  (window as any).showCompleted = showCompleted;
}

// Hook to use the showCompleted state
export const useShowCompletedState = () => {
  const [showCompletedState, setShowCompletedState] = useState(globalShowCompleted);

  useEffect(() => {
    const listener = (value: boolean) => setShowCompletedState(value);
    listeners.add(listener);

    return () => {
      listeners.delete(listener);
    };
  }, []);

  const toggle = useCallback(() => {
    showCompleted();
  }, []);

  const set = useCallback((value: boolean) => {
    showCompleted(value);
  }, []);

  return {
    showCompleted: showCompletedState,
    toggle,
    set,
  };
};
