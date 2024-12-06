import { AntMenu } from "fidesui";
import { ComponentProps } from "react";

import styles from "./FloatingMenu.module.scss";

type AntMenuProps = ComponentProps<typeof AntMenu>;

export const FloatingMenu = ({ className, ...props }: AntMenuProps) => (
  <AntMenu
    mode="vertical"
    {...props}
    className={`${styles.menu} ${className}`}
    style={{ width: 220 }}
  />
);
