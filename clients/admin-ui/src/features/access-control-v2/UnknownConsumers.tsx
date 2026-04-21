import { Button, Flex, Tag, Text, Title } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import Link from "next/link";

import { DATA_CONSUMERS_ROUTE } from "~/features/common/nav/routes";

import { MOCK_UNRESOLVED_IDENTITIES } from "../access-control/mockData";

const formatRelativeTime = (isoStr: string): string => {
  const diffMs = Date.now() - new Date(isoStr).getTime();
  const diffMins = Math.floor(diffMs / 60000);
  if (diffMins < 60) return `${diffMins}m ago`;
  const diffHrs = Math.floor(diffMins / 60);
  if (diffHrs < 24) return `${diffHrs}h ago`;
  const diffDays = Math.floor(diffHrs / 24);
  if (diffDays < 7) return `${diffDays}d ago`;
  return new Date(isoStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
};

const getRiskLevel = (
  queryCount: number,
  datasetCount: number,
): { label: string; color: string } => {
  if (queryCount > 2000 || datasetCount > 4)
    return { label: "High", color: palette.FIDESUI_ERROR };
  if (queryCount > 500 || datasetCount > 2)
    return { label: "Medium", color: palette.FIDESUI_WARNING };
  return { label: "Low", color: palette.FIDESUI_MINOS };
};

const UnknownConsumers = () => {
  const identities = MOCK_UNRESOLVED_IDENTITIES;

  if (identities.length === 0) return null;

  return (
    <Flex
      vertical
      gap={12}
      className="rounded-lg border border-solid px-5 py-4"
      style={{
        borderColor: palette.FIDESUI_NEUTRAL_100,
        backgroundColor: palette.FIDESUI_BG_DEFAULT,
      }}
    >
      <Flex justify="space-between" align="center">
        <Flex vertical>
          <Title level={5} className="!mb-0">
            Unknown consumers
          </Title>
          <Text type="secondary" className="text-xs">
            {identities.length}{" "}
            {identities.length === 1 ? "identity" : "identities"} in query logs
            not registered as a consumer. Register them to enable policy
            evaluation.
          </Text>
        </Flex>
      </Flex>

      {/* Table header */}
      <Flex
        className="border-b border-solid px-3 py-2"
        align="center"
        style={{
          backgroundColor: palette.FIDESUI_CORINTH,
          borderColor: palette.FIDESUI_NEUTRAL_100,
        }}
      >
        <Text strong className="w-[28%] text-xs">
          Identity
        </Text>
        <Text strong className="w-[24%] text-xs">
          Data accessed
        </Text>
        <Text strong className="w-[12%] text-right text-xs">
          Queries
        </Text>
        <Text strong className="w-[10%] text-xs">
          Last seen
        </Text>
        <Text strong className="w-[10%] text-xs">
          Risk
        </Text>
        <Text strong className="w-[16%] text-right text-xs">
          Actions
        </Text>
      </Flex>

      {/* Rows */}
      {identities.map((identity) => {
        const risk = getRiskLevel(
          identity.query_count,
          identity.datasets.length,
        );
        const datasetsDisplay =
          identity.datasets.length <= 2
            ? identity.datasets.join(", ")
            : `${identity.datasets.slice(0, 2).join(", ")} +${identity.datasets.length - 2} more`;

        return (
          <Flex
            key={identity.id}
            align="center"
            className="border-b border-solid px-3 py-2.5"
            style={{ borderColor: palette.FIDESUI_NEUTRAL_75 }}
          >
            <Text
              className="w-[28%] font-mono text-xs"
              ellipsis={{ tooltip: identity.identifier }}
            >
              {identity.identifier}
            </Text>
            <Text type="secondary" className="w-[24%] text-xs">
              {datasetsDisplay}
            </Text>
            <Text type="secondary" className="w-[12%] text-right text-xs">
              {identity.query_count.toLocaleString()}
            </Text>
            <Text type="secondary" className="w-[10%] text-xs">
              {formatRelativeTime(identity.last_seen)}
            </Text>
            <div className="w-[10%]">
              <Flex align="center" gap={4}>
                <div
                  className="size-1.5 rounded-full"
                  style={{ backgroundColor: risk.color }}
                />
                <Text className="text-xs">{risk.label}</Text>
              </Flex>
            </div>
            <Flex className="w-[16%]" justify="flex-end" gap={8}>
              <Link href={DATA_CONSUMERS_ROUTE}>
                <Button size="small" type="primary" className="!text-[10px]">
                  Register
                </Button>
              </Link>
              <Button size="small" className="!text-[10px]">
                Map to existing
              </Button>
            </Flex>
          </Flex>
        );
      })}
    </Flex>
  );
};

export default UnknownConsumers;
