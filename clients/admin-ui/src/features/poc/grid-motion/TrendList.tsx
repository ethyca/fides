import type { RadarChartDataPoint } from "fidesui";

import {
  GLASS_BG_CRITICAL,
  GLASS_BG_NEUTRAL,
  GLASS_BG_NEUTRAL_HOVER,
  GLASS_TRANSITION,
} from "./glass";
import Sparkline from "./Sparkline";
import { TREND_DATA } from "./trendData";
import { CARD_SPECS } from "./types";

const INK = "#2b2e35";
const INK_MUTED = "rgba(43,46,53,0.55)";
const ACCENT_WARM = "#C97B3D";
const MONO_FONT =
  "'Basier Square Mono', ui-monospace, SFMono-Regular, monospace";

interface TrendListProps {
  radarData: readonly RadarChartDataPoint[];
  selectedDimension: string | null;
  hoveredDimension: string | null;
  onSelect: (label: string) => void;
  onHover: (label: string | null) => void;
}

const TrendList = ({
  radarData,
  selectedDimension,
  hoveredDimension,
  onSelect,
  onHover,
}: TrendListProps) => {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 8,
        width: "100%",
      }}
    >
      {CARD_SPECS.slice()
        .sort((a, b) => a.collapsedOrder - b.collapsedOrder)
        .map((spec) => {
          const dim = radarData.find((d) => d.subject === spec.label);
          if (!dim) {
            return null;
          }
          const trend = TREND_DATA[spec.label];
          const isCritical = dim.status === "error";
          const isSelected = selectedDimension === spec.label;
          const isHovered = hoveredDimension === spec.label;
          const highlight = isSelected || isHovered;

          let background: string;
          if (isCritical) {
            background = GLASS_BG_CRITICAL;
          } else if (highlight) {
            background = GLASS_BG_NEUTRAL_HOVER;
          } else {
            background = GLASS_BG_NEUTRAL;
          }

          const delta = trend?.delta ?? 0;
          let deltaSign: string;
          if (delta > 0) {
            deltaSign = "↑";
          } else if (delta < 0) {
            deltaSign = "↓";
          } else {
            deltaSign = "→";
          }
          const deltaColor = isCritical || delta < 0 ? ACCENT_WARM : INK_MUTED;

          return (
            <button
              type="button"
              key={spec.id}
              onClick={() => onSelect(spec.label)}
              onMouseEnter={() => onHover(spec.label)}
              onMouseLeave={() => onHover(null)}
              style={{
                display: "grid",
                gridTemplateColumns: "1fr auto",
                alignItems: "center",
                gap: 16,
                width: "100%",
                padding: "14px 18px",
                border: "none",
                borderRadius: 6,
                textAlign: "left",
                cursor: "pointer",
                color: INK,
                ...(isCritical
                  ? { backgroundImage: background }
                  : { backgroundColor: background }),
                boxShadow: isSelected
                  ? "inset 0 0 0 1px rgba(43,46,53,0.10), 0 1px 2px rgba(43,46,53,0.04)"
                  : "inset 0 0 0 1px rgba(43,46,53,0.04)",
                transition: GLASS_TRANSITION,
              }}
            >
              <div style={{ minWidth: 0 }}>
                <div
                  style={{
                    fontSize: 10,
                    letterSpacing: "0.10em",
                    textTransform: "uppercase",
                    color: INK_MUTED,
                    marginBottom: 4,
                    whiteSpace: "nowrap",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                  }}
                >
                  {spec.label}
                </div>
                <div
                  style={{ display: "flex", alignItems: "baseline", gap: 10 }}
                >
                  <span
                    style={{
                      fontFamily: MONO_FONT,
                      fontSize: 32,
                      fontWeight: 500,
                      lineHeight: 1,
                      letterSpacing: "-0.02em",
                      color: INK,
                    }}
                  >
                    {dim.value}
                  </span>
                  <span
                    style={{
                      fontFamily: MONO_FONT,
                      fontSize: 12,
                      color: deltaColor,
                      letterSpacing: "0.02em",
                    }}
                  >
                    {deltaSign} {Math.abs(delta)}
                  </span>
                </div>
              </div>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "flex-end",
                }}
              >
                {trend && (
                  <Sparkline
                    points={trend.points}
                    width={140}
                    height={40}
                    stroke={isCritical ? ACCENT_WARM : INK}
                    fill={
                      isCritical
                        ? "rgba(201,123,61,0.10)"
                        : "rgba(43,46,53,0.05)"
                    }
                  />
                )}
              </div>
            </button>
          );
        })}
    </div>
  );
};

export default TrendList;
