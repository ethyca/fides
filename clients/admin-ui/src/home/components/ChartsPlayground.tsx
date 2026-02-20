import { Flex, Typography } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";

import Sparkline from "./Sparkline";

const { Text } = Typography;

const privacyRequestsData = [
  { value: 12 },
  { value: 18 },
  { value: 15 },
  { value: 22 },
  { value: 28 },
  { value: 25 },
  { value: 34 },
  { value: 30 },
  { value: 38 },
  { value: 42 },
  { value: 39 },
  { value: 47 },
];

const systemsManagedData = [
  { value: 5 },
  { value: 8 },
  { value: 7 },
  { value: 11 },
  { value: 14 },
  { value: 13 },
  { value: 16 },
  { value: 20 },
  { value: 18 },
  { value: 23 },
  { value: 22 },
  { value: 26 },
  { value: 29 },
];

const consentPreferencesData = [
  { value: 320 },
  { value: 380 },
  { value: 350 },
  { value: 420 },
  { value: 410 },
  { value: 460 },
  { value: 500 },
  { value: 480 },
  { value: 530 },
  { value: 570 },
  { value: 550 },
  { value: 610 },
  { value: 640 },
  { value: 680 },
];

interface SparklineCardProps {
  label: string;
  value: string;
  data: { value: number }[];
  color: string;
  width: number;
  chartHeight: number;
}

const SparklineCard = ({
  label,
  value,
  data,
  color,
  width,
  chartHeight,
}: SparklineCardProps) => (
  <div
    style={{
      width,
      border: `1px solid ${palette.FIDESUI_NEUTRAL_100}`,
      borderRadius: 8,
      padding: 16,
    }}
  >
    <Flex vertical gap="small">
      <Text type="secondary" style={{ fontSize: 12 }}>
        {label}
      </Text>
      <Text strong style={{ fontSize: 22 }}>
        {value}
      </Text>
      <div style={{ height: chartHeight }}>
        <Sparkline data={data} color={color} />
      </div>
    </Flex>
  </div>
);

export const ChartsPlayground = () => {
  return (
    <Flex gap="middle" wrap="wrap" style={{ padding: 16 }}>
      <SparklineCard
        label="Privacy Requests"
        value="47"
        data={privacyRequestsData}
        color={palette.FIDESUI_TERRACOTTA}
        width={200}
        chartHeight={40}
      />
      <SparklineCard
        label="Systems Managed"
        value="29"
        data={systemsManagedData}
        color={palette.FIDESUI_OLIVE}
        width={280}
        chartHeight={60}
      />
      <SparklineCard
        label="Consent Preferences"
        value="680"
        data={consentPreferencesData}
        color={palette.FIDESUI_MINOS}
        width={320}
        chartHeight={50}
      />
    </Flex>
  );
};
