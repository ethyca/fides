import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useRef, useState } from "react";

const INK = "#2b2d34";
const INK_MUTED = "rgba(43, 45, 52, 0.55)";
const INK_FAINT = "rgba(43, 45, 52, 0.34)";
const INK_HAIRLINE = "rgba(43, 45, 52, 0.16)";

const GLASS_BG = "rgba(255, 255, 255, 0.62)";
const GLASS_BG_HOVER = "rgba(255, 255, 255, 0.78)";
const GLASS_BLUR = "blur(14px)";

const SANS = `'Basier Square', 'Inter', system-ui, -apple-system, sans-serif`;
const MONO = `'Basier Square Mono', ui-monospace, SFMono-Regular, monospace`;

export const DELPHI_HEADER_HEIGHT = 56;

const DOMAINS = [
  { id: "a", name: "Domain A", region: "Primary" },
  { id: "b", name: "Domain B", region: "EMEA" },
  { id: "c", name: "Domain C", region: "APAC" },
];

const EthycaLogo = ({ size = 22 }: { size?: number }) => (
  <img
    src="/images/logomark-ethyca.svg"
    alt="Ethyca"
    height={size}
    style={{ height: size, width: "auto", display: "block" }}
  />
);

const HomeButton = () => {
  const [hover, setHover] = useState(false);
  return (
    <button
      type="button"
      aria-label="Home"
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        width: 36,
        height: 36,
        border: "none",
        borderRadius: 4,
        background: hover ? "rgba(43, 45, 52, 0.05)" : "transparent",
        cursor: "pointer",
        transition: "background 0.18s ease",
      }}
    >
      <EthycaLogo size={22} />
    </button>
  );
};

const Breadcrumb = () => {
  const [open, setOpen] = useState(false);
  const [hover, setHover] = useState(false);
  const [selectedId, setSelectedId] = useState("a");
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return undefined;
    const onClickOutside = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node))
        setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onClickOutside);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onClickOutside);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  const selected = DOMAINS.find((d) => d.id === selectedId) ?? DOMAINS[0];

  return (
    <div ref={ref} style={{ position: "relative" }}>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        onMouseEnter={() => setHover(true)}
        onMouseLeave={() => setHover(false)}
        style={{
          display: "flex",
          alignItems: "center",
          gap: 10,
          height: 32,
          padding: "0 8px",
          border: "none",
          borderRadius: 4,
          background: hover ? "rgba(43, 45, 52, 0.04)" : "transparent",
          color: INK,
          fontSize: 13,
          fontFamily: SANS,
          cursor: "pointer",
          transition: "background 0.18s ease",
        }}
      >
        <span style={{ color: INK_MUTED, fontWeight: 500 }}>Organization</span>
        <span style={{ color: INK_FAINT, fontSize: 11 }}>▸</span>
        <span style={{ color: INK, fontWeight: 500 }}>{selected.name}</span>
        <span
          style={{
            marginLeft: 2,
            color: INK_FAINT,
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
              minWidth: 220,
              padding: 6,
              border: `1px solid ${INK_HAIRLINE}`,
              borderRadius: 6,
              background: GLASS_BG_HOVER,
              backdropFilter: GLASS_BLUR,
              WebkitBackdropFilter: GLASS_BLUR,
              boxShadow:
                "0 1px 0 rgba(43, 45, 52, 0.02), 0 18px 36px -14px rgba(43, 45, 52, 0.30)",
              zIndex: 20,
            }}
          >
            {DOMAINS.map((d) => (
              <DomainOption
                key={d.id}
                name={d.name}
                region={d.region}
                isCurrent={d.id === selectedId}
                onClick={() => {
                  setSelectedId(d.id);
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

const DomainOption = ({
  name,
  region,
  isCurrent,
  onClick,
}: {
  name: string;
  region: string;
  isCurrent: boolean;
  onClick: () => void;
}) => {
  const [hover, setHover] = useState(false);
  const bg = isCurrent
    ? "rgba(43, 45, 52, 0.06)"
    : hover
      ? "rgba(43, 45, 52, 0.04)"
      : "transparent";
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
        background: bg,
        color: INK,
        fontSize: 13,
        fontFamily: SANS,
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

const IconButton = ({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) => {
  const [hover, setHover] = useState(false);
  return (
    <button
      type="button"
      aria-label={label}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        width: 32,
        height: 32,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        border: "none",
        borderRadius: 4,
        background: hover ? "rgba(43, 45, 52, 0.05)" : "transparent",
        color: INK_MUTED,
        cursor: "pointer",
        transition: "background 0.18s ease, color 0.18s ease",
      }}
    >
      {children}
    </button>
  );
};

const ProfileIcon = ({ size = 16 }: { size?: number }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <circle
      cx={12}
      cy={8}
      r={4}
      stroke="currentColor"
      strokeWidth={1.4}
    />
    <path
      d="M4 21c0-4.418 3.582-8 8-8s8 3.582 8 8"
      stroke="currentColor"
      strokeWidth={1.4}
      strokeLinecap="round"
    />
  </svg>
);

const SettingsIcon = ({ size = 16 }: { size?: number }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <circle cx={12} cy={12} r={3} stroke="currentColor" strokeWidth={1.4} />
    <path
      d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9c.214.516.69.916 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"
      stroke="currentColor"
      strokeWidth={1.4}
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

const DelphiHeader = () => {
  return (
    <header
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        height: DELPHI_HEADER_HEIGHT,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        paddingLeft: 16,
        paddingRight: 20,
        background: GLASS_BG,
        backdropFilter: GLASS_BLUR,
        WebkitBackdropFilter: GLASS_BLUR,
        borderBottom: `1px solid ${INK_HAIRLINE}`,
        zIndex: 50,
        boxSizing: "border-box",
        fontFamily: SANS,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <HomeButton />
        <span
          style={{
            width: 1,
            height: 18,
            background: INK_HAIRLINE,
          }}
          aria-hidden
        />
        <Breadcrumb />
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
        <IconButton label="Settings">
          <SettingsIcon />
        </IconButton>
        <IconButton label="Profile">
          <ProfileIcon />
        </IconButton>
      </div>
    </header>
  );
};

export default DelphiHeader;
