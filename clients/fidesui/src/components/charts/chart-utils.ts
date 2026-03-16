import type { RefObject } from "react";
import { useEffect, useState } from "react";

export const useContainerSize = (
  ref: RefObject<HTMLElement | null>,
): number => {
  const [size, setSize] = useState(0);
  useEffect(() => {
    const el = ref.current;
    if (!el) {
      return undefined;
    }
    const observer = new ResizeObserver(([entry]) => {
      const rect = entry.contentRect;
      setSize(Math.min(rect.width, rect.height));
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, [ref]);
  return size;
};

export const useChartAnimation = (animationDuration: number): boolean => {
  const [animationActive, setAnimationActive] = useState(true);
  useEffect(() => {
    if (animationDuration <= 0) {
      return undefined;
    }
    const startTime = performance.now();
    let animationId: number;
    const tick = (now: number) => {
      if (now - startTime >= animationDuration) {
        setAnimationActive(false);
      } else {
        animationId = requestAnimationFrame(tick);
      }
    };
    animationId = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(animationId);
  }, [animationDuration]);
  return animationActive;
};
