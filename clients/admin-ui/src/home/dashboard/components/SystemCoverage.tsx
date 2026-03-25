import { Card, Flex, Progress, Typography } from "fidesui";
import { theme } from "antd/lib";

import type { SystemCoverageData } from "../types";

const { Text } = Typography;

interface SystemCoverageProps {
  data: SystemCoverageData;
}

const SystemCoverage = ({ data }: SystemCoverageProps) => {
  const { token } = theme.useToken();

  return (
    <Card className="rounded-lg h-full" styles={{ body: { padding: "18px 24px" } }}>
      <Flex align="center" justify="space-between" className="mb-4">
        <Text
          className="text-[10px] tracking-[0.1em]"
          type="secondary"
          strong
        >
          SYSTEM COVERAGE
        </Text>
        <Text type="secondary" className="text-[11px]">
          + Connect more systems
        </Text>
      </Flex>

      <Flex align="start" gap={20}>
        {/* Donut */}
        <Flex vertical align="center" gap={4} className="shrink-0">
          <Progress
            type="circle"
            percent={data.percent}
            size={90}
            strokeWidth={8}
            strokeColor={token.colorSuccess}
            strokeLinecap="square"
            format={(pct) => (
              <span className="text-[16px] font-bold" style={{ fontFamily: token.fontFamilyCode }}>{pct}%</span>
            )}
          />
        </Flex>

        {/* Classification breakdown */}
        <Flex vertical gap={2} className="shrink-0">
          <Text strong className="text-[13px] mb-1" style={{ fontFamily: token.fontFamilyCode }}>
            {data.total} systems
          </Text>
          {data.breakdown.map((item) => (
            <Flex key={item.label} align="center" gap={8}>
              <svg width="8" height="8" viewBox="0 0 8 8" className="shrink-0">
                <circle cx="4" cy="4" r="4" fill={item.color} />
              </svg>
              <Text className="text-[11px]">
                {item.value} {item.label}
              </Text>
            </Flex>
          ))}
        </Flex>

        {/* Connected monitors */}
        <Flex
          vertical
          gap={3}
          className="flex-1 pl-4"
          style={{ borderLeft: `1px solid ${token.colorBorder}` }}
        >
          <Text
            className="text-[10px] tracking-[0.1em] mb-1"
            type="secondary"
            strong
          >
            MONITORS
          </Text>
          {data.monitors.map((m) => {
            const pct = m.systems > 0 ? Math.round((m.classified / m.systems) * 100) : 0;
            return (
              <Flex key={m.name} align="center" justify="space-between" gap={8}>
                <Text className="text-[11px]">{m.name}</Text>
                <Flex align="center" gap={6}>
                  <Text type="secondary" className="text-[10px] whitespace-nowrap" style={{ fontFamily: token.fontFamilyCode }}>
                    {m.classified}/{m.systems}
                  </Text>
                  <div
                    className="w-[36px] h-[4px] rounded-sm overflow-hidden"
                    style={{ backgroundColor: token.colorFillSecondary }}
                  >
                    <div
                      className="h-full rounded-sm"
                      style={{
                        width: `${pct}%`,
                        backgroundColor: pct === 100 ? token.colorSuccess : token.colorWarning,
                      }}
                    />
                  </div>
                </Flex>
              </Flex>
            );
          })}
        </Flex>
      </Flex>
    </Card>
  );
};

export default SystemCoverage;
