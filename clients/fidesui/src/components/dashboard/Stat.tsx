import { ArrowDownOutlined, ArrowUpOutlined } from "@ant-design/icons";
import { Typography } from "antd";
import React from "react";

const { Text, Title } = Typography;

export type StatTrend = "up" | "down" | "neutral";

export interface StatProps {
  value: string | number;
  change?: string | number;
  detail?: React.ReactNode;
  trend?: StatTrend;
}

const Stat = ({ value, change, detail, trend = "neutral" }: StatProps) => {
  const changeTextType =
    trend === "up" ? "success" : trend === "down" ? "danger" : "secondary";

  const TrendIcon =
    trend === "up"
      ? ArrowUpOutlined
      : trend === "down"
        ? ArrowDownOutlined
        : null;

  return (
    <div className="flex flex-col gap-1">
      <Title level={4} className="!my-0">
        {value}
      </Title>

      {change !== undefined && (
        <div className="flex items-center gap-1">
          {TrendIcon && (
            <Text type={changeTextType}>
              <TrendIcon />
            </Text>
          )}
          <Text type={changeTextType} strong>
            {change}
          </Text>
        </div>
      )}
      {detail}
    </div>
  );
};

export default Stat;
