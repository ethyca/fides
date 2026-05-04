import { useState } from "react";

import CommandBreadcrumb from "./CommandBreadcrumb";
import {
  buildBoxShadow,
  CHROME_GLASS_BG_HOVER,
  CHROME_GLASS_BORDER,
  GLASS_BG_NEUTRAL,
  GLASS_BLUR,
} from "./glass";

const INK = "#2b2e35";
const INK_MUTED = "rgba(43,46,53,0.55)";

export const HEADER_HEIGHT = 56;
const RAIL_OFFSET = 64;

const EthycaLogo = ({ size = 22 }: { size?: number }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <rect x="2" y="2" width="20" height="20" rx="4" fill={INK} />
    <path
      d="M8 8h8M8 12h6M8 16h8"
      stroke="#f5f3f1"
      strokeWidth="1.5"
      strokeLinecap="round"
    />
  </svg>
);

const CommandPaletteEntry = () => {
  const [hover, setHover] = useState(false);
  return (
    <button
      type="button"
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        display: "flex",
        alignItems: "center",
        gap: 10,
        height: 32,
        width: 240,
        padding: "0 10px 0 12px",
        border: `1px solid ${CHROME_GLASS_BORDER}`,
        borderRadius: 8,
        background: hover ? CHROME_GLASS_BG_HOVER : "transparent",
        color: INK_MUTED,
        fontSize: 12,
        cursor: "pointer",
        transition: "background 0.18s ease",
      }}
    >
      <svg width={14} height={14} viewBox="0 0 16 16" fill="none">
        <circle cx={7} cy={7} r={5} stroke="currentColor" strokeWidth={1.4} />
        <path
          d="M11 11l3 3"
          stroke="currentColor"
          strokeWidth={1.4}
          strokeLinecap="round"
        />
      </svg>
      <span style={{ flex: 1, textAlign: "left" }}>Search or jump to…</span>
      <span
        style={{
          fontFamily:
            "'Basier Square Mono', ui-monospace, SFMono-Regular, monospace",
          fontSize: 11,
          padding: "1px 5px",
          borderRadius: 4,
          background: "rgba(43,46,53,0.06)",
          color: INK_MUTED,
          letterSpacing: "0.04em",
        }}
      >
        ⌘K
      </span>
    </button>
  );
};

const AccountAvatar = () => {
  const [hover, setHover] = useState(false);
  return (
    <button
      type="button"
      aria-label="Account"
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        width: 32,
        height: 32,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        border: `1px solid ${CHROME_GLASS_BORDER}`,
        borderRadius: "50%",
        background: hover ? CHROME_GLASS_BG_HOVER : "transparent",
        color: INK,
        fontFamily:
          "'Basier Square Mono', ui-monospace, SFMono-Regular, monospace",
        fontSize: 11,
        fontWeight: 500,
        letterSpacing: "0.04em",
        cursor: "pointer",
        transition: "background 0.18s ease",
      }}
    >
      EK
    </button>
  );
};

interface HeaderProps {
  businessUnitId: string;
  onBusinessUnitChange: (id: string) => void;
}

const Header = ({ businessUnitId, onBusinessUnitChange }: HeaderProps) => {
  return (
    <header
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        height: HEADER_HEIGHT,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        paddingLeft: RAIL_OFFSET + 8,
        paddingRight: 24,
        background: GLASS_BG_NEUTRAL,
        backdropFilter: GLASS_BLUR,
        WebkitBackdropFilter: GLASS_BLUR,
        boxShadow: buildBoxShadow(false, false),
        zIndex: 15,
        boxSizing: "border-box",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
        <EthycaLogo />
        <span
          style={{
            width: 1,
            height: 18,
            background: "rgba(43,46,53,0.12)",
          }}
        />
        <CommandBreadcrumb
          currentBusinessUnitId={businessUnitId}
          onSelect={onBusinessUnitChange}
        />
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <CommandPaletteEntry />
        <AccountAvatar />
      </div>
    </header>
  );
};

export default Header;
