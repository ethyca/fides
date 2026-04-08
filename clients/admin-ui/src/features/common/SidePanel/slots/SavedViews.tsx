import { Collapse } from "fidesui";
import React from "react";

import styles from "../SidePanel.module.scss";

interface SavedViewsProps {
  children: React.ReactNode;
  defaultOpen?: boolean;
}

const SavedViews: React.FC<SavedViewsProps> & { slotOrder: number } = ({
  children,
  defaultOpen = false,
}) => (
  <div className={styles.savedViews}>
    <Collapse
      defaultActiveKey={defaultOpen ? ["savedViews"] : []}
      ghost
      items={[
        {
          key: "savedViews",
          label: "Saved views",
          children,
        },
      ]}
    />
  </div>
);
SavedViews.slotOrder = 6;

export default SavedViews;
