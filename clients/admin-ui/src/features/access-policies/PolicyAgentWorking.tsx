import { Flex, Typography } from "fidesui";

import styles from "./PolicyAgentWorking.module.scss";

interface PolicyAgentWorkingProps {
  size?: "default" | "small";
}

const PolicyAgentWorking = ({ size = "default" }: PolicyAgentWorkingProps) => (
  <Flex
    align="center"
    gap="small"
    role="status"
    className={`${styles.container} ${size === "small" ? styles.small : ""}`}
    data-testid="policy-agent-working"
  >
    <span className={styles.square} aria-hidden />
    <Typography.Text type="secondary">Policy agent is working</Typography.Text>
  </Flex>
);

export default PolicyAgentWorking;
