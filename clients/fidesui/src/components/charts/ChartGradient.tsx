import { CHART_GRADIENT } from "./chart-constants";

export interface ChartGradientProps {
    id: string;
    color: string;
    type?: "linear" | "radial";
    /** Reverses the opacity direction (transparent at start, opaque at end). */
    inverse?: boolean;
}

/**
 * Renders a reusable SVG gradient element (`<linearGradient>` or
 * `<radialGradient>`) to be placed inside a `<defs>` block.
 *
 * - Linear gradient runs top-to-bottom (y1=0 → y2=1).
 * - Radial gradient radiates from center outward.
 * - The `inverse` prop flips the opacity direction:
 *   - Default (false): opaque at start, transparent at end.
 *   - Inverse (true):  transparent at start, opaque at end.
 */
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
            <radialGradient id={id} cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor={color} stopOpacity={startOpacity} />
                <stop offset="100%" stopColor={color} stopOpacity={endOpacity} />
            </radialGradient>
        );
    }

    return (
        <linearGradient id={id} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity={startOpacity} />
            <stop offset="100%" stopColor={color} stopOpacity={endOpacity} />
        </linearGradient>
    );
};
