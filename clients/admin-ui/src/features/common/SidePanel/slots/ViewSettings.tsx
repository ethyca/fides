import { Collapse } from "fidesui";
import React from "react";

import styles from "../SidePanel.module.scss";

interface ViewSettingsProps {
  children: React.ReactNode;
  defaultOpen?: boolean;
}

const ViewSettings: React.FC<ViewSettingsProps> & { slotOrder: number } = ({
  children,
  defaultOpen = false,
}) => (
  <div className={styles.viewSettings}>
    <Collapse
      defaultActiveKey={defaultOpen ? ["viewSettings"] : []}
      ghost
      items={[
        {
          key: "viewSettings",
          label: "View settings",
          children,
        },
      ]}
    />
  </div>
);
ViewSettings.slotOrder = 5;

export default ViewSettings;
