// @ts-expect-error — Storybook types are in fidesui, not admin-ui
import type { Meta, StoryObj } from "@storybook/react-vite";
import { Icons } from "fidesui";
import React, { useCallback, useRef, useState } from "react";

import styles from "./IconRail.module.scss";

// Mock nav groups matching real NAV_CONFIG structure
const MOCK_GROUPS = [
  {
    title: "Overview",
    icon: <Icons.Home />,
    children: [{ title: "Home", path: "/", exact: true, children: [] }],
  },
  {
    title: "Detection & Discovery",
    icon: <Icons.DataAnalytics />,
    children: [
      { title: "Action center", path: "/action-center", children: [] },
      { title: "Data catalog", path: "/data-catalog", children: [] },
      { title: "Access control", path: "/access-control", children: [] },
    ],
  },
  {
    title: "Data inventory",
    icon: <Icons.DataTable />,
    children: [
      { title: "Data lineage", path: "/datamap", children: [] },
      { title: "System inventory", path: "/systems", children: [] },
      { title: "Add systems", path: "/add-systems", children: [] },
      { title: "Manage datasets", path: "/dataset", children: [] },
      { title: "Data map report", path: "/reporting/datamap", children: [] },
      { title: "Asset report", path: "/reporting/assets", children: [] },
    ],
  },
  {
    title: "Privacy requests",
    icon: <Icons.MessageQueue />,
    children: [
      {
        title: "Request manager",
        path: "/privacy-requests",
        children: [],
      },
      { title: "DSR policies", path: "/policies", children: [] },
    ],
  },
  {
    title: "Consent",
    icon: <Icons.SettingsAdjust />,
    children: [
      { title: "Vendors", path: "/consent/configure", children: [] },
      { title: "Notices", path: "/consent/privacy-notices", children: [] },
      {
        title: "Experiences",
        path: "/consent/privacy-experiences",
        children: [],
      },
      {
        title: "Consent report",
        path: "/consent/reporting",
        children: [],
      },
    ],
  },
  {
    title: "Core configuration",
    icon: <Icons.WorkflowAutomation />,
    children: [
      { title: "Taxonomy", path: "/taxonomy", children: [] },
      { title: "Integrations", path: "/integrations", children: [] },
      { title: "Notifications", path: "/notifications", children: [] },
      { title: "Properties", path: "/properties", children: [] },
    ],
  },
  {
    title: "Compliance",
    icon: <Icons.RuleDraft />,
    children: [
      { title: "Locations", path: "/locations", children: [] },
      { title: "Regulations", path: "/regulations", children: [] },
    ],
  },
];

const MOCK_SETTINGS_GROUP = {
  title: "Settings",
  icon: <Icons.Settings />,
  children: [
    { title: "Users", path: "/user-management", children: [] },
    { title: "Organization", path: "/organization", children: [] },
    { title: "About Fides", path: "/about", children: [] },
  ],
};

const ACTIVE_PATH = "/systems";
const ACTIVE_GROUP = MOCK_GROUPS.find((g) => g.title === "Data inventory")!;

// Self-contained IconRail story component (avoids admin-ui store dependencies)
const IconRailStory = () => {
  const [expanded, setExpanded] = useState(false);
  const [highlightedGroup, setHighlightedGroup] = useState<string | null>(null);
  const collapseTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleMouseEnter = useCallback(() => {
    if (collapseTimerRef.current) {
      clearTimeout(collapseTimerRef.current);
      collapseTimerRef.current = null;
    }
    setExpanded(true);
  }, []);

  const handleMouseLeave = useCallback(() => {
    collapseTimerRef.current = setTimeout(() => {
      setExpanded(false);
      setHighlightedGroup(null);
    }, 150);
  }, []);

  const allGroups = [...MOCK_GROUPS, MOCK_SETTINGS_GROUP];
  const mainGroups = MOCK_GROUPS;

  const isActivePage = (path: string) => path === ACTIVE_PATH;
  const isActiveGroup = (title: string) => title === ACTIVE_GROUP.title;

  return (
    <div style={{ display: "flex", height: "100vh", background: "#f5f5f5" }}>
      <div className={styles.railWrapper}>
        <div
          className={`${styles.rail} ${expanded ? styles.railExpanded : ""}`}
          onMouseEnter={handleMouseEnter}
          onMouseLeave={handleMouseLeave}
        >
          <div
            className={`${styles.railTop} ${expanded ? styles.railExpandedTop : ""}`}
          >
            {/* Logo */}
            <div
              className={`${styles.logo} ${expanded ? styles.logoExpanded : ""}`}
            >
              <Icons.Home
                style={{ width: 24, height: 24, color: "white" }}
              />
            </div>

            {expanded ? (
              <div className={styles.expandedNav}>
                {allGroups.map((group, idx) => {
                  const isHighlighted = highlightedGroup === group.title;
                  const groupActive = isActiveGroup(group.title);

                  return (
                    <React.Fragment key={group.title}>
                      {idx === mainGroups.length && (
                        <div className={styles.separator} />
                      )}
                      <div className={styles.sectionGroup}>
                        <div
                          className={`${styles.sectionHeader} ${groupActive ? styles.sectionHeaderActive : ""} ${isHighlighted && !groupActive ? styles.sectionHeaderHighlighted : ""}`}
                        >
                          <span className={styles.sectionIcon}>
                            {group.icon}
                          </span>
                          <span className={styles.sectionTitle}>
                            {group.title}
                          </span>
                        </div>
                        <ul className={styles.subPageList}>
                          {group.children.map((child) => (
                            <li key={child.path} className={styles.subPageItem}>
                              <a
                                href="#"
                                className={`${styles.subPageLink} ${isActivePage(child.path) ? styles.subPageLinkActive : ""}`}
                                onClick={(e) => e.preventDefault()}
                              >
                                {child.title}
                              </a>
                            </li>
                          ))}
                        </ul>
                      </div>
                    </React.Fragment>
                  );
                })}
              </div>
            ) : (
              <>
                {mainGroups.map((group) => (
                  <button
                    key={group.title}
                    type="button"
                    className={`${styles.iconItem} ${isActiveGroup(group.title) ? styles.iconItemActive : ""}`}
                    onMouseEnter={() => setHighlightedGroup(group.title)}
                    title={group.title}
                  >
                    {group.icon}
                  </button>
                ))}
              </>
            )}
          </div>

          <div
            className={`${styles.railBottom} ${expanded ? styles.railExpandedBottom : ""}`}
          >
            {!expanded && (
              <button
                type="button"
                className={`${styles.iconItem} ${isActiveGroup("Settings") ? styles.iconItemActive : ""}`}
                onMouseEnter={() => setHighlightedGroup("Settings")}
                title="Settings"
              >
                <Icons.Settings />
              </button>
            )}
            <button type="button" className={styles.bottomButton} title="Help">
              <Icons.Help />
            </button>
            <button
              type="button"
              className={styles.bottomButton}
              title="Account"
            >
              <Icons.User />
            </button>
          </div>
        </div>
      </div>

      {/* Content area placeholder */}
      <div style={{ flex: 1, padding: 24, background: "#fff" }}>
        <h2 style={{ color: "#666", fontWeight: 400 }}>
          Content area — hover over the rail to expand
        </h2>
        <p style={{ color: "#999" }}>
          Active page: <strong>System inventory</strong> (Data inventory group)
        </p>
      </div>
    </div>
  );
};

const meta = {
  title: "Admin UI/IconRail",
  parameters: {
    layout: "fullscreen",
  },
} satisfies Meta;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => <IconRailStory />,
};
