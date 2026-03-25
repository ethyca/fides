import { Card, Flex, Typography } from "fidesui";
import { Sparkline } from "fidesui";
import { theme } from "antd/lib";

import type { SparklineCardData } from "../types";

const { Text } = Typography;

interface SparklineMetricCardProps {
  card: SparklineCardData;
  sparklineHeight?: number;
  compact?: boolean;
}

const SparklineMetricCard = ({
  card,
  sparklineHeight = 40,
  compact = false,
}: SparklineMetricCardProps) => {
  const { token } = theme.useToken();
  const trendColor =
    card.trendDirection === "up" ? token.colorSuccess : token.colorError;
  const heroSize = compact ? "text-[14px]" : "text-[18px]";
  const padding = compact ? "10px 16px" : "14px 20px";

  return (
    <Card className="rounded-lg" styles={{ body: { padding } }}>
      <Text
        className="text-[10px] tracking-[0.1em] mb-1 block uppercase"
        type="secondary"
        strong
      >
        {card.title}
      </Text>
      <Flex align="baseline" gap={6}>
        <Text className={`${heroSize} font-bold`} style={{ fontFamily: token.fontFamilyCode }}>
          {card.value}
          {card.unit}
        </Text>
        <Text
          className="text-[11px] font-semibold"
          style={{ color: trendColor, fontFamily: token.fontFamilyCode }}
        >
          {card.trend}
        </Text>
      </Flex>
      <div style={{ height: sparklineHeight }} className="mt-2">
        <Sparkline data={card.data} strokeWidth={1.2} />
      </div>
    </Card>
  );
};

export default SparklineMetricCard;
