import { useEffect, useRef, useState } from "react";

function easeOut(t: number): number {
  return 1 - (1 - t) ** 3;
}

export const useCountUp = (target: number, duration = 800): number => {
  const [value, setValue] = useState(0);
  const rafRef = useRef<number>();
  const startRef = useRef<number>();
  const fromRef = useRef(0);

  useEffect(() => {
    const from = fromRef.current;

    // If already at target, skip animation
    if (from === target) {
      return undefined;
    }

    startRef.current = undefined;

    const animate = (timestamp: number) => {
      if (startRef.current === undefined) {
        startRef.current = timestamp;
      }
      const elapsed = timestamp - startRef.current;
      const t = Math.min(elapsed / duration, 1);
      const current = Math.round(from + (target - from) * easeOut(t));
      setValue(current);

      if (t < 1) {
        rafRef.current = requestAnimationFrame(animate);
      } else {
        fromRef.current = target;
      }
    };

    rafRef.current = requestAnimationFrame(animate);

    return () => {
      if (rafRef.current !== undefined) {
        cancelAnimationFrame(rafRef.current);
        // Snapshot current displayed value as the new starting point
        fromRef.current = value;
      }
    };
  }, [target, duration]); // eslint-disable-line react-hooks/exhaustive-deps

  return value;
};
