import { Menu } from "fidesui";
import type { ComponentProps } from "react";

import styles from "./FloatingMenu.module.scss";

type MenuProps = ComponentProps<typeof Menu>;

export const FloatingMenu = ({ className, ...props }: MenuProps) => (
  <Menu
    {...props}
    className={`${styles.menu} ${className}`}
    style={{ width: 220 }}
  />
);
