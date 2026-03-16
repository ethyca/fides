import type { RadarChartDataPoint } from "fidesui";
import { Alert, Card, Flex, RadarChart, Spin, Statistic, Tag } from "fidesui";
import { useCallback, useMemo } from "react";

import { BAND_CONFIG, BAND_STATUS } from "~/features/dashboard/constants";
import { useGetDashboardPostureQuery } from "~/features/dashboard/dashboard.slice";
import { DiffDirection } from "~/features/dashboard/types";

import cardStyles from "./dashboard-card.module.scss";
import { PostureBreakdownContent } from "./PostureBreakdownContent";
import styles from "./PostureCard.module.scss";
import { useCountUp } from "./useCountUp";
import { openDashboardDrawer } from "./useDashboardDrawer";
import { setDimensionFilter } from "./useDimensionFilter";

function getDiffPrefix(direction: DiffDirection): string | undefined {
  if (direction === DiffDirection.UNCHANGED) {
    return undefined;
  }
  if (direction === DiffDirection.DOWN) {
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
  const { data: posture, isLoading } = useGetDashboardPostureQuery();
  const postureScore = posture?.score ?? 0;
  const postureDiff = posture?.diff_percent ?? 0;
  const diffDirection = posture?.diff_direction ?? DiffDirection.UNCHANGED;

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
        <Flex vertical gap={2} className={styles.radarTooltip}>
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
    <Spin spinning={isLoading}>
      <Card
        title="Posture"
        variant="borderless"
        className={styles.cardContainer}
      >
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
              diffDirection === DiffDirection.UNCHANGED
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
    </Spin>
  );
};
