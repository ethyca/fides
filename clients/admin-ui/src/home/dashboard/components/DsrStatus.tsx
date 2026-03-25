import { Card, Flex, Typography } from "fidesui";
import { theme } from "antd/lib";

import type { CoverageBreakdownItem, DsrStatusData, SlaBar } from "../types";

const { Text } = Typography;

interface DsrStatusProps {
  data: DsrStatusData;
}

const StackedBar = ({ bar }: { bar: SlaBar }) => {
  const total = bar.segments.reduce((s, i) => s + i.value, 0);
  if (total === 0) return null;

  return (
    <Flex align="center" gap={8}>
      <Text type="secondary" className="text-[11px] w-[60px] shrink-0">
        {bar.label}
      </Text>
      <Flex className="h-2 flex-1 rounded-sm overflow-hidden">
        {bar.segments.map((seg) => (
          <div
            key={seg.label}
            style={{
              flex: seg.value,
              backgroundColor: seg.color,
            }}
          />
        ))}
      </Flex>
    </Flex>
  );
};

const Legend = ({ items }: { items: CoverageBreakdownItem[] }) => (
  <Flex gap={12}>
    {items.map((item) => (
      <Flex key={item.label} align="center" gap={4}>
        <svg width="6" height="6" viewBox="0 0 6 6">
          <circle cx="3" cy="3" r="3" fill={item.color} />
        </svg>
        <Text type="secondary" className="text-[10px]">
          {item.label}
        </Text>
      </Flex>
    ))}
  </Flex>
);

const DsrStatus = ({ data }: DsrStatusProps) => {
  const { token } = theme.useToken();
  return (
  <Card className="rounded-lg h-full" styles={{ body: { padding: "18px 24px" } }}>
    <Flex align="center" justify="space-between" className="mb-4">
      <Text
        className="text-[10px] tracking-[0.1em]"
        type="secondary"
        strong
      >
        DSR STATUS
      </Text>
      <Text type="secondary" className="text-[11px]">
        View all requests →
      </Text>
    </Flex>

    <Flex align="start" gap={32}>
      {/* Left: active count + breakdown */}
      <Flex vertical className="shrink-0">
        <Flex align="baseline" gap={8} className="mb-3">
          <Text className="text-[24px] font-bold leading-none" style={{ fontFamily: token.fontFamilyCode }}>
            {data.active}
          </Text>
          <Text type="secondary" className="text-[11px]">
            Active Requests
          </Text>
        </Flex>
        <Flex vertical gap={2}>
          {data.breakdown.map((item) => (
            <Flex key={item.label} align="center" gap={8}>
              <Text strong className="text-[13px]" style={{ color: item.color, fontFamily: token.fontFamilyCode }}>
                {item.value}
              </Text>
              <Text className="text-[11px]">{item.label}</Text>
            </Flex>
          ))}
        </Flex>
      </Flex>

      {/* Right: SLA health bars */}
      <Flex vertical gap={8} className="flex-1 min-w-0">
        <Text
          className="text-[10px] tracking-[0.1em]"
          type="secondary"
          strong
        >
          SLA HEALTH
        </Text>
        {data.slaBars.map((bar) => (
          <StackedBar key={bar.label} bar={bar} />
        ))}
        <div className="mt-1">
          <Legend items={data.slaLegend} />
        </div>
      </Flex>
    </Flex>
  </Card>
  );
};

export default DsrStatus;
