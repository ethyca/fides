import { theme } from "antd/lib";
import type { ReactNode } from "react";
import { useEffect, useRef, useState } from "react";
import { Pie, PieChart } from "recharts";

import type { AntColorTokenKey } from "./chart-constants";
import { CHART_ANIMATION } from "./chart-constants";
import { useChartAnimation } from "./chart-utils";

export interface DonutChartSegment {
  value: number;
  color: AntColorTokenKey;
  name?: string;
}

export type DonutChartVariant = "default" | "thick";

const DONUT_THICKNESS: Record<DonutChartVariant, number> = {
  default: 8,
  thick: 16,
};

export interface DonutChartProps {
  segments: DonutChartSegment[];
  centerLabel?: ReactNode;
  variant?: DonutChartVariant;
  animationDuration?: number;
}

export const DonutChart = ({
  segments,
  centerLabel,
  variant = "default",
  animationDuration = CHART_ANIMATION.defaultDuration,
}: DonutChartProps) => {
  const { token } = theme.useToken();
  const containerRef = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState(0);
  const animationActive = useChartAnimation(animationDuration);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return undefined;
    const observer = new ResizeObserver(([entry]) => {
      const rect = entry.contentRect;
      setSize(Math.min(rect.width, rect.height));
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  const thickness = DONUT_THICKNESS[variant];
  const outerRadius = size / 2;
  const innerRadius = outerRadius - thickness;

  const data = segments.map((segment) => ({
    name: segment.name,
    value: segment.value,
    fill: token[segment.color],
  }));

  return (
    <div ref={containerRef} className="relative h-full w-full">
      {size > 0 && (
        <PieChart width={size} height={size}>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={innerRadius}
            outerRadius={outerRadius}
            dataKey="value"
            startAngle={90}
            endAngle={-270}
            stroke="none"
            isAnimationActive={animationDuration > 0 && animationActive}
            animationDuration={animationDuration}
            animationEasing={CHART_ANIMATION.easing}
          />
        </PieChart>
      )}
      {centerLabel != null && (
        <div className="absolute inset-0 flex items-center justify-center">
          {centerLabel}
        </div>
      )}
    </div>
  );
};
