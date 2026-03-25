import { Card, Flex, Typography } from "fidesui";
import { theme } from "antd/lib";

import type { AlertData } from "../types";

const { Text } = Typography;

interface AlertBannerProps {
  data: AlertData;
}

const AlertBanner = ({ data }: AlertBannerProps) => {
  const { token } = theme.useToken();

  return (
    <Card
      className="rounded-lg"
      styles={{
        body: {
          padding: "12px 24px",
          backgroundColor: token.colorWarningBg,
          borderRadius: 8,
        },
      }}
    >
      <Flex align="center" justify="space-between">
        <Flex align="center" gap={8}>
          <svg width="8" height="8" viewBox="0 0 8 8">
            <circle cx="4" cy="4" r="4" fill={token.colorWarning} />
          </svg>
          <Text className="text-[13px]">{data.message}</Text>
        </Flex>
        <Flex gap={4}>
          {data.actions.map((action, i) => (
            <span key={action.label}>
              {i > 0 && (
                <Text type="secondary" className="text-[11px] mx-1">
                  ·
                </Text>
              )}
              <Text className="text-[11px] cursor-pointer" style={{ color: token.colorWarning }}>
                {action.label}
              </Text>
            </span>
          ))}
        </Flex>
      </Flex>
    </Card>
  );
};

export default AlertBanner;
