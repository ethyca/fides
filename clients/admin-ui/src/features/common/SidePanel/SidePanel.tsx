import { Drawer, Layout } from "fidesui";
import React from "react";

import { useSidePanelSlots } from "./hooks/useSidePanelSlots";
import Actions from "./slots/Actions";
import Filters from "./slots/Filters";
import Identity from "./slots/Identity";
import Navigation from "./slots/Navigation";
import SavedViews from "./slots/SavedViews";
import Search from "./slots/Search";
import ViewSettings from "./slots/ViewSettings";
import { useSidePanelContext } from "./SidePanelContext";
import styles from "./SidePanel.module.scss";

const { Sider } = Layout;

const PANEL_WIDTH = 220;

interface SidePanelProps {
  children: React.ReactNode;
}

const SidePanelComponent: React.FC<SidePanelProps> = ({ children }) => {
  const { collapsed, toggleCollapsed, isOverlay } = useSidePanelContext();
  const sortedChildren = useSidePanelSlots(children);

  if (!sortedChildren.length) {
    return null;
  }

  if (isOverlay && !collapsed) {
    return (
      <Drawer
        open
        onClose={toggleCollapsed}
        placement="left"
        width={PANEL_WIDTH}
        styles={{ body: { padding: 0 } }}
        closable={false}
      >
        <div className={styles.panelContent}>{sortedChildren}</div>
      </Drawer>
    );
  }

  if (collapsed) {
    return null;
  }

  return (
    <Sider width={PANEL_WIDTH} theme="light" className={styles.panel}>
      <div className={styles.panelContent}>{sortedChildren}</div>
    </Sider>
  );
};

const SidePanel = SidePanelComponent as React.FC<SidePanelProps> & {
  Identity: typeof Identity;
  Navigation: typeof Navigation;
  Search: typeof Search;
  Actions: typeof Actions;
  Filters: typeof Filters;
  ViewSettings: typeof ViewSettings;
  SavedViews: typeof SavedViews;
};

SidePanel.Identity = Identity;
SidePanel.Navigation = Navigation;
SidePanel.Search = Search;
SidePanel.Actions = Actions;
SidePanel.Filters = Filters;
SidePanel.ViewSettings = ViewSettings;
SidePanel.SavedViews = SavedViews;

export default SidePanel;
