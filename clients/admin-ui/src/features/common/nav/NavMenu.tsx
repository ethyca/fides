import { AntMenu as Menu, Icons } from "fidesui";
import { ComponentProps } from "react";

import styles from "./NavMenu.module.scss";

type MenuProps = ComponentProps<typeof Menu>;

export const NavMenu = ({ className, ...props }: MenuProps) => (
  <Menu
    mode="inline"
    theme="dark"
    inlineIndent={8}
    expandIcon={
      <div>
        {/* The wrapper div is required otherwise the size of the icon is ignored */}
        <Icons.ChevronDown size={14} />
      </div>
    }
    {...props}
    className={`${styles.menu} ${className}`}
  />
);
