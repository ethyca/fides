import type { RadarChartDataPoint } from "fidesui";
import {
  Alert,
  antTheme,
  Flex,
  Icons,
  RadarChart,
  Skeleton,
  SparkleIcon,
  Statistic,
  Tag,
  Text,
} from "fidesui";
import { useCallback, useMemo } from "react";

import { BAND_CONFIG, BAND_STATUS } from "~/features/dashboard/constants";
import { useGetDashboardPostureQuery } from "~/features/dashboard/dashboard.slice";
import { DiffDirection } from "~/features/dashboard/types";

import styles from "./PostureCard.module.scss";
import { useCountUp } from "./useCountUp";
import { openDashboardDrawer } from "./useDashboardDrawer";

function getDiffPrefix(direction: DiffDirection): React.ReactNode | undefined {
  if (direction === DiffDirection.UNCHANGED) {
    return undefined;
  }
  if (direction === DiffDirection.DOWN) {
    return <Icons.ArrowDown size={12} />;
  }
  return <Icons.ArrowUp size={12} />;
}

export const PostureScore = ({ children }: { children?: React.ReactNode }) => {
  const { token } = antTheme.useToken();
  const { data: posture, isLoading } = useGetDashboardPostureQuery();
  const postureScore = posture?.score ?? 0;
  const postureDiff = posture?.diff_percent ?? 0;
  const diffDirection = posture?.diff_direction ?? DiffDirection.UNCHANGED;


  const animatedScore = useCountUp(postureScore);

  const openPostureDrawer = useCallback(() => {
    openDashboardDrawer({ type: "posture" });
  }, []);

  if (isLoading) {
    return <Skeleton active paragraph={{ rows: 6 }} />;
  }

  return (
    <Flex vertical>
      <Text
        type="secondary"
        className={styles.sectionLabel}
        style={{ fontFamily: token.fontFamilyCode }}
      >
        Governance Posture
      </Text>

      <div
        role="button"
        tabIndex={0}
        aria-label="View posture breakdown"
        className={styles.heroScore}
        onClick={openPostureDrawer}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            openPostureDrawer();
          }
        }}
      >
        <Statistic
          value={animatedScore}
          valueStyle={{
            fontSize: 96,
            fontWeight: 200,
            lineHeight: 0.95,
            letterSpacing: "-3px",
          }}
          suffix={<span className={styles.heroScoreSuffix}>/100</span>}
        />
      </div>

      <Flex align="center" gap={8} className="mb-2 mt-3">
        {diffDirection !== DiffDirection.UNCHANGED && (
          <Tag
            color={diffDirection === DiffDirection.UP ? "success" : "error"}
            className={styles.trendPill}
          >
            {getDiffPrefix(diffDirection)} {postureDiff} pts
          </Tag>
        )}
        <Text type="secondary" className="text-[13px]">
          from last period
        </Text>
      </Flex>

      {posture?.agent_annotation && (
        <Alert
          type="info"
          showIcon
          icon={
            <SparkleIcon
              size={12}
              style={{ color: "var(--fidesui-terracotta)" }}
            />
          }
          message={posture.agent_annotation}
          className="mt-4"
        />
      )}

      {children}
    </Flex>
  );
};

export const PostureRadar = () => {
  const { data: posture, isLoading } = useGetDashboardPostureQuery();

  const radarData = useMemo(
    () =>
      posture?.dimensions.map((dimension) => ({
        subject: dimension.label,
        value: dimension.score,
        status: BAND_STATUS[dimension.band],
      })),
    [posture?.dimensions],
  );

  const handleDimensionClick = useCallback(() => {
    openDashboardDrawer({ type: "posture" });
  }, []);

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

  if (isLoading) {
    return <Skeleton active paragraph={{ rows: 8 }} />;
  }

  return (
    <Flex vertical align="center" justify="center" className="h-full">
      <div className={styles.radarChartContainer}>
        <RadarChart
          data={radarData}
          outerRadius="80%"
          onDimensionClick={handleDimensionClick}
          tooltipContent={renderTooltip}
        />
      </div>
      <Text type="secondary" className="mt-1 text-xs">
        Click a dimension to explore breakdown
      </Text>
    </Flex>
  );
};

/** @deprecated Use PostureScore and PostureRadar instead */
export const PostureCard = PostureScore;
