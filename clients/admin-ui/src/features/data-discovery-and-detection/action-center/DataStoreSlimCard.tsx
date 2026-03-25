import { Card, Flex, Progress, Statistic, Tag, Typography } from "fidesui";
import { useMemo } from "react";

import { nFormatter } from "~/features/common/utils";

import { FAKE_DATA_CATEGORIES, computePercent } from "./dashboardFakeData";
import { MonitorAggregatedResults } from "./types";

const { Text } = Typography;

export type SlimCardVariant = "A" | "B" | "C";

interface DataStoreSlimCardProps {
  monitors: MonitorAggregatedResults[];
  variant?: SlimCardVariant;
}

const OVERALL = { totalDiscovered: 52_853, approved: 34_000 };

const useSlimCardData = (monitors: MonitorAggregatedResults[]) => {
  const hasData = monitors.length > 0;
  const percent =
    OVERALL.totalDiscovered > 0
      ? Math.round((OVERALL.approved / OVERALL.totalDiscovered) * 100)
      : 0;

  const items = useMemo(() => {
    if (!hasData) return [];
    let unlabeled = 0;
    let classifying = 0;
    let classified = 0;
    let reviewed = 0;
    for (const m of monitors) {
      const u = m.updates as {
        unlabeled?: number;
        classifying?: number;
        in_review?: number;
        reviewed?: number;
      };
      unlabeled += u.unlabeled ?? 0;
      classifying += u.classifying ?? 0;
      classified += u.in_review ?? 0;
      reviewed += u.reviewed ?? 0;
    }
    return [
      { label: "unlabeled", value: unlabeled },
      { label: "classifying", value: classifying },
      { label: "classified", value: classified },
      { label: "reviewed", value: reviewed },
    ].filter((s) => s.value > 0);
  }, [monitors, hasData]);

  const tagTotal = FAKE_DATA_CATEGORIES.reduce((s, d) => s + d.value, 0);

  return { hasData, percent, items, tagTotal };
};

// ── Shared right-hand sections ──

const StatusSection = ({
  items,
}: {
  items: { label: string; value: number }[];
}) => (
  <div className="shrink-0">
    <Text
      className="text-[10px] tracking-[0.1em] mb-1 block"
      type="secondary"
      strong
    >
      CURRENT STATUS
    </Text>
    <Text className="text-[11px]" type="secondary">
      {items
        .map((item) => `${nFormatter(item.value)} ${item.label}`)
        .join(" · ")}
    </Text>
  </div>
);

const CategoriesSection = ({ tagTotal }: { tagTotal: number }) => (
  <div className="min-w-0 flex-1">
    <Text
      className="text-[10px] tracking-[0.1em] mb-1 block"
      type="secondary"
      strong
    >
      DATA CATEGORIES
    </Text>
    <Flex gap={4} wrap="wrap">
      {FAKE_DATA_CATEGORIES.map((item) => (
        <Tag key={item.label} className="text-[11px]">
          {item.label} {computePercent(item.value, tagTotal)}%
        </Tag>
      ))}
    </Flex>
  </div>
);

const Divider = () => (
  <div className="w-px h-8 bg-neutral-200 shrink-0" />
);

// ── Variant A: Ant Statistic component with suffix ──

const VariantA = ({
  percent,
  items,
  tagTotal,
}: {
  percent: number;
  items: { label: string; value: number }[];
  tagTotal: number;
}) => (
  <Card className="rounded-lg" styles={{ body: { padding: "10px 20px" } }}>
    <Flex align="center" gap={32}>
      <Flex align="baseline" gap={12} className="shrink-0">
        <Statistic
          value={percent}
          suffix="%"
          title={
            <Text
              className="text-[10px] tracking-[0.1em]"
              type="secondary"
              strong
            >
              RESOURCES APPROVED
            </Text>
          }
          valueStyle={{ fontSize: 24, fontWeight: 700, lineHeight: 1 }}
        />
        <Text type="secondary" className="text-[11px] whitespace-nowrap">
          {nFormatter(OVERALL.approved, 1)} of{" "}
          {nFormatter(OVERALL.totalDiscovered, 1)}
        </Text>
      </Flex>
      <Divider />
      <StatusSection items={items} />
      <Divider />
      <CategoriesSection tagTotal={tagTotal} />
    </Flex>
  </Card>
);

// ── Variant B: Mini donut + bold text ──

const VariantB = ({
  percent,
  items,
  tagTotal,
}: {
  percent: number;
  items: { label: string; value: number }[];
  tagTotal: number;
}) => (
  <Card className="rounded-lg" styles={{ body: { padding: "10px 20px" } }}>
    <Flex align="center" gap={32}>
      <Flex align="center" gap={12} className="shrink-0">
        <Progress
          type="circle"
          percent={percent}
          size={40}
          strokeWidth={10}
          strokeColor="#5a9a68"
          format={(pct) => (
            <span className="text-[11px] font-bold">{pct}%</span>
          )}
        />
        <div>
          <Text
            className="text-[10px] tracking-[0.1em] block"
            type="secondary"
            strong
          >
            RESOURCES APPROVED
          </Text>
          <Text className="text-[13px] font-semibold">
            {nFormatter(OVERALL.approved, 1)}
          </Text>
          <Text type="secondary" className="text-[11px]">
            {" "}
            of {nFormatter(OVERALL.totalDiscovered, 1)}
          </Text>
        </div>
      </Flex>
      <Divider />
      <StatusSection items={items} />
      <Divider />
      <CategoriesSection tagTotal={tagTotal} />
    </Flex>
  </Card>
);

// ── Variant C: Stacked large number + sub-label ──

const VariantC = ({
  percent,
  items,
  tagTotal,
}: {
  percent: number;
  items: { label: string; value: number }[];
  tagTotal: number;
}) => (
  <Card className="rounded-lg" styles={{ body: { padding: "10px 20px" } }}>
    <Flex align="center" gap={32}>
      <div className="shrink-0">
        <Text
          className="text-[10px] tracking-[0.1em] block"
          type="secondary"
          strong
        >
          RESOURCES APPROVED
        </Text>
        <Flex align="baseline" gap={6}>
          <Text className="text-xl font-bold" style={{ color: "#5a9a68" }}>
            {percent}%
          </Text>
          <Text type="secondary" className="text-[11px]">
            · {nFormatter(OVERALL.approved, 1)} /{" "}
            {nFormatter(OVERALL.totalDiscovered, 1)}
          </Text>
        </Flex>
      </div>
      <Divider />
      <StatusSection items={items} />
      <Divider />
      <CategoriesSection tagTotal={tagTotal} />
    </Flex>
  </Card>
);

// ── Main export ──

const DataStoreSlimCard = ({
  monitors,
  variant = "A",
}: DataStoreSlimCardProps) => {
  const { hasData, percent, items, tagTotal } = useSlimCardData(monitors);

  if (!hasData) {
    return null;
  }

  const props = { percent, items, tagTotal };

  if (variant === "B") return <VariantB {...props} />;
  if (variant === "C") return <VariantC {...props} />;
  return <VariantA {...props} />;
};

export default DataStoreSlimCard;
