import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useRef, useState } from "react";

import { BUSINESS_UNITS } from "./businessUnits";
import {
  CHROME_GLASS_BG_HOVER,
  CHROME_GLASS_BORDER,
  CHROME_GLASS_SHADOW,
  GLASS_BLUR,
} from "./glass";

const INK = "#2b2e35";
const INK_MUTED = "rgba(43,46,53,0.55)";

interface BusinessUnitOptionProps {
  name: string;
  region: string;
  isCurrent: boolean;
  onClick: () => void;
}

const BusinessUnitOption = ({
  name,
  region,
  isCurrent,
  onClick,
}: BusinessUnitOptionProps) => {
  const [hover, setHover] = useState(false);
  let background: string;
  if (isCurrent) {
    background = "rgba(43,46,53,0.06)";
  } else if (hover) {
    background = "rgba(43,46,53,0.04)";
  } else {
    background = "transparent";
  }
  return (
    <button
      type="button"
      onClick={onClick}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        width: "100%",
        display: "flex",
        flexDirection: "column",
        alignItems: "flex-start",
        gap: 2,
        padding: "8px 10px",
        border: "none",
        borderRadius: 4,
        background,
        color: INK,
        fontSize: 13,
        cursor: "pointer",
        textAlign: "left",
        transition: "background 0.15s ease",
      }}
    >
      <span style={{ fontWeight: 500 }}>{name}</span>
      <span style={{ fontSize: 11, color: INK_MUTED }}>{region}</span>
    </button>
  );
};

interface CommandBreadcrumbProps {
  currentBusinessUnitId: string;
  onSelect: (id: string) => void;
}

const CommandBreadcrumb = ({
  currentBusinessUnitId,
  onSelect,
}: CommandBreadcrumbProps) => {
  const [open, setOpen] = useState(false);
  const [hover, setHover] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const current =
    BUSINESS_UNITS.find((bu) => bu.id === currentBusinessUnitId) ??
    BUSINESS_UNITS[0];

  useEffect(() => {
    if (!open) {
      return undefined;
    }
    const onClickOutside = (e: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
        setOpen(false);
      }
    };
    const onEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", onClickOutside);
    document.addEventListener("keydown", onEscape);
    return () => {
      document.removeEventListener("mousedown", onClickOutside);
      document.removeEventListener("keydown", onEscape);
    };
  }, [open]);

  return (
    <div ref={containerRef} style={{ position: "relative" }}>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        onMouseEnter={() => setHover(true)}
        onMouseLeave={() => setHover(false)}
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          height: 32,
          padding: "0 6px",
          border: "none",
          borderRadius: 4,
          background: hover ? "rgba(43,46,53,0.04)" : "transparent",
          color: INK,
          fontSize: 13,
          cursor: "pointer",
          transition: "background 0.18s ease",
        }}
      >
        <span style={{ color: INK_MUTED, fontWeight: 500 }}>Acme</span>
        <span style={{ color: INK_MUTED, fontSize: 11 }}>▸</span>
        <span style={{ color: INK, fontWeight: 500 }}>
          {current.name.replace(/^Acme\s+/, "")}
        </span>
        <span
          style={{
            marginLeft: 2,
            color: INK_MUTED,
            fontSize: 10,
            transform: open ? "rotate(180deg)" : "rotate(0deg)",
            transition: "transform 0.2s ease",
          }}
        >
          ▾
        </span>
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            transition={{ duration: 0.18, ease: [0.22, 1, 0.36, 1] }}
            style={{
              position: "absolute",
              top: "calc(100% + 6px)",
              left: 0,
              minWidth: 240,
              padding: 6,
              border: `1px solid ${CHROME_GLASS_BORDER}`,
              borderRadius: 4,
              background: CHROME_GLASS_BG_HOVER,
              backdropFilter: GLASS_BLUR,
              WebkitBackdropFilter: GLASS_BLUR,
              boxShadow: CHROME_GLASS_SHADOW,
              zIndex: 20,
            }}
          >
            {BUSINESS_UNITS.map((bu) => (
              <BusinessUnitOption
                key={bu.id}
                name={bu.name}
                region={bu.region}
                isCurrent={bu.id === currentBusinessUnitId}
                onClick={() => {
                  onSelect(bu.id);
                  setOpen(false);
                }}
              />
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default CommandBreadcrumb;
