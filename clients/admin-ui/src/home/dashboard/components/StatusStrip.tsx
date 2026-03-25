import { Card, Flex, Progress, Typography } from "fidesui";
import { theme } from "antd/lib";
import type { ReactNode } from "react";

import type { SummaryData } from "../types";

const { Text } = Typography;

const Divider = () => {
  const { token } = theme.useToken();
  return (
    <div
      className="w-px h-5 shrink-0"
      style={{ backgroundColor: token.colorBorder }}
    />
  );
};

interface StatItemProps {
  value: number | string;
  label: string;
  color?: string;
}

const StatItem = ({ value, label, color }: StatItemProps) => {
  const { token } = theme.useToken();
  return (
    <Flex align="center" gap={4}>
      <Text strong className="text-[13px]" style={{ fontFamily: token.fontFamilyCode, ...(color ? { color } : {}) }}>
        {value}
      </Text>
      <Text type="secondary" className="text-[11px]">
        {label}
      </Text>
    </Flex>
  );
};

interface StatusStripProps {
  data: SummaryData;
  inlineAlert?: string;
  trailing?: ReactNode;
}

const StatusStrip = ({ data, inlineAlert, trailing }: StatusStripProps) => {
  const { token } = theme.useToken();
  const trendColor = data.trend >= 0 ? token.colorSuccess : token.colorError;
  const trendSign = data.trend >= 0 ? "+" : "";

  return (
    <Card className="rounded-lg" styles={{ body: { padding: "12px 24px" } }}>
      <Flex align="center" justify="space-between">
        <Flex align="center" gap={16}>
          <Flex align="center" gap={8}>
            <Progress
              type="circle"
              percent={data.score}
              size={32}
              strokeWidth={10}
              strokeColor={token.colorSuccess}
              strokeLinecap="square"
              format={() => (
                <span className="text-[11px] font-bold" style={{ fontFamily: token.fontFamilyCode }}>{data.score}</span>
              )}
            />
            <Text
              className="text-[11px] font-semibold"
              style={{ color: trendColor, fontFamily: token.fontFamilyCode }}
            >
              {trendSign}
              {data.trend}
            </Text>
          </Flex>
          <Divider />
          <StatItem value={data.dsrsPending} label="DSRs pending" />
          <Divider />
          <StatItem
            value={data.dsrsOverdue}
            label={inlineAlert ?? "overdue"}
            color={data.dsrsOverdue > 0 ? token.colorError : undefined}
          />
          <Divider />
          <StatItem value={data.systemsCount} label="systems" />
          <Divider />
          <StatItem value={data.violations} label="violations" />
        </Flex>
        {trailing}
      </Flex>
    </Card>
  );
};

export default StatusStrip;
