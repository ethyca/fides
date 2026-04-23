import { Card, Flex, Text } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import { useRouter } from "next/router";

import { DATA_PURPOSES_ROUTE } from "~/features/common/nav/routes";

import type { DataPurpose, PurposeSummary } from "./data-purpose.slice";
import { computeCategoryDrift } from "./purposeUtils";

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

const RISK_VARIANTS: Record<
  "drift" | "compliant" | "unknown",
  (riskCount: number) => {
    dotColor: string;
    label: string;
    textProps: React.ComponentProps<typeof Text>;
  }
> = {
  drift: (riskCount) => ({
    dotColor: palette.FIDESUI_ERROR,
    label: `${riskCount} ${riskCount === 1 ? "Risk" : "Risks"}`,
    textProps: { style: { color: palette.FIDESUI_MINOS } },
  }),
  compliant: () => ({
    dotColor: palette.FIDESUI_SUCCESS,
    label: "Compliant",
    textProps: { style: { color: palette.FIDESUI_MINOS } },
  }),
  unknown: () => ({
    dotColor: "#d9d9d9",
    label: "Not scanned",
    textProps: { type: "secondary" },
  }),
};

const RiskIndicator = ({
  status,
  riskCount,
}: {
  status: "drift" | "compliant" | "unknown";
  riskCount: number;
}) => {
  const { dotColor, label, textProps } = RISK_VARIANTS[status](riskCount);
  return (
    <Flex align="center" gap={5}>
      <Dot color={dotColor} />
      <Text {...textProps} className="text-xs">
        {label}
      </Text>
    </Flex>
  );
};

interface PurposeCardProps {
  purpose: DataPurpose;
  summary: PurposeSummary | undefined;
}

const getRelativeTime = (dateStr: string | undefined): string => {
  if (!dateStr) {
    return "";
  }
  const now = new Date();
  const date = new Date(dateStr);
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays === 0) {
    return "Updated today";
  }
  if (diffDays === 1) {
    return "Updated yesterday";
  }
  if (diffDays < 7) {
    return `Updated ${diffDays} days ago`;
  }
  if (diffDays < 30) {
    return `Updated ${Math.floor(diffDays / 7)} weeks ago`;
  }
  return `Updated ${Math.floor(diffDays / 30)} months ago`;
};

const PurposeCard = ({ purpose, summary }: PurposeCardProps) => {
  const router = useRouter();
  const drift = computeCategoryDrift(
    purpose.data_categories ?? [],
    summary?.detected_data_categories ?? [],
  );

  return (
    <Card
      size="small"
      hoverable
      className="h-full cursor-pointer bg-gray-50 transition-shadow"
      onClick={() => router.push(`${DATA_PURPOSES_ROUTE}/${purpose.fides_key}`)}
    >
      <Flex vertical gap={8} className="h-full">
        <Text strong>{purpose.name}</Text>
        <Text type="secondary" className="line-clamp-2 text-xs">
          {purpose.description}
        </Text>
        <RiskIndicator
          status={drift.status}
          riskCount={drift.undeclared.length}
        />
        <div className="mt-auto">
          <Text type="secondary" className="text-xs">
            {summary?.system_count ?? 0} data consumers &middot;{" "}
            {(purpose.data_categories ?? []).length} categories
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
