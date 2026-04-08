import { Avatar, Card, Divider, Flex, Progress, Tag, Text } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import { useRouter } from "next/router";

import { getBrandIconUrl } from "~/features/common/utils";

import type { MockSystem } from "../types";
import HealthBadge from "./HealthBadge";

interface SystemCardProps {
  system: MockSystem;
}

const getAnnotationColor = (pct: number): string => {
  if (pct >= 75) {
    return palette.FIDESUI_SUCCESS;
  }
  if (pct >= 40) {
    return palette.FIDESUI_WARNING;
  }
  return palette.FIDESUI_ERROR;
};

const SystemCard = ({ system }: SystemCardProps) => {
  const router = useRouter();

  const totalIssues = system.issue_count;
  return (
    <Card
      size="small"
      style={{
        cursor: "pointer",
        height: "100%",
        backgroundColor: palette.FIDESUI_CORINTH,
      }}
      className="transition-shadow hover:shadow-[0_2px_6px_rgba(0,0,0,0.08)]"
      onClick={() => router.push(`/system-inventory/${system.fides_key}`)}
    >
      <Flex vertical gap={8} className="h-full">
        {/* Header: name + role icons + health */}
        <Flex justify="space-between" align="flex-start">
          <Flex align="center" gap={8}>
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
                      backgroundColor: "#e6e6e8",
                      color: "#53575c",
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
            count={totalIssues > 0 ? totalIssues : undefined}
          />
        </Flex>

        {/* Purpose tags */}
        <Flex gap={4} className="flex-nowrap overflow-hidden">
          {system.purposes.length > 0 ? (
            <>
              {system.purposes.slice(0, 4).map((p) => (
                <Tag
                  key={p.name}
                  bordered={false}
                  className="shrink-0 text-xs"
                  style={{ backgroundColor: palette.FIDESUI_NEUTRAL_100 }}
                >
                  {p.name}
                </Tag>
              ))}
              {system.purposes.length > 4 && (
                <Tag
                  bordered={false}
                  className="shrink-0 text-xs"
                  style={{ backgroundColor: palette.FIDESUI_NEUTRAL_100 }}
                >
                  +{system.purposes.length - 4} more
                </Tag>
              )}
            </>
          ) : (
            <Text type="secondary" className="text-xs">
              No purpose defined
            </Text>
          )}
        </Flex>

        {/* Bottom section */}
        <div className="mt-auto">
          <Divider className="!my-2" />
          <Flex justify="space-between" align="center">
            <Flex align="center" gap={6}>
              <Progress
                type="circle"
                percent={system.annotation_percent}
                size={20}
                strokeColor={getAnnotationColor(system.annotation_percent)}
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
                      backgroundColor: "#e6e6e8",
                      color: "#53575c",
                      fontSize: 10,
                      border: "2px solid white",
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
