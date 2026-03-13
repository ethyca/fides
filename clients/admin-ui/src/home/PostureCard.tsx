import classNames from "classnames";
import { Alert, Card, RadarChart, Statistic } from "fidesui";

import { useGetDashboardPostureQuery } from "~/features/dashboard/dashboard.slice";

import cardStyles from "./dashboard-card.module.scss";
import styles from "./PostureCard.module.scss";

const BAND_STATUS: Record<string, "warning" | "error" | undefined> = {
  at_risk: "warning",
  critical: "error",
};

function getDiffPrefix(direction: string): string | undefined {
  if (direction === "unchanged") {
    return undefined;
  }
  if (direction === "down") {
    return "↓";
  }
  return "↑";
}

function getPostureAlertType(score: number): "error" | "warning" | "success" {
  if (score < 40) {
    return "error";
  }
  if (score < 80) {
    return "warning";
  }
  return "success";
}

export const PostureCard = () => {
  const { data: posture } = useGetDashboardPostureQuery();
  const postureScore = posture?.score ?? 0;
  const postureDiff = posture?.diff_percent ?? 0;
  const diffDirection = posture?.diff_direction ?? "unchanged";

  const radarData = posture?.dimensions.map((dimension) => ({
    subject: dimension.label,
    value: dimension.score,
    status: BAND_STATUS[dimension.band],
  }));

  return (
    <Card
      title="Posture"
      variant="borderless"
      className={classNames(cardStyles.dashboardCard, styles.cardContainer)}
    >
      <Statistic value={postureScore} />
      <Statistic
        trend={
          diffDirection === "unchanged"
            ? "neutral"
            : (diffDirection as "up" | "down")
        }
        value={postureDiff}
        prefix={getDiffPrefix(diffDirection)}
        className={cardStyles.smallStatistic}
      />
      <div className={styles.radarChartWrapper}>
        <div className={styles.radarChartInner}>
          <RadarChart data={radarData} outerRadius="80%" />
        </div>
      </div>
      {posture?.agent_annotation && (
        <Alert
          type={getPostureAlertType(postureScore)}
          message={posture.agent_annotation}
          className={styles.alertSm}
        />
      )}
    </Card>
  );
};
