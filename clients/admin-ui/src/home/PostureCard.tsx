import type { RadarChartDataPoint, RadarPointStatus } from "fidesui";
import {
  Alert,
  Card,
  ConfigProvider,
  Flex,
  Icons,
  RadarChart,
  Tag,
  Text,
  Tooltip,
  useThemeMode,
} from "fidesui";
import { useCallback, useMemo } from "react";

import {
  BAND_CONFIG,
  BAND_STATUS,
  DIMENSION_DESCRIPTIONS,
  DIMENSION_LABELS,
} from "~/features/dashboard/constants";
import { useGetDashboardPostureQuery } from "~/features/dashboard/dashboard.slice";

import styles from "./PostureCard.module.scss";
import { useCountUp } from "./useCountUp";
import { openDashboardDrawer } from "./useDashboardDrawer";
import { setDimensionFilter } from "./useDimensionFilter";

export const PostureCard = () => {
  const { data: posture, isLoading } = useGetDashboardPostureQuery();
  const { resolvedMode } = useThemeMode();
  const postureScore = posture?.score ?? 0;

  const animatedScore = useCountUp(postureScore);

  const alertTheme = useMemo(
    () => ({
      components: {
        Alert: {
          colorInfoBg:
            resolvedMode === "dark"
              ? "var(--fidesui-bg-minos)"
              : "var(--fidesui-limestone)",
          colorInfoBorder:
            resolvedMode === "dark"
              ? "var(--fidesui-minos)"
              : "var(--fidesui-limestone)",
        },
      },
    }),
    [resolvedMode],
  );

  const openPostureDrawer = useCallback(() => {
    openDashboardDrawer({ type: "posture" });
  }, []);

  const radarData = useMemo(
    () =>
      posture?.dimensions.map((dimension) => ({
        subject: DIMENSION_LABELS[dimension.dimension] ?? dimension.label,
        value: Math.round(dimension.score),
        status: BAND_STATUS[dimension.band],
        tag: {
          label: `${Math.round(dimension.score)} / 100`,
          status: (BAND_STATUS[dimension.band] ??
            "success") as RadarPointStatus,
        },
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
      const dim = posture?.dimensions.find(
        (d) => (DIMENSION_LABELS[d.dimension] ?? d.label) === point.subject,
      );
      const description = dim
        ? DIMENSION_DESCRIPTIONS[dim.dimension]
        : undefined;
      if (!description) {
        return null;
      }
      return <span className="max-w-[200px] text-xs">{description}</span>;
    },
    [posture?.dimensions],
  );

  return (
    <Card
      title={
        <Tooltip
          title="A composite score (0–100) measuring your organization's data governance health across coverage, classification, consent, DSR compliance, and more. Higher is better."
          placement="bottom"
        >
          <Flex
            align="center"
            gap={4}
            style={{ cursor: "pointer", display: "inline-flex" }}
          >
            <Text>Governance Posture Score</Text>
            <Icons.Help size={14} className="opacity-30" />
          </Flex>
        </Tooltip>
      }
      variant="borderless"
      loading={isLoading}
      className={styles.cardContainer}
    >
      <ConfigProvider theme={alertTheme}>
        <div
          role="button"
          tabIndex={0}
          className={styles.clickableAlert}
          onClick={openPostureDrawer}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              openPostureDrawer();
            }
          }}
        >
          <Alert
            type="info"
            showIcon={false}
            className={styles.summaryAlert}
            title={
              <Flex align="center" gap="middle">
                <div>
                  <Flex vertical>
                    <span className={styles.scoreValue}>
                      {animatedScore}
                      <span className={styles.scoreDenominator}>/100</span>
                    </span>
                    {posture?.band && (
                      <Tag
                        color={BAND_CONFIG[posture.band].color}
                        className="mt-1 w-fit"
                      >
                        {BAND_CONFIG[posture.band].label}
                      </Tag>
                    )}
                  </Flex>
                </div>
                {posture?.agent_annotation && (
                  <span className={styles.summaryText}>
                    {posture.agent_annotation}{" "}
                    <span className={styles.viewDetailsCta}>
                      View details <Icons.ArrowRight size={12} />
                    </span>
                  </span>
                )}
              </Flex>
            }
          />
        </div>
      </ConfigProvider>
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
    </Card>
  );
};
