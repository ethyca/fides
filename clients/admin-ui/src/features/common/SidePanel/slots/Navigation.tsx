import { Menu } from "fidesui";
import React from "react";

import styles from "../SidePanel.module.scss";

interface NavigationItem {
  key: string;
  label: string;
  disabled?: boolean;
  hidden?: boolean;
  type?: "group";
  children?: Array<{ key: string; label: string; disabled?: boolean }>;
}

interface NavigationProps {
  items: NavigationItem[];
  activeKey: string;
  onSelect: (key: string) => void;
}

const Navigation: React.FC<NavigationProps> & { slotOrder: number } = ({
  items,
  activeKey,
  onSelect,
}) => {
  const menuItems = items
    .filter((item) => !item.hidden)
    .map((item) => {
      if (item.type === "group" && item.children) {
        return {
          key: item.key,
          label: item.label,
          type: "group" as const,
          children: item.children.map((child) => ({
            key: child.key,
            label: child.label,
            disabled: child.disabled,
          })),
        };
      }
      return {
        key: item.key,
        label: item.label,
        disabled: item.disabled,
      };
    });

  return (
    <div className={styles.navigation}>
      <Menu
        mode="inline"
        selectedKeys={[activeKey]}
        onClick={({ key }) => onSelect(key)}
        items={menuItems}
        className={styles.navigationMenu}
      />
    </div>
  );
};
Navigation.slotOrder = 1;

export default Navigation;
