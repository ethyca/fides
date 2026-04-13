import {
  Alert,
  antTheme,
  Flex,
  Icons,
  Progress,
  SparkleIcon,
  Tag,
  Text,
} from "fidesui";
import NextLink from "next/link";

import {
  BAND_CONFIG,
  DIMENSION_DESCRIPTIONS,
  DIMENSION_LABELS,
  DIMENSION_ROUTES,
} from "~/features/dashboard/constants";
import { useGetDashboardPostureQuery } from "~/features/dashboard/dashboard.slice";
import type { PostureBand } from "~/features/dashboard/types";

import styles from "./PostureBreakdownContent.module.scss";

export const PostureBreakdownContent = () => {
  const { data: posture } = useGetDashboardPostureQuery();
  const { token } = antTheme.useToken();

  if (!posture) {
    return null;
  }

  const overallBand = BAND_CONFIG[posture.band];

  const bandColorMap: Record<string, string> = {
    success: token.colorSuccess,
    caution: token.colorWarning,
    error: token.colorError,
    info: token.colorInfo,
  };

  const getBandColor = (band: PostureBand) =>
    bandColorMap[BAND_CONFIG[band].color] ?? token.colorPrimary;

  return (
    <Flex vertical gap={12}>
      <Flex vertical gap="small">
        <Flex align="baseline" gap={8}>
          <Text className={styles.scoreValue}>
            {Math.round(posture.score)}
            <Text className={styles.scoreDenominator}>/100</Text>
          </Text>
          {overallBand && (
            <Tag color={overallBand.color}>{overallBand.label}</Tag>
          )}
        </Flex>
        <Text type="secondary" className="text-xs">
          The Governance Posture Score is a composite metric (0–100) that
          measures your organization&apos;s data governance health across
          coverage, classification, consent, DSR compliance, and more. Each
          dimension is weighted based on its impact to your overall privacy
          program.
        </Text>
      </Flex>

      {posture.agent_annotation && (
        <Alert
          type="info"
          showIcon
          icon={<SparkleIcon size={14} />}
          message={posture.agent_annotation}
        />
      )}

      {posture.dimensions.map((dim) => {
        const band = BAND_CONFIG[dim.band];
        const route = DIMENSION_ROUTES[dim.dimension];
        const description = DIMENSION_DESCRIPTIONS[dim.dimension];
        const progressColor = getBandColor(dim.band);

        const card = (
          <div key={dim.dimension} className={styles.dimensionCard}>
            <Flex align="center" gap={8}>
              <Flex vertical gap={4} className="min-w-0 flex-1">
                <Flex align="center" gap={6}>
                  <Text strong>
                    {DIMENSION_LABELS[dim.dimension] ?? dim.label}
                  </Text>
                  {band && <Tag color={band.color}>{band.label}</Tag>}
                </Flex>
                {description && (
                  <Text type="secondary" className="text-xs">
                    {description}
                  </Text>
                )}
                <Flex align="center" gap="small">
                  <Text className={styles.dimScore}>
                    {Math.round(dim.score)} / 100
                  </Text>
                  <Text type="secondary" className="text-xs">
                    {Math.round(dim.weight * 100)}% weight
                  </Text>
                </Flex>
                <Progress
                  percent={dim.score}
                  showInfo={false}
                  size="small"
                  strokeColor={progressColor}
                />
              </Flex>
              {route && (
                <Icons.Launch size={14} className={styles.launchIcon} />
              )}
            </Flex>
          </div>
        );

        if (route) {
          return (
            <NextLink
              key={dim.dimension}
              href={route.route}
              className={styles.dimensionLink}
            >
              {card}
            </NextLink>
          );
        }
        return card;
      })}
    </Flex>
  );
};
