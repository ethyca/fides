import { CHART_GRADIENT } from "./chart-constants";

export interface ChartGradientProps {
  id: string;
  color: string;
  type?: "linear" | "radial";
  inverse?: boolean;
}

export const ChartGradient = ({
  id,
  color,
  type = "linear",
  inverse = false,
}: ChartGradientProps) => {
  const startOpacity = inverse
    ? CHART_GRADIENT.endOpacity
    : CHART_GRADIENT.startOpacity;
  const endOpacity = inverse
    ? CHART_GRADIENT.startOpacity
    : CHART_GRADIENT.endOpacity;

  if (type === "radial") {
    return (
      <defs>
        <radialGradient id={id} cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor={color} stopOpacity={startOpacity} />
          <stop offset="100%" stopColor={color} stopOpacity={endOpacity} />
        </radialGradient>
      </defs>
    );
  }

  return (
    <defs>
      <linearGradient id={id} x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stopColor={color} stopOpacity={startOpacity} />
        <stop offset="100%" stopColor={color} stopOpacity={endOpacity} />
      </linearGradient>
    </defs>
  );
};
