import classNames from "classnames";
import { Flex } from "fidesui";

import styles from "./LegendPanel.module.scss";

export const LegendPanel = () => (
  <Flex vertical gap={4} className={styles.root} data-testid="legend-panel">
    <Flex align="center" gap="small" className={styles.dataDependency}>
      <svg className={styles.swatch} viewBox="0 0 30 8">
        <line
          x1="0"
          y1="4"
          x2="30"
          y2="4"
          stroke="currentColor"
          strokeWidth="2"
          strokeDasharray="5"
        />
      </svg>
      <span>Data dependency</span>
    </Flex>
    <Flex align="center" gap="small" className={styles.manualReview}>
      <svg className={styles.swatch} viewBox="0 0 30 8">
        <line
          x1="0"
          y1="4"
          x2="30"
          y2="4"
          stroke="currentColor"
          strokeWidth="2"
          strokeDasharray="6 4"
        />
      </svg>
      <span>Manual review gate</span>
    </Flex>
    <Flex align="center" gap="small">
      <span className={classNames(styles.cardSwatch, styles.cardInFlow)} />
      <span>In-flow system</span>
    </Flex>
    <Flex align="center" gap="small">
      <span className={classNames(styles.cardSwatch, styles.cardSkipped)} />
      <span>Not touched</span>
    </Flex>
    <Flex align="center" gap="small">
      <span className={styles.chevron}>›</span>
      <span>Process flow</span>
    </Flex>
  </Flex>
);
