import classNames from "classnames";
import { formatDistanceStrict } from "date-fns";
import { Card, Empty, Flex, Skeleton, Typography } from "fidesui";

import { SparkleIcon } from "~/features/common/Icon/SparkleIcon";
import type { ActivityFeedItem } from "~/features/dashboard/dashboard.slice";

import styles from "./ActivityFeedCard.module.scss";
import cardStyles from "./dashboard-card.module.scss";

interface ActivityFeedCardProps {
  activityFeed:
    | {
        items: ActivityFeedItem[];
      }
    | undefined;
}

function formatRelativeTime(timestamp: string): string {
  return formatDistanceStrict(new Date(timestamp), new Date())
    .replace(/ seconds?/, "s")
    .replace(/ minutes?/, "m")
    .replace(/ hours?/, "h")
    .replace(/ days?/, "d")
    .replace(/ months?/, "mo")
    .replace(/ years?/, "y");
}

const ActivityFeedCard = ({ activityFeed }: ActivityFeedCardProps) => (
  <Card
    variant="borderless"
    title="Activity"
    className={classNames("overflow-clip h-full", cardStyles.dashboardCard)}
    showTitleDivider={false}
  >
    {activityFeed?.items ? (
      <Flex vertical gap={0} className={styles.activityList}>
        {activityFeed.items.map((item) => {
          const isAgent = item.actor_type === "agent";
          const relativeTime = formatRelativeTime(item.timestamp);

          return (
            <Flex
              key={`${item.timestamp}-${item.actor_type}`}
              align="center"
              gap={12}
              className={classNames(styles.activityRow, {
                [styles.activityRowAgent]: isAgent,
              })}
            >
              {isAgent ? (
                <SparkleIcon className={styles.sparkleIcon} />
              ) : (
                <span className={styles.activityDot} />
              )}
              <Typography.Text className={styles.activityMessage}>
                <Typography.Text
                  strong
                  className={isAgent ? styles.actorAgent : undefined}
                >
                  {isAgent ? "Astralis" : "User"}
                </Typography.Text>{" "}
                {item.message}
              </Typography.Text>
              <Typography.Text type="secondary" className={styles.relativeTime}>
                {relativeTime}
              </Typography.Text>
            </Flex>
          );
        })}
        {activityFeed.items.length === 0 && (
          <Empty description="No recent activity" />
        )}
      </Flex>
    ) : (
      <Skeleton active />
    )}
  </Card>
);

export default ActivityFeedCard;
