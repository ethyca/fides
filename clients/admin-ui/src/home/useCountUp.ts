import { usePrefersReducedMotion } from "fidesui";
import { useEffect, useRef, useState } from "react";

function easeOut(t: number): number {
  return 1 - (1 - t) ** 3;
}

export const useCountUp = (target: number, duration = 800): number => {
  const [value, setValue] = useState(0);
  const rafRef = useRef<number | undefined>(undefined);
  const startRef = useRef<number | undefined>(undefined);
  const reduceMotion = usePrefersReducedMotion();

  useEffect(() => {
    if (reduceMotion) {
      return setValue(target);
    }

    if (target === 0) {
      setValue(0);
      return undefined;
    }

    startRef.current = undefined;

    const animate = (timestamp: number) => {
      if (startRef.current === undefined) {
        startRef.current = timestamp;
      }
      const elapsed = timestamp - startRef.current;
      const t = Math.min(elapsed / duration, 1);
      setValue(Math.round(target * easeOut(t)));

      if (t < 1) {
        rafRef.current = requestAnimationFrame(animate);
      }
    };

    rafRef.current = requestAnimationFrame(animate);

    return () => {
      if (rafRef.current !== undefined) {
        cancelAnimationFrame(rafRef.current);
      }
    };
  }, [reduceMotion, target, duration]);

  return value;
};
