import type { RadarChartDataPoint } from "fidesui";
import { Alert, Card, Flex, RadarChart, Statistic, Tag } from "fidesui";
import { useCallback, useMemo } from "react";

import { useGetDashboardPostureQuery } from "~/features/dashboard/dashboard.slice";

import cardStyles from "./dashboard-card.module.scss";
import { BAND_CONFIG, BAND_STATUS } from "./posture-constants";
import { PostureBreakdownContent } from "./PostureBreakdownContent";
import styles from "./PostureCard.module.scss";
import { useCountUp } from "./useCountUp";
import { openDashboardDrawer } from "./useDashboardDrawer";
import { setDimensionFilter } from "./useDimensionFilter";

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

  const animatedScore = useCountUp(postureScore);

  const openPostureDrawer = useCallback(() => {
    openDashboardDrawer({
      title: "Posture breakdown",
      content: <PostureBreakdownContent posture={posture} />,
    });
  }, [posture]);

  const radarData = useMemo(
    () =>
      posture?.dimensions.map((dimension) => ({
        subject: dimension.label,
        value: dimension.score,
        status: BAND_STATUS[dimension.band],
      })),
    [posture?.dimensions],
  );

  const handleDimensionClick = useCallback(
    (index: number) => {
      const dim = posture?.dimensions[index];
      if (dim) {
        setDimensionFilter(dim.dimension);
      }
    },
    [posture?.dimensions],
  );

  const renderTooltip = useCallback(
    (point: RadarChartDataPoint) => {
      const dim = posture?.dimensions.find((d) => d.label === point.subject);
      const band = dim ? BAND_CONFIG[dim.band] : undefined;
      return (
        <Flex
          vertical
          gap={2}
          className="rounded px-3 py-2 text-xs"
          style={{
            backgroundColor: "var(--ant-color-bg-elevated)",
            boxShadow: "var(--ant-box-shadow)",
          }}
        >
          <span className="font-semibold">{point.subject}</span>
          <Flex align="center" gap={6}>
            <span>{point.value} / 100</span>
            {band && (
              <Tag color={band.color} className="!mr-0 !text-xs">
                {band.label}
              </Tag>
            )}
          </Flex>
        </Flex>
      );
    },
    [posture?.dimensions],
  );

  return (
    <Card title="Posture" variant="borderless" className={styles.cardContainer}>
      <Flex align="baseline" gap="middle">
        <div
          role="button"
          tabIndex={0}
          className={styles.clickableScore}
          onClick={openPostureDrawer}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              openPostureDrawer();
            }
          }}
        >
          <Statistic value={animatedScore} />
        </div>
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
      </Flex>
      <div className={styles.radarChartWrapper}>
        <div className={styles.radarChartInner}>
          <RadarChart
            data={radarData}
            outerRadius="80%"
            onDimensionClick={handleDimensionClick}
            tooltipContent={renderTooltip}
          />
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
