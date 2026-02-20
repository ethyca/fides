import { CUSTOM_TAG_COLOR, Tag } from "fidesui";
import type { ComponentProps } from "react";

import styles from "./CitationBadge.module.scss";

interface CitationBadgeProps
  extends Omit<ComponentProps<typeof Tag>, "children"> {
  number: number;
}

export const CitationBadge = ({ number, ...props }: CitationBadgeProps) => (
  <Tag color={CUSTOM_TAG_COLOR.INFO} className={styles.badge} {...props}>
    {number}
  </Tag>
);
