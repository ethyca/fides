import type { RadarChartDataPoint } from "fidesui";
import { CollapseIcon, ExpandIcon, RadarChart } from "fidesui";
import { AnimatePresence, LayoutGroup, motion } from "framer-motion";
import { useRouter } from "next/router";
import { useEffect, useRef, useState } from "react";

import ChatPanel from "../entry-point/ChatPanel";
import BackgroundGlow from "./BackgroundGlow";
import { DEFAULT_BUSINESS_UNIT_ID } from "./businessUnits";
import { CardContent } from "./CardContent";
import FeatureFlagPanel from "./FeatureFlagPanel";
import { buildBoxShadow, getGlassBgStyle, GLASS_TRANSITION } from "./glass";
import Header, { HEADER_HEIGHT } from "./Header";
import { getCardStyle, RADAR_LAYOUT } from "./layout";
import { CURRENT_PERSONA, DEFAULT_VIEW_BY_PERSONA, type View } from "./persona";
import ProductGrid, { type ProductCardVariant } from "./ProductGrid";
import { type ProductId, PRODUCTS } from "./products";
import TrendList from "./TrendList";
import { CARD_SPECS, CardId } from "./types";
import ViewToggle from "./ViewToggle";

const INK = "#2b2e35";

const GRID_VW = 60;
const GAP = 12;
const PAD_X = 32;
const PAD_TOP = HEADER_HEIGHT + 24;
const PAD_BOTTOM = 96;
const CELL_MIN = 140;

const TRANSITION = RADAR_LAYOUT.transition;

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

type Mode = "splash" | "explore";

type ChatEntryPoint = "header" | "bottom";

const CHAT_ENTRY_POINT_OPTIONS = ["header", "bottom"] as const;
const CARD_VARIANT_OPTIONS = ["minimal", "metrics"] as const;

const GridMotionExperiment = () => {
  const router = useRouter();
  const [mode, setMode] = useState<Mode>("splash");
  const [chatOpen, setChatOpen] = useState(false);
  const [navigatingTo, setNavigatingTo] = useState<ProductId | null>(null);
  const [chatEntryPoint, setChatEntryPoint] =
    useState<ChatEntryPoint>("header");
  const [cardVariant, setCardVariant] = useState<ProductCardVariant>("metrics");
  const [selectedDimension, setSelectedDimension] = useState<string | null>(
    null,
  );
  const [view, setView] = useState<View>(
    DEFAULT_VIEW_BY_PERSONA[CURRENT_PERSONA],
  );
  const [businessUnitId, setBusinessUnitId] = useState<string>(
    DEFAULT_BUSINESS_UNIT_ID,
  );
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
  }, [mode, view]);

  const exitToSplash = () => {
    setMode("splash");
    setSelectedDimension(null);
    setExpanded(new Set());
  };

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && mode === "explore") {
        exitToSplash();
      }
      if (
        chatEntryPoint === "header" &&
        (e.metaKey || e.ctrlKey) &&
        e.key.toLowerCase() === "k"
      ) {
        e.preventDefault();
        setChatOpen((prev) => !prev);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [mode, chatEntryPoint]);

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

  const selectByLabel = (label: string) => {
    if (mode === "explore" && selectedDimension === label) {
      exitToSplash();
      return;
    }
    setSelectedDimension(label);
    setMode("explore");
    if (view === "mosaic") {
      const match = CARD_SPECS.find((s) => s.label === label);
      if (match) {
        setExpanded(new Set([match.id]));
      }
    }
  };

  const handleViewChange = (next: View) => {
    setView(next);
    if (next === "mosaic" && selectedDimension) {
      const match = CARD_SPECS.find((s) => s.label === selectedDimension);
      if (match) {
        setExpanded(new Set([match.id]));
      }
    } else if (next === "trend") {
      setExpanded(new Set());
    }
  };

  const radarTarget =
    mode === "splash"
      ? {
          left: "70%",
          width: 480,
        }
      : {
          left: "20vw",
          width: 380,
        };

  const handleProductSelect = (id: ProductId) => {
    const product = PRODUCTS.find((p) => p.id === id);
    if (!product?.owned) {
      return;
    }
    setChatOpen(false);
    setNavigatingTo(id);
  };

  return (
    <>
      <BackgroundGlow />

      <Header
        businessUnitId={businessUnitId}
        onBusinessUnitChange={setBusinessUnitId}
        onCommandPalette={
          chatEntryPoint === "header" ? () => setChatOpen(true) : undefined
        }
      />

      <motion.div
        animate={{ opacity: navigatingTo ? 0 : 1 }}
        transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
        onAnimationComplete={() => {
          if (navigatingTo) {
            const product = PRODUCTS.find((p) => p.id === navigatingTo);
            if (product) {
              router.push(product.href);
            }
          }
        }}
        style={{
          minHeight: "100vh",
          position: "relative",
          boxSizing: "border-box",
        }}
      >
        <div
          style={{
            position: "fixed",
            left: 32,
            top: `calc(50% + ${HEADER_HEIGHT / 2}px)`,
            transform: "translateY(-50%)",
            width: "min(48vw, 700px)",
            height: `min(820px, calc(100vh - ${HEADER_HEIGHT}px - 64px))`,
            zIndex: 2,
            pointerEvents: mode === "splash" ? "auto" : "none",
            opacity: mode === "splash" ? 1 : 0,
            transition: "opacity 0.35s cubic-bezier(0.22, 1, 0.36, 1)",
          }}
        >
          <ProductGrid variant={cardVariant} onSelect={handleProductSelect} />
        </div>

        <motion.div
          initial={false}
          animate={radarTarget}
          transition={TRANSITION}
          style={{
            position: "fixed",
            top: `calc(50% + ${HEADER_HEIGHT / 2}px)`,
            translateX: "-50%",
            translateY: "-50%",
            display: "flex",
            flexDirection: "column",
            alignItems: "stretch",
            zIndex: 1,
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
              onDimensionClick={(_, point) => selectByLabel(point.subject)}
            />
          </div>
          <div
            style={{
              display: "flex",
              alignItems: "baseline",
              gap: 8,
              color: INK,
              marginTop: mode === "splash" ? 32 : 24,
              transition: "margin-top 0.6s cubic-bezier(0.22, 1, 0.36, 1)",
            }}
          >
            <span
              style={{
                fontFamily:
                  "'Basier Square Mono', ui-monospace, SFMono-Regular, monospace",
                fontWeight: 500,
                lineHeight: 0.9,
                letterSpacing: "-0.04em",
                fontSize: mode === "splash" ? 96 : 64,
                transition: "font-size 0.6s cubic-bezier(0.22, 1, 0.36, 1)",
              }}
            >
              {GPS_SCORE}
            </span>
            <span
              style={{
                fontFamily:
                  "'Basier Square Mono', ui-monospace, SFMono-Regular, monospace",
                fontSize: 13,
                letterSpacing: "0.08em",
                textTransform: "uppercase",
                opacity: 0.5,
              }}
            >
              / 100 Governance Posture Score ®
            </span>
          </div>
        </motion.div>

        <AnimatePresence>
          {mode === "explore" && (
            <motion.div
              key="right-panel"
              initial={{ opacity: 0, x: 24 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 24 }}
              transition={{
                duration: 0.45,
                ease: [0.22, 1, 0.36, 1],
                delay: 0.05,
              }}
              style={{
                position: "absolute",
                top: 0,
                left: `${100 - GRID_VW}vw`,
                width: `${GRID_VW}vw`,
                paddingTop: PAD_TOP,
                paddingLeft: PAD_X,
                paddingRight: PAD_X,
                paddingBottom: PAD_BOTTOM,
                boxSizing: "border-box",
                zIndex: 2,
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "flex-end",
                  marginBottom: 16,
                }}
              >
                <ViewToggle view={view} onChange={handleViewChange} />
              </div>

              {view === "trend" ? (
                <TrendList
                  radarData={RADAR_DATA}
                  selectedDimension={selectedDimension}
                  hoveredDimension={hoveredDimension}
                  onSelect={selectByLabel}
                  onHover={setHoveredDimension}
                />
              ) : (
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
                            expandedOrder.indexOf(b.id) -
                            expandedOrder.indexOf(a.id)
                          );
                        }
                        return (
                          (baseOrder.get(a.id) ?? 0) -
                          (baseOrder.get(b.id) ?? 0)
                        );
                      });
                    })().map((spec) => {
                      const isExpanded = expanded.has(spec.id);
                      const isHovered =
                        hoveredDimension === spec.label ||
                        hoveredCard === spec.id;
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
                              setSelectedDimension(spec.label);
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
                            aria-label={
                              isExpanded ? "Collapse card" : "Expand card"
                            }
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
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      {chatEntryPoint === "bottom" && (
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
      )}

      {chatEntryPoint === "header" && chatOpen && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            pointerEvents: "none",
            zIndex: 10,
          }}
        >
          <ChatPanel
            expanded={null}
            open={chatOpen}
            onOpenChange={setChatOpen}
          />
        </div>
      )}

      <FeatureFlagPanel
        flags={[
          {
            key: "cardVariant",
            label: "Product card variant",
            value: cardVariant,
            options: CARD_VARIANT_OPTIONS,
            onChange: (v) => setCardVariant(v as ProductCardVariant),
          },
          {
            key: "chatEntryPoint",
            label: "Astralis entry point",
            value: chatEntryPoint,
            options: CHAT_ENTRY_POINT_OPTIONS,
            onChange: (v) => setChatEntryPoint(v as ChatEntryPoint),
          },
        ]}
      />
    </>
  );
};

export default GridMotionExperiment;
