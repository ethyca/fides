import { ArrowDownOutlined, ArrowUpOutlined } from "@ant-design/icons";
import classNames from "classnames";
import { Alert, Card, Statistic } from "fidesui";
import { RadarChart } from "fidesui";

import type { PostureResponse } from "~/features/dashboard/dashboard.slice";

import cardStyles from "./dashboard-card.module.scss";
import styles from "./PostureCard.module.scss";

const BAND_STATUS: Record<string, "warning" | "error" | undefined> = {
  at_risk: "warning",
  critical: "error",
};

function getPostureAlertType(score: number): "error" | "warning" | "success" {
  if (score < 40) return "error";
  if (score < 80) return "warning";
  return "success";
}

interface PostureCardProps {
  posture: PostureResponse | undefined;
}

const PostureCard = ({ posture }: PostureCardProps) => {
  const postureScore = posture?.score ?? 0;
  const postureDiff = posture?.diff_percent ?? 0;
  const diffDirection = posture?.diff_direction ?? "unchanged";

  const radarData = posture?.dimensions.map((d) => ({
    subject: d.label,
    value: d.score,
    status: BAND_STATUS[d.band],
  }));

  return (
    <Card
      title="Posture"
      variant="borderless"
      className={classNames("h-full", cardStyles.dashboardCard)}
      showTitleDivider={false}
    >
      <>
        <Statistic valueVariant="display" value={postureScore} />
        <Statistic
          trend={diffDirection === "unchanged" ? "neutral" : diffDirection === "down" ? "down" : "up"}
          value={postureDiff}
          prefix={
            diffDirection === "down" ? (
              <ArrowDownOutlined />
            ) : (
              <ArrowUpOutlined />
            )
          }
          className={cardStyles.smallStatistic}
        />
        <div className={classNames(styles.radarChartWrapper)}>
          <RadarChart data={radarData} outerRadius="90%" />
        </div>
        {posture?.agent_annotation && (
          <Alert
            type={getPostureAlertType(postureScore)}
            message={posture.agent_annotation}
            className={styles.alertSm}
          />
        )}
      </>
    </Card>
  );
};

export default PostureCard;
