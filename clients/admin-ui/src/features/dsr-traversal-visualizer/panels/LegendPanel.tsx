import { Card, Flex, Text } from "fidesui";

import styles from "./LegendPanel.module.scss";

const LegendPanel = () => (
  <Card size="small" className={styles.panel} data-testid="visualizer-legend">
    <Flex vertical gap={6}>
      <Text strong style={{ fontSize: 12 }}>
        Legend
      </Text>
      <div className={styles.row}>
        <span className={styles.swatch} />
        <Text type="secondary" style={{ fontSize: 11 }}>
          Integration / Identity / Manual task
        </Text>
      </div>
      <div className={styles.row}>
        <span className={styles.lineSwatch} />
        <Text type="secondary" style={{ fontSize: 11 }}>
          depends on
        </Text>
      </div>
      <div className={styles.row}>
        <span className={`${styles.lineSwatch} ${styles.lineSwatchDashed}`} />
        <Text type="secondary" style={{ fontSize: 11 }}>
          gates
        </Text>
      </div>
    </Flex>
  </Card>
);

export default LegendPanel;
