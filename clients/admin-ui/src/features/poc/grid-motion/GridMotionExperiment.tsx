import type { RadarChartDataPoint } from "fidesui";
import { CollapseIcon, ExpandIcon, RadarChart } from "fidesui";
import { LayoutGroup, motion } from "framer-motion";
import { useEffect, useRef, useState } from "react";

import ChatPanel from "../entry-point/ChatPanel";
import { CardContent } from "./CardContent";
import { buildBoxShadow, getGlassBgStyle, GLASS_TRANSITION } from "./glass";
import { getCardStyle } from "./layout";
import SideNav from "./SideNav";
import { CARD_SPECS, CardId } from "./types";

const INK = "#2b2e35";
const SURFACE = "#f1efee";

const GRID_VW = 60;
const GAP = 12;
const PAD_X = 32;
const PAD_TOP = 32;
const PAD_BOTTOM = 96;
const CELL_MIN = 140;

const TRANSITION_DURATION_S = 0.5;
const TRANSITION = {
  duration: TRANSITION_DURATION_S,
  ease: [0.22, 1, 0.36, 1],
} as const;

const SINGLE_EXPAND = true;
const SWAP_STAGGER_MS = 60;

const CRITICAL_STATUSES = new Set(["error"]);

const RADAR_DATA: RadarChartDataPoint[] = [
  { subject: "Coverage", value: 78 },
  { subject: "Classification Health", value: 64 },
  { subject: "Consent Alignment", value: 82 },
  { subject: "DSR Compliance", value: 71 },
  { subject: "Policy Enforcement", value: 58 },
  { subject: "AI Readiness", value: 42, status: "error" },
  { subject: "Assessment Coverage", value: 69 },
];

const GPS_SCORE = Math.round(
  RADAR_DATA.reduce((sum, d) => sum + d.value, 0) / RADAR_DATA.length,
);

const GridMotionExperiment = () => {
  const [expanded, setExpanded] = useState<ReadonlySet<CardId>>(
    () => new Set(),
  );
  const [hoveredDimension, setHoveredDimension] = useState<string | null>(null);
  const [hoveredCard, setHoveredCard] = useState<CardId | null>(null);
  const [colCount, setColCount] = useState(0);
  const gridRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = gridRef.current;
    if (!el) {
      return undefined;
    }
    const update = () => {
      const tracks = window
        .getComputedStyle(el)
        .gridTemplateColumns.split(" ")
        .filter(Boolean);
      setColCount(tracks.length);
    };
    update();
    const ro = new ResizeObserver(update);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const toggleCard = (id: CardId) => {
    setExpanded((current) => {
      if (current.has(id)) {
        const next = new Set(current);
        next.delete(id);
        return next;
      }
      if (SINGLE_EXPAND) {
        if (current.size > 0) {
          window.setTimeout(() => {
            setExpanded(new Set([id]));
          }, SWAP_STAGGER_MS);
          return new Set();
        }
        return new Set([id]);
      }
      const next = new Set(current);
      next.add(id);
      return next;
    });
  };

  const toggleByLabel = (label: string) => {
    const match = CARD_SPECS.find((s) => s.label === label);
    if (match) {
      toggleCard(match.id);
    }
  };

  return (
    <>
      <div
        style={{
          position: "fixed",
          inset: 0,
          background: SURFACE,
          zIndex: 0,
          pointerEvents: "none",
        }}
      />

      <div
        style={{
          minHeight: "100vh",
          position: "relative",
          boxSizing: "border-box",
        }}
      >
        <div
          style={{
            position: "fixed",
            left: 0,
            top: 0,
            width: "40vw",
            height: "100vh",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            padding: 32,
            boxSizing: "border-box",
            zIndex: 1,
          }}
        >
          <div
            style={{
              width: "min(80%, 480px)",
              display: "flex",
              flexDirection: "column",
              alignItems: "stretch",
            }}
          >
            <div
              style={{
                width: "100%",
                aspectRatio: "1 / 1",
              }}
            >
              <RadarChart
                data={RADAR_DATA}
                outerRadius="80%"
                noFill
                noTickStroke
                onDimensionHover={(_, point) =>
                  setHoveredDimension(point.subject)
                }
                onDimensionLeave={() => setHoveredDimension(null)}
                onDimensionClick={(_, point) => toggleByLabel(point.subject)}
              />
            </div>
            <div
              style={{
                marginTop: 24,
                display: "flex",
                alignItems: "baseline",
                gap: 6,
                color: INK,
              }}
            >
              <span
                style={{
                  fontFamily:
                    "'Basier Square Mono', ui-monospace, SFMono-Regular, monospace",
                  fontSize: 56,
                  fontWeight: 500,
                  lineHeight: 1,
                  letterSpacing: "-0.02em",
                }}
              >
                {GPS_SCORE}
              </span>
              <span
                style={{
                  fontFamily:
                    "'Basier Square Mono', ui-monospace, SFMono-Regular, monospace",
                  fontSize: 14,
                  letterSpacing: "0.08em",
                  textTransform: "uppercase",
                  opacity: 0.5,
                }}
              >
                / 100 Governance Posture Score ®
              </span>
            </div>
          </div>
        </div>

        <div
          style={{
            marginLeft: `${100 - GRID_VW}vw`,
            width: `${GRID_VW}vw`,
            paddingTop: PAD_TOP,
            paddingLeft: PAD_X,
            paddingRight: PAD_X,
            paddingBottom: PAD_BOTTOM,
            boxSizing: "border-box",
            position: "relative",
            zIndex: 2,
          }}
        >
          <div
            ref={gridRef}
            style={{
              direction: "rtl",
              display: "grid",
              gridTemplateColumns: `repeat(auto-fit, minmax(${CELL_MIN}px, 1fr))`,
              gridAutoRows: `${CELL_MIN}px`,
              gridAutoFlow: "row dense",
              gap: GAP,
              justifyContent: "start",
            }}
          >
            <LayoutGroup>
              {(() => {
                const expandedOrder = Array.from(expanded);
                const baseOrder = new Map(
                  CARD_SPECS.map((s, i) => [s.id, i] as const),
                );
                return [...CARD_SPECS].sort((a, b) => {
                  const aExp = expanded.has(a.id);
                  const bExp = expanded.has(b.id);
                  if (aExp !== bExp) {
                    return aExp ? -1 : 1;
                  }
                  if (aExp) {
                    return (
                      expandedOrder.indexOf(b.id) - expandedOrder.indexOf(a.id)
                    );
                  }
                  return (
                    (baseOrder.get(a.id) ?? 0) - (baseOrder.get(b.id) ?? 0)
                  );
                });
              })().map((spec) => {
                const isExpanded = expanded.has(spec.id);
                const isHovered =
                  hoveredDimension === spec.label || hoveredCard === spec.id;
                const dimension = RADAR_DATA.find(
                  (d) => d.subject === spec.label,
                );
                const isCritical =
                  !!dimension?.status &&
                  CRITICAL_STATUSES.has(dimension.status);
                return (
                  <motion.div
                    key={spec.id}
                    layout
                    layoutId={spec.id}
                    onClick={() => {
                      if (!isExpanded) {
                        toggleCard(spec.id);
                      }
                    }}
                    onMouseEnter={() => setHoveredCard(spec.id)}
                    onMouseLeave={() =>
                      setHoveredCard((current) =>
                        current === spec.id ? null : current,
                      )
                    }
                    transition={TRANSITION}
                    style={{
                      ...getCardStyle(spec, isExpanded, colCount),
                      direction: "ltr",
                      cursor: isExpanded ? "default" : "pointer",
                      border: "none",
                      borderRadius: 4,
                      padding: 14,
                      overflow: "hidden",
                      position: "relative",
                      display: "flex",
                      alignItems: "stretch",
                      justifyContent: "flex-start",
                      textAlign: "left",
                      ...getGlassBgStyle(isCritical, isHovered),
                      boxShadow: buildBoxShadow(isCritical, isHovered),
                      transition: GLASS_TRANSITION,
                      color: "#2b2e35",
                    }}
                  >
                    <motion.div
                      layout="position"
                      style={{ width: "100%", height: "100%" }}
                    >
                      <CardContent spec={spec} isExpanded={isExpanded} />
                    </motion.div>
                    <button
                      type="button"
                      aria-label={isExpanded ? "Collapse card" : "Expand card"}
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleCard(spec.id);
                      }}
                      style={{
                        position: "absolute",
                        top: 10,
                        right: 10,
                        width: 16,
                        height: 16,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        padding: 0,
                        border: "none",
                        background: "transparent",
                        cursor: "pointer",
                        color: INK,
                        opacity: isHovered || isExpanded ? 0.7 : 0.3,
                        transition: "opacity 0.2s",
                      }}
                    >
                      {isExpanded ? (
                        <CollapseIcon size={10} />
                      ) : (
                        <ExpandIcon size={10} />
                      )}
                    </button>
                  </motion.div>
                );
              })}
            </LayoutGroup>
          </div>
        </div>
      </div>

      <SideNav />

      <div
        style={{
          position: "fixed",
          inset: 0,
          pointerEvents: "none",
          zIndex: 10,
        }}
      >
        <ChatPanel expanded={null} />
      </div>
    </>
  );
};

export default GridMotionExperiment;
