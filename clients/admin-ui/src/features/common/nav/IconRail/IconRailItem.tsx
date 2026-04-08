import React from "react";

import styles from "./IconRail.module.scss";

interface IconRailItemProps {
  icon: React.ReactNode;
  title: string;
  isActive: boolean;
  onClick: () => void;
  onMouseEnter?: () => void;
  className?: string;
}

const IconRailItem: React.FC<IconRailItemProps> = ({
  icon,
  title,
  isActive,
  onClick,
  onMouseEnter,
  className,
}) => (
  <button
    type="button"
    className={`${styles.iconItem} ${isActive ? styles.iconItemActive : ""} ${className ?? ""}`}
    onClick={onClick}
    onMouseEnter={onMouseEnter}
    aria-label={title}
    title={title}
  >
    {icon}
  </button>
);

export default IconRailItem;
