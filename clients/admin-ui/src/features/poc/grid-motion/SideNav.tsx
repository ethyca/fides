import { motion } from "framer-motion";
import { useState } from "react";

import {
  buildBoxShadow,
  GLASS_BLUR,
  GLASS_TRANSITION,
  getGlassBgStyle,
} from "./glass";
import {
  AstralisIcon,
  FidesIcon,
  GearIcon,
  HeliosIcon,
  JanusIcon,
  LetheIcon,
  LightningIcon,
} from "./NavIcons";

const INK = "#2b2e35";
const INK_MUTED = "#53575C";
const INK_REST = "#A8AAAD";
const ROW_HOVER_BG = "rgba(43,46,53,0.05)";
const ACTIVE_BG = "rgba(43,46,53,0.08)";
const ACCENT_WARM = "#C97B3D";

const RAIL_WIDTH = 64;
const COLLAPSED_WIDTH = RAIL_WIDTH;
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
  items: string[];
  accent?: boolean;
  brand?: boolean;
};

const BRAND_SECTION: Section = {
  id: "fides",
  Icon: FidesIcon,
  header: null,
  items: [],
  brand: true,
};

const PRODUCT_SECTIONS: Section[] = [
  {
    id: "discovery",
    Icon: AstralisIcon,
    header: "Discovery & Inventory",
    items: [
      "Overview",
      "Activity Log",
      "Systems",
      "Datasets",
      "Data Catalog",
      "Data Lineage",
      "Reports",
    ],
  },
  {
    id: "consent",
    Icon: HeliosIcon,
    header: "Consent",
    items: [
      "Overview",
      "Vendors",
      "Privacy Notices",
      "Privacy Experiences",
      "Consent Report",
      "Consent Settings",
    ],
  },
  {
    id: "privacy-requests",
    Icon: JanusIcon,
    header: "Privacy Requests",
    items: [
      "Overview",
      "Request Manager",
      "DSR Policies",
      "Notifications",
      "Request Settings",
    ],
  },
  {
    id: "data-governance",
    Icon: LetheIcon,
    header: "Data Governance",
    items: [
      "Overview",
      "Access Control",
      "Access Policies",
      "Data Purposes",
      "Data Consumers",
      "Privacy Assessments",
    ],
  },
];

const FOOTER_SECTIONS: Section[] = [
  {
    id: "integrations",
    Icon: LightningIcon,
    header: "Integrations",
    items: ["Integration List", "Email Providers", "Chat Providers"],
    accent: true,
  },
  {
    id: "settings",
    Icon: GearIcon,
    header: null,
    items: ["Settings"],
  },
];

const ACTIVE_SECTION_ID = "discovery";
const ACTIVE_ITEM = "Overview";

const SECTION_HEADER_STYLE = {
  fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
  fontSize: 11,
  letterSpacing: "0.08em",
  textTransform: "uppercase" as const,
  color: INK,
  opacity: 0.5,
  marginBottom: 4,
  whiteSpace: "nowrap" as const,
};

const ITEM_BASE_STYLE = {
  fontSize: 13,
  lineHeight: "22px",
  whiteSpace: "nowrap" as const,
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  paddingRight: 4,
};

type IconButtonProps = {
  section: Section;
  isHoveredSection: boolean;
  isActiveSection: boolean;
  onMouseEnter: () => void;
  onMouseLeave: () => void;
};

const IconButton = ({
  section,
  isHoveredSection,
  isActiveSection,
  onMouseEnter,
  onMouseLeave,
}: IconButtonProps) => {
  const { Icon, accent, brand } = section;
  const highlight = isHoveredSection || isActiveSection;
  let iconColor: string;
  if (brand) {
    iconColor = INK;
  } else if (accent) {
    iconColor = ACCENT_WARM;
  } else if (highlight) {
    iconColor = INK;
  } else {
    iconColor = INK_REST;
  }
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
        background: isActiveSection
          ? ACTIVE_BG
          : isHoveredSection
            ? ROW_HOVER_BG
            : "transparent",
        color: iconColor,
        cursor: "pointer",
        transition: "background 0.18s ease, color 0.18s ease",
      }}
    >
      <Icon size={brand ? 18 : 22} />
    </div>
  );
};

type LabelGroupProps = {
  section: Section;
  isHoveredSection: boolean;
  isActiveSection: boolean;
  onMouseEnter: () => void;
  onMouseLeave: () => void;
};

const LabelGroup = ({
  section,
  isHoveredSection,
  isActiveSection,
  onMouseEnter,
  onMouseLeave,
}: LabelGroupProps) => {
  const { header, items, brand } = section;
  if (brand) {
    return null;
  }
  return (
    <div
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
      style={{
        padding: "6px 8px",
        borderRadius: 4,
        background: isHoveredSection ? ROW_HOVER_BG : "transparent",
        transition: "background 0.18s ease",
        cursor: "pointer",
      }}
    >
      {header && <div style={SECTION_HEADER_STYLE}>{header}</div>}
      {items.map((item) => {
        const isActive = isActiveSection && item === ACTIVE_ITEM;
        return (
          <div
            key={item}
            style={{
              ...ITEM_BASE_STYLE,
              color: isActive
                ? INK
                : isHoveredSection
                  ? INK_MUTED
                  : INK_REST,
              fontWeight: isActive ? 500 : 400,
              transition: "color 0.18s ease",
            }}
          >
            <span>{item}</span>
            {isActive && (
              <span
                style={{
                  width: 5,
                  height: 5,
                  borderRadius: "50%",
                  background: INK,
                  flexShrink: 0,
                }}
              />
            )}
          </div>
        );
      })}
    </div>
  );
};

const SideNav = () => {
  const [expanded, setExpanded] = useState(false);
  const [hoveredSection, setHoveredSection] = useState<string | null>(null);

  const handleSectionEnter = (id: string) => () => setHoveredSection(id);
  const handleSectionLeave = (id: string) => () =>
    setHoveredSection((current) => (current === id ? null : current));

  return (
    <motion.aside
      onMouseEnter={() => setExpanded(true)}
      onMouseLeave={() => {
        setExpanded(false);
        setHoveredSection(null);
      }}
      animate={{ width: expanded ? EXPANDED_WIDTH : COLLAPSED_WIDTH }}
      transition={TRANSITION}
      style={{
        position: "fixed",
        left: 0,
        top: 56,
        bottom: 0,
        zIndex: 5,
        boxSizing: "border-box",
        display: "flex",
        flexDirection: "row",
        alignItems: "stretch",
        ...getGlassBgStyle(false, expanded),
        backdropFilter: GLASS_BLUR,
        WebkitBackdropFilter: GLASS_BLUR,
        boxShadow: buildBoxShadow(false, expanded),
        transition: GLASS_TRANSITION,
        overflow: "hidden",
        color: INK,
      }}
    >
      <div
        style={{
          width: RAIL_WIDTH,
          flexShrink: 0,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          padding: "12px 0",
        }}
      >
        <IconButton
          section={BRAND_SECTION}
          isHoveredSection={hoveredSection === BRAND_SECTION.id}
          isActiveSection={false}
          onMouseEnter={handleSectionEnter(BRAND_SECTION.id)}
          onMouseLeave={handleSectionLeave(BRAND_SECTION.id)}
        />
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
              onMouseEnter={handleSectionEnter(section.id)}
              onMouseLeave={handleSectionLeave(section.id)}
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
              onMouseEnter={handleSectionEnter(section.id)}
              onMouseLeave={handleSectionLeave(section.id)}
            />
          ))}
        </div>
      </div>

      <motion.div
        animate={{ opacity: expanded ? 1 : 0 }}
        transition={
          expanded
            ? { duration: 0.25, delay: 0.18 }
            : { duration: 0.12 }
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
        <div style={{ height: ICON_BUTTON_SIZE }} />
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
              isActiveSection={section.id === ACTIVE_SECTION_ID}
              onMouseEnter={handleSectionEnter(section.id)}
              onMouseLeave={handleSectionLeave(section.id)}
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
              isActiveSection={false}
              onMouseEnter={handleSectionEnter(section.id)}
              onMouseLeave={handleSectionLeave(section.id)}
            />
          ))}
        </div>
      </motion.div>
    </motion.aside>
  );
};

export default SideNav;
