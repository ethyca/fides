import { theme } from "antd/lib";
import type { ReactNode } from "react";
import { useRef } from "react";
import { Pie, PieChart } from "recharts";

import type { AntColorTokenKey } from "./chart-constants";
import { CHART_ANIMATION, DONUT_THICKNESS } from "./chart-constants";
import { useChartAnimation, useContainerSize } from "./chart-utils";

export interface DonutChartSegment {
  /** Values don't need to sum to 100 — Recharts sizes each segment relative to the total. */
  value: number;
  color: AntColorTokenKey;
  name?: string;
}

export type DonutChartVariant = "default" | "thick" | "thin";

export interface DonutChartProps {
  segments: DonutChartSegment[];
  centerLabel?: ReactNode;
  variant?: DonutChartVariant;
  animationDuration?: number;
  fit?: "contain" | "fill";
}

export const DonutChart = ({
  segments,
  centerLabel,
  variant = "default",
  animationDuration = CHART_ANIMATION.defaultDuration,
  fit = "contain",
}: DonutChartProps) => {
  const { token } = theme.useToken();
  const containerRef = useRef<HTMLDivElement>(null);
  const { width, height } = useContainerSize(containerRef);
  const size =
    fit === "contain" ? Math.min(width, height) : Math.max(width, height);
  const animationActive = useChartAnimation(animationDuration);

  const thickness = DONUT_THICKNESS[variant];
  const outerRadius = size / 2;
  const innerRadius = outerRadius - thickness;

  const data = segments.map((segment) => ({
    name: segment.name,
    value: segment.value,
    fill: token[segment.color],
  }));

  return (
    <div
      ref={containerRef}
      className="flex relative h-full w-full content-center justify-center"
    >
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
