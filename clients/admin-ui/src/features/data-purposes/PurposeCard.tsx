import classNames from "classnames";
import { Card, Flex, Text } from "fidesui";

import { useRelativeTime } from "~/features/common/hooks/useRelativeTime";
import { RouterLink } from "~/features/common/nav/RouterLink";
import { DATA_PURPOSES_ROUTE } from "~/features/common/nav/routes";

import type { DataPurpose, PurposeSummary } from "./data-purpose.slice";
import { computeCategoryDrift } from "./purposeUtils";

const Dot = ({ className }: { className: string }) => (
  <span
    className={classNames(
      "inline-block size-[7px] shrink-0 rounded-full",
      className,
    )}
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
    dotClass: "bg-[var(--fidesui-color-error)]",
    label: `${riskCount} ${riskCount === 1 ? "Risk" : "Risks"}`,
    textProps: { className: "!text-[var(--fidesui-minos)]" },
  }),
  compliant: () => ({
    dotClass: "bg-[var(--fidesui-color-success)]",
    label: "Compliant",
    textProps: { className: "!text-[var(--fidesui-minos)]" },
  }),
  unknown: () => ({
    dotClass: "bg-[var(--fidesui-neutral-300)]",
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
      <Text
        {...textProps}
        className={classNames("text-xs", textProps.className)}
      >
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
  const drift = computeCategoryDrift(
    purpose.data_categories ?? [],
    summary?.detected_data_categories ?? [],
  );
  const updatedAt = purpose.updated_at ? new Date(purpose.updated_at) : null;
  const updatedAgo = useRelativeTime(updatedAt);

  return (
    <RouterLink
      href={`${DATA_PURPOSES_ROUTE}/${purpose.fides_key}`}
      unstyled
      className="block h-full"
    >
      <Card size="small" hoverable className="h-full">
        <Flex vertical gap={8} className="h-full">
          <Text strong>{purpose.name}</Text>
          <Text type="secondary" className="line-clamp-2 text-xs">
            {purpose.description}
          </Text>
          <RiskIndicator
            status={drift.status}
            riskCount={drift.undeclared.length}
          />
          <Flex vertical gap={4} className="mt-auto">
            <Text type="secondary" className="text-xs">
              {summary?.system_count ?? 0} data consumers &middot;{" "}
              {(purpose.data_categories ?? []).length} categories
            </Text>
            <Text type="secondary" className="text-xs">
              {updatedAgo && `Updated ${updatedAgo}`}
            </Text>
          </Flex>
        </Flex>
      </Card>
    </RouterLink>
  );
};

export default PurposeCard;
