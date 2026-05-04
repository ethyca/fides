import {
  CHROME_GLASS_BG,
  CHROME_GLASS_BORDER,
  CHROME_GLASS_SHADOW,
  GLASS_BLUR,
} from "./glass";
import type { View } from "./persona";

const INK = "#2b2e35";
const INK_MUTED = "rgba(43,46,53,0.55)";

interface ViewToggleProps {
  view: View;
  onChange: (view: View) => void;
}

const OPTIONS: { value: View; label: string }[] = [
  { value: "trend", label: "Trend" },
  { value: "mosaic", label: "Mosaic" },
];

const ViewToggle = ({ view, onChange }: ViewToggleProps) => {
  return (
    <div
      role="tablist"
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 2,
        height: 36,
        padding: 3,
        border: `1px solid ${CHROME_GLASS_BORDER}`,
        borderRadius: 999,
        background: CHROME_GLASS_BG,
        backdropFilter: GLASS_BLUR,
        WebkitBackdropFilter: GLASS_BLUR,
        boxShadow: CHROME_GLASS_SHADOW,
      }}
    >
      {OPTIONS.map((opt) => {
        const active = opt.value === view;
        return (
          <button
            type="button"
            role="tab"
            aria-selected={active}
            key={opt.value}
            onClick={() => onChange(opt.value)}
            style={{
              height: 28,
              padding: "0 14px",
              border: "none",
              borderRadius: 999,
              background: active ? "rgba(255,255,255,0.7)" : "transparent",
              color: active ? INK : INK_MUTED,
              fontSize: 12,
              fontWeight: 500,
              letterSpacing: "0.02em",
              cursor: "pointer",
              boxShadow: active
                ? "0 1px 2px rgba(43,46,53,0.06), inset 0 0 0 1px rgba(255,255,255,0.6)"
                : "none",
              transition: "background 0.18s ease, color 0.18s ease",
            }}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
};

export default ViewToggle;
