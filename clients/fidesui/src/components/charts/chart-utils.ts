import { useEffect, useState } from "react";

export const useChartAnimation = (animationDuration: number): boolean => {
  const [animationActive, setAnimationActive] = useState(true);
  useEffect(() => {
    if (animationDuration <= 0) return;
    const timer = setTimeout(() => setAnimationActive(false), animationDuration);
    return () => clearTimeout(timer);
  }, [animationDuration]);
  return animationActive;
};
