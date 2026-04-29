import { Card, Flex, Text } from "fidesui";
import { useRouter } from "next/router";

import { useRelativeTime } from "~/features/common/hooks/useRelativeTime";
import { DATA_PURPOSES_ROUTE } from "~/features/common/nav/routes";

import type { DataPurpose, PurposeSummary } from "./data-purpose.slice";
import { computeCategoryDrift } from "./purposeUtils";

const Dot = ({ className }: { className: string }) => (
  <span
    className={`inline-block size-[7px] shrink-0 rounded-full ${className}`}
  />
);

const RISK_VARIANTS: Record<
  "drift" | "compliant" | "unknown",
  (riskCount: number) => {
    dotClass: string;
    label: string;
    textProps: React.ComponentProps<typeof Text>;
  }
> = {
  drift: (riskCount) => ({
    dotClass: "bg-[var(--ant-color-error)]",
    label: `${riskCount} ${riskCount === 1 ? "Risk" : "Risks"}`,
    textProps: { className: "!text-[var(--fidesui-minos)]" },
  }),
  compliant: () => ({
    dotClass: "bg-[var(--ant-color-success)]",
    label: "Compliant",
    textProps: { className: "!text-[var(--fidesui-minos)]" },
  }),
  unknown: () => ({
    dotClass: "bg-neutral-3",
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
  const { dotClass, label, textProps } = RISK_VARIANTS[status](riskCount);
  return (
    <Flex align="center" gap={5}>
      <Dot className={dotClass} />
      <Text {...textProps} className={`text-xs ${textProps.className ?? ""}`}>
        {label}
      </Text>
    </Flex>
  );
};

interface PurposeCardProps {
  purpose: DataPurpose;
  summary: PurposeSummary | undefined;
}

const PurposeCard = ({ purpose, summary }: PurposeCardProps) => {
  const router = useRouter();
  const drift = computeCategoryDrift(
    purpose.data_categories ?? [],
    summary?.detected_data_categories ?? [],
  );
  const updatedAt = purpose.updated_at ? new Date(purpose.updated_at) : null;
  const updatedAgo = useRelativeTime(updatedAt);

  return (
    <Card
      size="small"
      hoverable
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
            {updatedAgo && `Updated ${updatedAgo}`}
          </Text>
        </div>
      </Flex>
    </Card>
  );
};

export default PurposeCard;
