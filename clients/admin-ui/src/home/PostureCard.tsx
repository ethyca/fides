import type { RadarChartDataPoint } from "fidesui";
import {
  Alert,
  Card,
  Flex,
  Icons,
  RadarChart,
  SparkleIcon,
  Statistic,
  Tag,
} from "fidesui";
import { useCallback, useMemo } from "react";

import { BAND_CONFIG, BAND_STATUS } from "~/features/dashboard/constants";
import { useGetDashboardPostureQuery } from "~/features/dashboard/dashboard.slice";
import { DiffDirection } from "~/features/dashboard/types";

import styles from "./PostureCard.module.scss";
import { useCountUp } from "./useCountUp";
import { openDashboardDrawer } from "./useDashboardDrawer";
import { setDimensionFilter } from "./useDimensionFilter";

function getDiffPrefix(direction: DiffDirection): React.ReactNode | undefined {
  if (direction === DiffDirection.UNCHANGED) {
    return undefined;
  }
  if (direction === DiffDirection.DOWN) {
    return <Icons.ArrowDown size={12} />;
  }
  return <Icons.ArrowUp size={12} />;
}



export const PostureCard = () => {
  const { data: posture, isLoading } = useGetDashboardPostureQuery();
  const postureScore = posture?.score ?? 0;
  const postureDiff = posture?.diff_percent ?? 0;
  const diffDirection = posture?.diff_direction ?? DiffDirection.UNCHANGED;

  const animatedScore = useCountUp(postureScore);

  const openPostureDrawer = useCallback(() => {
    openDashboardDrawer({ type: "posture" });
  }, []);

  const radarData = useMemo(() => {
    if (!posture?.dimensions) {
      return undefined;
    }
    const maxWeight = Math.max(...posture.dimensions.map((d) => d.weight));
    return posture.dimensions.map((dimension) => ({
      subject: dimension.label,
      value: dimension.score,
      weight: maxWeight > 0 ? (dimension.weight / maxWeight) * 100 : 0,
      status: BAND_STATUS[dimension.band],
    }));
  }, [posture?.dimensions]);

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
          {dim && (
            <span className="text-xs opacity-65">
              {Math.round(dim.weight * 100)}% weight
            </span>
          )}
        </Flex>
      );
    },
    [posture?.dimensions],
  );

  return (
    <Card
      title="Posture"
      variant="borderless"
      loading={isLoading}
      className={styles.cardContainer}
    >
      <Flex align="baseline" gap="small" className={styles.scoreOverlay}>
        <div
          role="button"
          tabIndex={0}
          aria-label="View posture breakdown"
          className={styles.clickableScore}
          onClick={openPostureDrawer}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              openPostureDrawer();
            }
          }}
        >
          <Statistic value={animatedScore} valueStyle={{ fontSize: 48 }} />
        </div>
        <Statistic
          trend={
            diffDirection === DiffDirection.UNCHANGED
              ? "neutral"
              : (diffDirection as "up" | "down")
          }
          value={postureDiff}
          prefix={getDiffPrefix(diffDirection)}
          size="sm"
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
          type="info"
          showIcon
          icon={<SparkleIcon size={14} />}
          message={posture.agent_annotation}
          className={styles.alertSm}
        />
      )}
    </Card>
  );
};
