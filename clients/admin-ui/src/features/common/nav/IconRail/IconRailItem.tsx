import React from "react";

import styles from "./IconRail.module.scss";

interface IconRailItemProps {
  icon: React.ReactNode;
  title: string;
  isActive: boolean;
  onClick: () => void;
  onMouseEnter?: () => void;
}

const IconRailItem: React.FC<IconRailItemProps> = ({
  icon,
  title,
  isActive,
  onClick,
  onMouseEnter,
}) => (
  <button
    type="button"
    className={`${styles.iconItem} ${isActive ? styles.iconItemActive : ""}`}
    onClick={onClick}
    onMouseEnter={onMouseEnter}
    aria-label={title}
    title={title}
  >
    {icon}
  </button>
);

export default IconRailItem;
