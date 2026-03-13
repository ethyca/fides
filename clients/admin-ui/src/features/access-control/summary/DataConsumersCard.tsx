import { antTheme, Card, Flex, Text } from "fidesui";

import type { DataConsumerSummary } from "../types";

interface DataConsumersCardProps {
  data: DataConsumerSummary[];
  activeCount: number;
  loading?: boolean;
}

export const DataConsumersCard = ({
  data,
  activeCount,
  loading,
}: DataConsumersCardProps) => {
  const { token } = antTheme.useToken();
  const items = data.slice(0, 5);

  return (
    <Card
      loading={loading}
      title={<Text strong>Data consumers</Text>}
      extra={
        <Text type="secondary" style={{ fontSize: token.fontSizeSM }}>
          {activeCount} active
        </Text>
      }
    >
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
            <>
              <Text key={`${item.name}-name`}>{item.name}</Text>
              <Text
                key={`${item.name}-reqs`}
                style={{ textAlign: "right" }}
              >
                {item.requests.toLocaleString()}
              </Text>
              <Text
                key={`${item.name}-viol`}
                strong
                style={{
                  textAlign: "right",
                  color:
                    item.violations > 0
                      ? token.colorError
                      : token.colorSuccess,
                }}
              >
                {item.violations.toLocaleString()}
              </Text>
            </>
          ))}
        </div>
      </Flex>
    </Card>
  );
};
