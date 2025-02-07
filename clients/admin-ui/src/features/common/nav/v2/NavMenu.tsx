import { AntMenu as Menu } from "fidesui";
import { ComponentProps } from "react";

import styles from "./NavMenu.module.scss";

type MenuProps = ComponentProps<typeof Menu>;

export const NavMenu = ({ className, ...props }: MenuProps) => (
  <Menu
    mode="inline"
    theme="dark"
    inlineIndent={16}
    {...props}
    className={`${styles.menu} ${className}`}
  />
);
