import { useCallback, useEffect, useRef, useState } from "preact/hooks";

import { useLiveRegion } from "../providers/live-region-context";

const BUTTON_COMPLETE_DELAY = 3000;

interface UseAutoResetFlagReturn {
  isActive: boolean;
  activate: (durationMs?: number) => void;
  deactivate: () => void;
}

/**
 * Manages a boolean flag that automatically resets to false after a delay.
 * - Calling `activate()` sets the flag to true and schedules a reset after `durationMs`.
 * - Repeated `activate()` calls while active will reset the timer.
 * - `deactivate()` clears any pending timer and sets the flag to false.
 */
const useAutoResetFlag = (
  initial: boolean = false,
  defaultDurationMs: number = BUTTON_COMPLETE_DELAY,
): UseAutoResetFlagReturn => {
  const [isActive, setIsActive] = useState<boolean>(initial);
  const timeoutRef = useRef<number | null>(null);
  const { clear: clearLiveRegion } = useLiveRegion();

  const clearTimer = useCallback(() => {
    if (timeoutRef.current !== null) {
      window.clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  }, []);

  const deactivate = useCallback(() => {
    clearTimer();
    setIsActive(false);
    clearLiveRegion();
  }, [clearTimer, clearLiveRegion]);

  const activate = useCallback(
    (durationMs?: number) => {
      clearTimer();
      setIsActive(true);
      const delay = durationMs ?? defaultDurationMs;
      timeoutRef.current = window.setTimeout(() => {
        setIsActive(false);
        clearLiveRegion();
        timeoutRef.current = null;
      }, delay) as unknown as number;
    },
    [clearTimer, defaultDurationMs, clearLiveRegion],
  );

  useEffect(() => () => clearTimer(), [clearTimer]);

  return { isActive, activate, deactivate };
};

export default useAutoResetFlag;
