import { Button, Flex, Tag, Text, Title } from "fidesui";
import NextLink from "next/link";

import {
  BAND_CONFIG,
  DIMENSION_DESCRIPTIONS,
  DIMENSION_ROUTES,
} from "~/features/dashboard/constants";
import { useGetDashboardPostureQuery } from "~/features/dashboard/dashboard.slice";

import styles from "./PostureBreakdownContent.module.scss";

export const PostureBreakdownContent = () => {
  const { data: posture } = useGetDashboardPostureQuery();

  if (!posture) {
    return null;
  }

  const overallBand = BAND_CONFIG[posture.band];

  return (
    <Flex vertical gap="large">
      <Flex align="baseline" gap={12}>
        <Title level={2} className="!mb-0">
          {posture.score}
        </Title>
        {overallBand && (
          <Tag color={overallBand.color}>{overallBand.label}</Tag>
        )}
      </Flex>

      {posture.dimensions.map((dim) => {
        const band = BAND_CONFIG[dim.band];
        const route = DIMENSION_ROUTES[dim.dimension];
        const description = DIMENSION_DESCRIPTIONS[dim.dimension];

        return (
          <div key={dim.dimension} className={styles.dimensionCard}>
            <Flex vertical gap="small">
              <Text strong>{dim.label}</Text>
              <Flex justify="space-between" align="flex-start" gap={12}>
                <Flex vertical gap="small" className="min-w-0 flex-1">
                  {description && <Text type="secondary">{description}</Text>}
                  <Flex align="center" gap="medium">
                    <Text>{dim.score} / 100</Text>
                    {band && <Tag color={band.color}>{band.label}</Tag>}
                    <Text type="secondary">
                      {Math.round(dim.weight * 100)}% weight
                    </Text>
                  </Flex>
                </Flex>
                {route && (
                  <NextLink href={route.route} passHref>
                    <Button size="small">{route.label}</Button>
                  </NextLink>
                )}
              </Flex>
            </Flex>
          </div>
        );
      })}
    </Flex>
  );
};
