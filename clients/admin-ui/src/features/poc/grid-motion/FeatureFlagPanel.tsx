import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useRef, useState } from "react";

import {
  CHROME_GLASS_BG_HOVER,
  CHROME_GLASS_BORDER,
  CHROME_GLASS_SHADOW,
  GLASS_BG_NEUTRAL,
  GLASS_BLUR,
} from "./glass";

const INK = "#2b2e35";
const INK_MUTED = "rgba(43,46,53,0.55)";

export interface FlagDef<T extends string> {
  key: string;
  label: string;
  value: T;
  options: readonly T[];
  onChange: (next: T) => void;
}

interface FeatureFlagPanelProps {
  flags: FlagDef<string>[];
}

const FlagRow = ({ flag }: { flag: FlagDef<string> }) => {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 6,
        padding: "10px 4px",
      }}
    >
      <span
        style={{
          fontSize: 10,
          letterSpacing: "0.10em",
          textTransform: "uppercase",
          color: INK_MUTED,
        }}
      >
        {flag.label}
      </span>
      <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
        {flag.options.map((opt) => {
          const active = opt === flag.value;
          return (
            <button
              type="button"
              key={opt}
              onClick={() => flag.onChange(opt)}
              style={{
                height: 26,
                padding: "0 10px",
                border: `1px solid ${
                  active ? "rgba(43,46,53,0.18)" : "rgba(43,46,53,0.08)"
                }`,
                borderRadius: 4,
                background: active ? "rgba(43,46,53,0.06)" : "transparent",
                color: active ? INK : INK_MUTED,
                fontSize: 11,
                fontWeight: 500,
                letterSpacing: "0.02em",
                cursor: "pointer",
                transition: "background 0.15s ease, color 0.15s ease",
              }}
            >
              {opt}
            </button>
          );
        })}
      </div>
    </div>
  );
};

const FlagIcon = ({ size = 16 }: { size?: number }) => (
  <svg width={size} height={size} viewBox="0 0 16 16" fill="none">
    <path
      d="M3 2v12M3 3h8l-1.5 2 1.5 2H3"
      stroke="currentColor"
      strokeWidth={1.4}
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

const FeatureFlagPanel = ({ flags }: FeatureFlagPanelProps) => {
  const [open, setOpen] = useState(false);
  const [hoverButton, setHoverButton] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) {
      return undefined;
    }
    const onClick = (e: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
        setOpen(false);
      }
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", onClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onClick);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  return (
    <div
      ref={containerRef}
      style={{
        position: "fixed",
        bottom: 16,
        right: 16,
        zIndex: 30,
      }}
    >
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 6 }}
            transition={{ duration: 0.18, ease: [0.22, 1, 0.36, 1] }}
            style={{
              position: "absolute",
              bottom: 36,
              right: 0,
              width: 240,
              padding: "8px 12px 12px",
              border: `1px solid ${CHROME_GLASS_BORDER}`,
              borderRadius: 4,
              background: CHROME_GLASS_BG_HOVER,
              backdropFilter: GLASS_BLUR,
              WebkitBackdropFilter: GLASS_BLUR,
              boxShadow: CHROME_GLASS_SHADOW,
            }}
          >
            <div
              style={{
                fontSize: 10,
                letterSpacing: "0.12em",
                textTransform: "uppercase",
                color: INK_MUTED,
                paddingTop: 4,
                paddingBottom: 4,
                borderBottom: "1px solid rgba(43,46,53,0.06)",
                marginBottom: 4,
              }}
            >
              Feature Flags
            </div>
            {flags.map((flag) => (
              <FlagRow key={flag.key} flag={flag} />
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      <button
        type="button"
        aria-label="Toggle feature flags"
        onClick={() => setOpen((o) => !o)}
        onMouseEnter={() => setHoverButton(true)}
        onMouseLeave={() => setHoverButton(false)}
        style={{
          width: 28,
          height: 28,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          border: `1px solid ${CHROME_GLASS_BORDER}`,
          borderRadius: 4,
          background: open ? CHROME_GLASS_BG_HOVER : GLASS_BG_NEUTRAL,
          backdropFilter: GLASS_BLUR,
          WebkitBackdropFilter: GLASS_BLUR,
          boxShadow: CHROME_GLASS_SHADOW,
          color: open || hoverButton ? INK : INK_MUTED,
          cursor: "pointer",
          transition: "background 0.18s ease, color 0.18s ease",
        }}
      >
        <FlagIcon />
      </button>
    </div>
  );
};

export default FeatureFlagPanel;
