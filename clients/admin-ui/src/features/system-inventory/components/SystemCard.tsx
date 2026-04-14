import classNames from "classnames";
import { Avatar, Card, Divider, Flex, Progress, Text } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import { useRouter } from "next/router";

import { getBrandIconUrl } from "~/features/common/utils";

import { SEVERITY_COLORS, SEVERITY_LABELS } from "../constants";
import type { MockSystem, SystemRisk } from "../types";
import { formatFreshness } from "../utils";
import HealthBadge from "./HealthBadge";
import styles from "./SystemCard.module.scss";

interface SystemCardProps {
  system: MockSystem;
  accentBorder?: boolean;
  expanded?: boolean;
}

const ANNOTATION_COLOR = palette.FIDESUI_NEUTRAL_500;

const RiskRow = ({ risk }: { risk: SystemRisk }) => (
  <Flex align="center" gap={6} className="min-w-0">
    <div
      aria-label={`Severity ${SEVERITY_LABELS[risk.severity]}`}
      className="size-2 shrink-0 rounded-full"
      style={{ backgroundColor: SEVERITY_COLORS[risk.severity] }}
    />
    <Text className="min-w-0 flex-1 truncate text-xs">{risk.title}</Text>
    <Text type="secondary" className="shrink-0 text-[10px]">
      {formatFreshness(risk.detectedAt)}
    </Text>
  </Flex>
);

const SystemCard = ({ system, accentBorder, expanded }: SystemCardProps) => {
  const router = useRouter();
  const totalRisks = system.risk_count;
  const hasRisks = totalRisks > 0;

  return (
    <Card
      size="small"
      style={{
        cursor: "pointer",
        height: "100%",
        backgroundColor: palette.FIDESUI_CORINTH,
      }}
      className={classNames(
        "transition-shadow hover:shadow-[0_2px_6px_rgba(0,0,0,0.08)]",
        {
          [styles.accentError]: accentBorder && totalRisks >= 3,
          [styles.accentWarning]:
            accentBorder && totalRisks > 0 && totalRisks < 3,
        },
      )}
      onClick={() => router.push(`/system-inventory/${system.fides_key}`)}
    >
      <Flex vertical gap={4} className="h-full">
        {/* Header: name + health badge */}
        <Flex justify="space-between" align="flex-start">
          <Flex align="center" gap={6}>
            <Avatar
              size={24}
              shape="square"
              src={
                system.logoUrl ??
                (system.logoDomain
                  ? getBrandIconUrl(system.logoDomain, 48)
                  : undefined)
              }
              style={
                !system.logoDomain && !system.logoUrl
                  ? {
                      backgroundColor: palette.FIDESUI_NEUTRAL_100,
                      color: palette.FIDESUI_NEUTRAL_800,
                      fontSize: 10,
                    }
                  : undefined
              }
            >
              {!system.logoDomain && !system.logoUrl
                ? system.name.slice(0, 2).toUpperCase()
                : null}
            </Avatar>
            <Text strong>{system.name}</Text>
          </Flex>
          <HealthBadge
            health={system.health}
            count={hasRisks ? totalRisks : undefined}
          />
        </Flex>

        {/* Risks block — animated expand/collapse */}
        <div
          className={classNames(styles.expandWrapper, {
            [styles.expandWrapperOpen]: expanded,
          })}
        >
          <div className={styles.expandInner}>
            <Flex vertical gap={4} className="min-w-0">
              {hasRisks ? (
                system.risks.map((risk) => (
                  <RiskRow key={risk.id} risk={risk} />
                ))
              ) : (
                <Flex align="center" gap={6}>
                  <div
                    className="size-2 shrink-0 rounded-full"
                    style={{ backgroundColor: palette.FIDESUI_SUCCESS }}
                  />
                  <Text
                    className="text-xs"
                    style={{ color: palette.FIDESUI_SUCCESS_TEXT }}
                  >
                    No risks detected
                  </Text>
                </Flex>
              )}
            </Flex>
          </div>
        </div>

        {/* Bottom section */}
        <div className="mt-auto">
          <Divider className="!my-2" />
          <Flex justify="space-between" align="center">
            <Flex align="center" gap={6}>
              <Progress
                type="circle"
                percent={system.annotation_percent}
                size={20}
                strokeColor={ANNOTATION_COLOR}
                strokeWidth={14}
                format={() => null}
              />
              <Text type="secondary" className="text-xs">
                {system.annotation_percent}% annotated
              </Text>
            </Flex>
            {system.stewards.length > 0 ? (
              <Flex gap={-8}>
                {system.stewards.map((st) => (
                  <Avatar
                    key={st.initials}
                    size="small"
                    style={{
                      backgroundColor: palette.FIDESUI_NEUTRAL_100,
                      color: palette.FIDESUI_NEUTRAL_800,
                      fontSize: 10,
                      border: `2px solid ${palette.FIDESUI_FULL_WHITE}`,
                    }}
                  >
                    {st.initials}
                  </Avatar>
                ))}
              </Flex>
            ) : (
              <Text type="secondary" className="text-xs">
                No steward
              </Text>
            )}
          </Flex>
        </div>
      </Flex>
    </Card>
  );
};

export default SystemCard;
