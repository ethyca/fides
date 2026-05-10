import { motion } from "framer-motion";
import { useState } from "react";

import {
  AstralisIcon,
  GearIcon,
  HeliosIcon,
  JanusIcon,
  LetheIcon,
  LightningIcon,
} from "~/features/poc/grid-motion/NavIcons";

import { DELPHI_HEADER_HEIGHT } from "./DelphiHeader";

const INK = "#2b2d34";
const INK_MUTED = "#53575C";
const INK_REST = "#A8AAAD";
const INK_HAIRLINE = "rgba(43, 45, 52, 0.16)";
const ROW_HOVER_BG = "rgba(43, 45, 52, 0.05)";
const ACTIVE_BG = "rgba(43, 45, 52, 0.08)";
const ACCENT_WARM = "#B96E46";

const GLASS_BG = "rgba(255, 255, 255, 0.45)";
const GLASS_BG_HOVER = "rgba(255, 255, 255, 0.62)";
const GLASS_BLUR = "blur(14px)";
const HOVER_SHADOW =
  "0 1px 0 rgba(43, 45, 52, 0.02), 0 12px 26px -22px rgba(43, 45, 52, 0.22)";

const SANS = `'Basier Square', 'Inter', system-ui, -apple-system, sans-serif`;
const MONO = `'Basier Square Mono', ui-monospace, SFMono-Regular, monospace`;

export const DELPHI_RAIL_WIDTH = 64;
const EXPANDED_WIDTH = 280;
const ICON_BUTTON_SIZE = 40;
const ICON_GAP = 6;
const SECTION_GAP = 14;

const TRANSITION = { duration: 0.5, ease: [0.22, 1, 0.36, 1] } as const;

type IconComponent = (props: { size?: number }) => JSX.Element;

type Section = {
  id: string;
  Icon: IconComponent;
  header: string | null;
  product?: string | null;
  accent?: boolean;
};

const PRODUCT_SECTIONS: Section[] = [
  {
    id: "discovery",
    Icon: AstralisIcon,
    header: "Discovery & Inventory",
    product: "Astralis",
  },
  {
    id: "consent",
    Icon: HeliosIcon,
    header: "Consent",
    product: "Helios",
  },
  {
    id: "privacy-requests",
    Icon: JanusIcon,
    header: "Privacy Requests",
    product: "Janus",
  },
  {
    id: "data-governance",
    Icon: LetheIcon,
    header: "Data Governance",
    product: "Lethe",
  },
];

const FOOTER_SECTIONS: Section[] = [
  {
    id: "integrations",
    Icon: LightningIcon,
    header: "Integrations",
    accent: true,
  },
  {
    id: "settings",
    Icon: GearIcon,
    header: "Settings",
  },
];

const ACTIVE_SECTION_ID: string = "discovery";

const HEADER_STYLE = {
  fontFamily: MONO,
  fontSize: 11,
  letterSpacing: "0.10em",
  textTransform: "uppercase" as const,
  color: INK,
  opacity: 0.62,
  whiteSpace: "nowrap" as const,
  marginBottom: 4,
};

const PRODUCT_STYLE = {
  fontFamily: SANS,
  fontSize: 14,
  letterSpacing: "-0.005em",
  color: INK,
  whiteSpace: "nowrap" as const,
};

const IconButton = ({
  section,
  isHoveredSection,
  isActiveSection,
  onMouseEnter,
  onMouseLeave,
}: {
  section: Section;
  isHoveredSection: boolean;
  isActiveSection: boolean;
  onMouseEnter: () => void;
  onMouseLeave: () => void;
}) => {
  const { Icon, accent } = section;
  const highlight = isHoveredSection || isActiveSection;
  let iconColor: string;
  if (accent) iconColor = ACCENT_WARM;
  else if (highlight) iconColor = INK;
  else iconColor = INK_REST;
  let bg: string;
  if (isActiveSection) bg = ACTIVE_BG;
  else if (isHoveredSection) bg = ROW_HOVER_BG;
  else bg = "transparent";
  return (
    <div
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
      style={{
        width: ICON_BUTTON_SIZE,
        height: ICON_BUTTON_SIZE,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        borderRadius: 4,
        background: bg,
        color: iconColor,
        cursor: "pointer",
        transition: "background 0.18s ease, color 0.18s ease",
      }}
    >
      <Icon size={22} />
    </div>
  );
};

const LabelGroup = ({
  section,
  isHoveredSection,
  onMouseEnter,
  onMouseLeave,
}: {
  section: Section;
  isHoveredSection: boolean;
  onMouseEnter: () => void;
  onMouseLeave: () => void;
}) => {
  const { header, product } = section;
  return (
    <div
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
      style={{
        padding: "8px 10px",
        borderRadius: 4,
        background: isHoveredSection ? ROW_HOVER_BG : "transparent",
        transition: "background 0.18s ease",
        cursor: "pointer",
      }}
    >
      {header ? <div style={HEADER_STYLE}>{header}</div> : null}
      {product ? <div style={PRODUCT_STYLE}>{product}</div> : null}
    </div>
  );
};

const DelphiSideNav = () => {
  const [expanded, setExpanded] = useState(false);
  const [hoveredSection, setHoveredSection] = useState<string | null>(null);

  const handleEnter = (id: string) => () => setHoveredSection(id);
  const handleLeave = (id: string) => () =>
    setHoveredSection((current) => (current === id ? null : current));

  return (
    <motion.aside
      onMouseEnter={() => setExpanded(true)}
      onMouseLeave={() => {
        setExpanded(false);
        setHoveredSection(null);
      }}
      animate={{ width: expanded ? EXPANDED_WIDTH : DELPHI_RAIL_WIDTH }}
      transition={TRANSITION}
      style={{
        position: "fixed",
        left: 0,
        top: DELPHI_HEADER_HEIGHT,
        bottom: 0,
        zIndex: 40,
        boxSizing: "border-box",
        display: "flex",
        flexDirection: "row",
        alignItems: "stretch",
        background: expanded ? GLASS_BG_HOVER : GLASS_BG,
        backdropFilter: GLASS_BLUR,
        WebkitBackdropFilter: GLASS_BLUR,
        borderRight: `1px solid ${INK_HAIRLINE}`,
        boxShadow: expanded ? HOVER_SHADOW : "none",
        overflow: "hidden",
        color: INK,
      }}
    >
      <div
        style={{
          width: DELPHI_RAIL_WIDTH,
          flexShrink: 0,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          padding: "16px 0",
        }}
      >
        <div
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
            gap: ICON_GAP,
            alignItems: "center",
          }}
        >
          {PRODUCT_SECTIONS.map((section) => (
            <IconButton
              key={section.id}
              section={section}
              isHoveredSection={hoveredSection === section.id}
              isActiveSection={section.id === ACTIVE_SECTION_ID}
              onMouseEnter={handleEnter(section.id)}
              onMouseLeave={handleLeave(section.id)}
            />
          ))}
        </div>
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: ICON_GAP,
            alignItems: "center",
          }}
        >
          {FOOTER_SECTIONS.map((section) => (
            <IconButton
              key={section.id}
              section={section}
              isHoveredSection={hoveredSection === section.id}
              isActiveSection={false}
              onMouseEnter={handleEnter(section.id)}
              onMouseLeave={handleLeave(section.id)}
            />
          ))}
        </div>
      </div>

      <motion.div
        animate={{ opacity: expanded ? 1 : 0 }}
        transition={
          expanded ? { duration: 0.25, delay: 0.18 } : { duration: 0.12 }
        }
        style={{
          flex: 1,
          minWidth: 0,
          display: "flex",
          flexDirection: "column",
          padding: "20px 16px 20px 4px",
          pointerEvents: expanded ? "auto" : "none",
        }}
      >
        <div
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
            gap: SECTION_GAP,
          }}
        >
          {PRODUCT_SECTIONS.map((section) => (
            <LabelGroup
              key={section.id}
              section={section}
              isHoveredSection={hoveredSection === section.id}
              onMouseEnter={handleEnter(section.id)}
              onMouseLeave={handleLeave(section.id)}
            />
          ))}
        </div>
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: SECTION_GAP,
          }}
        >
          {FOOTER_SECTIONS.map((section) => (
            <LabelGroup
              key={section.id}
              section={section}
              isHoveredSection={hoveredSection === section.id}
              onMouseEnter={handleEnter(section.id)}
              onMouseLeave={handleLeave(section.id)}
            />
          ))}
        </div>
      </motion.div>
    </motion.aside>
  );
};

export default DelphiSideNav;
