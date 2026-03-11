import classNames from "classnames";
import { Card, Divider, Flex, Skeleton, Typography } from "fidesui";

import type { AstralisResponse } from "~/features/dashboard/dashboard.slice";

import styles from "./AstralisCard.module.scss";
import cardStyles from "./dashboard-card.module.scss";

interface AstralisCardProps {
  astralis: AstralisResponse | undefined;
}

const AstralisCard = ({ astralis }: AstralisCardProps) => (
  <Card
    variant="borderless"
    className={classNames("overflow-clip h-full", cardStyles.dashboardCard)}
    showTitleDivider={false}
    title="Astralis"
  >
    {astralis ? (
      <Flex vertical gap={0}>
        {(
          [
            ["PIA active", astralis.active_conversations],
            ["Auto-approvals", astralis.completed_assessments],
            ["Risks found", astralis.risks_identified],
          ] as const
        ).map(([label, value]) => (
          <Flex
            key={label}
            justify="space-between"
            align="center"
            className={styles.statRow}
          >
            <Typography.Text>{label}</Typography.Text>
            <Typography.Text strong className={styles.statValue}>
              {value}
            </Typography.Text>
          </Flex>
        ))}
        <Divider className={styles.astralisDivider} />
        <Flex vertical align="center" className={styles.autonomyBox}>
          <Typography.Text type="secondary" className={styles.autonomyLabel}>
            AUTONOMY
          </Typography.Text>
          <Typography.Text strong className={styles.autonomyValue}>
            {astralis.active_conversations + astralis.awaiting_response > 0
              ? Math.round(
                  (astralis.completed_assessments /
                    (astralis.completed_assessments +
                      astralis.awaiting_response)) *
                    100,
                )
              : 0}
            <span className={styles.autonomyPercent}>%</span>
          </Typography.Text>
          <Typography.Text
            type="secondary"
            className={styles.autonomySubtitle}
          >
            of actions this month
          </Typography.Text>
        </Flex>
      </Flex>
    ) : (
      <Skeleton active />
    )}
  </Card>
);

export default AstralisCard;
