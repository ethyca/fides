import { Card, Flex, Text } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import { useRouter } from "next/router";

import { DATA_PURPOSES_ROUTE } from "~/features/common/nav/routes";

import { computeCategoryDrift } from "./purposeUtils";
import type { DataPurpose, PurposeSummary } from "./types";

const Dot = ({ color }: { color: string }) => (
  <span
    style={{
      display: "inline-block",
      width: 7,
      height: 7,
      borderRadius: "50%",
      backgroundColor: color,
      flexShrink: 0,
    }}
  />
);

const RiskIndicator = ({
  status,
  riskCount,
}: {
  status: string;
  riskCount: number;
}) => {
  if (status === "drift") {
    return (
      <Flex align="center" gap={5}>
        <Dot color={palette.FIDESUI_ERROR} />
        <Text className="text-xs" style={{ color: palette.FIDESUI_MINOS }}>
          {riskCount} {riskCount === 1 ? "risk" : "risks"}
        </Text>
      </Flex>
    );
  }
  if (status === "compliant") {
    return (
      <Flex align="center" gap={5}>
        <Dot color={palette.FIDESUI_SUCCESS} />
        <Text className="text-xs" style={{ color: palette.FIDESUI_MINOS }}>
          Compliant
        </Text>
      </Flex>
    );
  }
  return (
    <Flex align="center" gap={5}>
      <Dot color="#d9d9d9" />
      <Text type="secondary" className="text-xs">
        Not scanned
      </Text>
    </Flex>
  );
};

interface PurposeCardProps {
  purpose: DataPurpose;
  summary: PurposeSummary | undefined;
}

const getRelativeTime = (dateStr: string): string => {
  const now = new Date();
  const date = new Date(dateStr);
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return "Updated today";
  if (diffDays === 1) return "Updated yesterday";
  if (diffDays < 7) return `Updated ${diffDays} days ago`;
  if (diffDays < 30) return `Updated ${Math.floor(diffDays / 7)} weeks ago`;
  return `Updated ${Math.floor(diffDays / 30)} months ago`;
};

const PurposeCard = ({ purpose, summary }: PurposeCardProps) => {
  const router = useRouter();
  const drift = computeCategoryDrift(
    purpose.data_categories,
    purpose.detected_data_categories,
  );

  return (
    <Card
      size="small"
      style={{
        backgroundColor: "#fafafa",
        cursor: "pointer",
        height: "100%",
      }}
      className="transition-shadow hover:shadow-[0_2px_6px_rgba(0,0,0,0.08)]"
      onClick={() => router.push(`${DATA_PURPOSES_ROUTE}/${purpose.id}`)}
    >
      <Flex vertical gap={8} className="h-full">
        <Text strong>{purpose.name}</Text>
        <Text type="secondary" className="line-clamp-2 text-xs">
          {purpose.description}
        </Text>
        <RiskIndicator status={drift.status} riskCount={drift.undeclared.length} />
        <div className="mt-auto">
          <Text type="secondary" className="text-xs">
            {summary?.system_count ?? 0} data consumers &middot;{" "}
            {purpose.data_categories.length} categories
          </Text>
          <br />
          <Text type="secondary" className="text-xs">
            {getRelativeTime(purpose.updated_at)}
          </Text>
        </div>
      </Flex>
    </Card>
  );
};

export default PurposeCard;
