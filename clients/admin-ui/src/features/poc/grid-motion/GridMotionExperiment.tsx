import { LayoutGroup, motion } from "framer-motion";
import { CSSProperties, useState } from "react";

import { getCardStyle } from "./layout";
import {
  ALL_CARDS,
  CardId,
  CENTER_CARDS,
  ExpandableCardId,
  LEFT_CARDS,
  LeftCardId,
} from "./types";

// Ethyca monotone: minos ink on a limestone surface.
const INK = "#2b2e35";
const SURFACE = "#f1efee";

const WIREFRAME: CSSProperties = {
  border: `1px solid ${INK}`,
  background: "transparent",
};

const CENTER_STYLE: CSSProperties = {
  border: "none",
  background: "transparent",
};

const TRANSITION = { duration: 0.5, ease: [0.22, 1, 0.36, 1] } as const;

const isLeft = (id: CardId): id is LeftCardId =>
  (LEFT_CARDS as readonly CardId[]).includes(id);

const cardLabelStyles = (isExpanded: boolean): CSSProperties => ({
  fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
  fontSize: isExpanded ? 64 : 24,
  fontWeight: 400,
  color: INK,
  letterSpacing: "-0.02em",
  transition: "font-size 0.5s cubic-bezier(0.22,1,0.36,1)",
});

const GridMotionExperiment = () => {
  const [expanded, setExpanded] = useState<ExpandableCardId>("health-score");
  const [leftStacked, setLeftStacked] = useState(false);

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 1000,
        background: SURFACE,
        padding: 16,
        boxSizing: "border-box",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(12, 1fr)",
          gridTemplateRows: "repeat(8, 1fr)",
          width: "100%",
          height: "100%",
          gap: 12,
        }}
      >
        <LayoutGroup>
          <motion.div
            layout
            transition={TRANSITION}
            style={{
              gridColumn: "5 / span 4",
              gridRow: "1 / span 8",
              display: "grid",
              gridTemplateColumns: leftStacked ? "1fr" : "1fr 1fr",
              gridTemplateRows: leftStacked ? "repeat(4, 1fr)" : "auto auto",
              alignContent: "start",
              gap: 12,
            }}
          >
            {LEFT_CARDS.map((cardId) => {
              const globalIndex = ALL_CARDS.indexOf(cardId);
              return (
                <motion.button
                  key={cardId}
                  type="button"
                  layout
                  layoutId={cardId}
                  onClick={() => setLeftStacked((v) => !v)}
                  transition={TRANSITION}
                  style={{
                    ...WIREFRAME,
                    aspectRatio: leftStacked ? undefined : "1 / 1",
                    cursor: "pointer",
                    padding: 0,
                    overflow: "hidden",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    ...cardLabelStyles(false),
                  }}
                >
                  <motion.span layout="position">{globalIndex + 1}</motion.span>
                </motion.button>
              );
            })}
          </motion.div>

          {ALL_CARDS.filter((id): id is ExpandableCardId => !isLeft(id)).map(
            (cardId) => {
              const globalIndex = ALL_CARDS.indexOf(cardId);
              const isCenter = (CENTER_CARDS as readonly CardId[]).includes(
                cardId,
              );
              const isExpanded = cardId === expanded;
              const skin: CSSProperties = isCenter ? CENTER_STYLE : WIREFRAME;
              return (
                <motion.button
                  key={cardId}
                  type="button"
                  layout
                  layoutId={cardId}
                  onClick={() => setExpanded(cardId)}
                  transition={TRANSITION}
                  style={{
                    ...getCardStyle(cardId, expanded),
                    ...skin,
                    cursor: "pointer",
                    padding: 0,
                    overflow: "hidden",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    ...cardLabelStyles(isExpanded),
                  }}
                >
                  <motion.span layout="position">{globalIndex + 1}</motion.span>
                </motion.button>
              );
            },
          )}
        </LayoutGroup>
      </div>
    </div>
  );
};

export default GridMotionExperiment;
