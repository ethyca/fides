import { Badge, Collapse, Typography } from "fidesui";
import React from "react";

import styles from "../SidePanel.module.scss";

const { Text } = Typography;

interface FiltersProps {
  activeCount?: number;
  onClearAll?: () => void;
  children: React.ReactNode;
  defaultOpen?: boolean;
}

const Filters: React.FC<FiltersProps> & { slotOrder: number } = ({
  activeCount = 0,
  onClearAll,
  children,
  defaultOpen = true,
}) => (
  <div className={styles.filters}>
    <Collapse
      defaultActiveKey={defaultOpen ? ["filters"] : []}
      ghost
      items={[
        {
          key: "filters",
          label: (
            <div className={styles.filterHeader}>
              <span>
                Filters{" "}
                {activeCount > 0 && (
                  <Badge count={activeCount} size="small" />
                )}
              </span>
              {activeCount > 0 && onClearAll && (
                <Text
                  type="secondary"
                  className={styles.clearAll}
                  onClick={(e) => {
                    e.stopPropagation();
                    onClearAll();
                  }}
                >
                  Clear all
                </Text>
              )}
            </div>
          ),
          children: <div className={styles.filterContent}>{children}</div>,
        },
      ]}
    />
  </div>
);
Filters.slotOrder = 4;

export default Filters;
