import { Card, Flex, Text } from "fidesui";
import { Fragment, useMemo } from "react";
import { theme as antTheme } from "antd/lib";

import type { ConsumerRequestSummary } from "../types";

interface DataConsumersCardProps {
  data: ConsumerRequestSummary[];
  activeCount: number;
  loading?: boolean;
}

export const DataConsumersCard = ({
  data,
  activeCount,
  loading,
}: DataConsumersCardProps) => {
  const { token } = antTheme.useToken();
  const items = useMemo(() => data.slice(0, 5), [data]);

  return (
    <Card loading={loading} title={<Text strong>Data consumers</Text>}>
      <Flex vertical gap={8}>
        <div
          className="grid gap-y-2"
          style={{
            gridTemplateColumns: "1fr auto auto",
            columnGap: token.marginMD,
          }}
        >
          <Text type="secondary" style={{ fontSize: token.fontSizeSM }}>
            Consumer
          </Text>
          <Text
            type="secondary"
            style={{ fontSize: token.fontSizeSM, textAlign: "right" }}
          >
            Reqs
          </Text>
          <Text
            type="secondary"
            style={{ fontSize: token.fontSizeSM, textAlign: "right" }}
          >
            Viol
          </Text>

          {items.map((item) => (
            <Fragment key={item.name}>
              <Text>{item.name}</Text>
              <Text style={{ textAlign: "right" }}>
                {item.requests.toLocaleString()}
              </Text>
              <Text
                strong
                style={{
                  textAlign: "right",
                  color:
                    item.violations > 0 ? token.colorError : token.colorSuccess,
                }}
              >
                {item.violations.toLocaleString()}
              </Text>
            </Fragment>
          ))}
        </div>
      </Flex>
    </Card>
  );
};
