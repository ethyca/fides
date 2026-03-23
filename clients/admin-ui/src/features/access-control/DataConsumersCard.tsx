import { Card, Text } from "fidesui";
import { Fragment, useMemo } from "react";

import type { ConsumerRequestSummary } from "./types";

interface DataConsumersCardProps {
  data: ConsumerRequestSummary[];
  activeCount: number;
  loading?: boolean;
}

export const DataConsumersCard = ({
  data,
  loading,
}: DataConsumersCardProps) => {
  const items = useMemo(() => data.slice(0, 5), [data]);

  return (
    <Card
      loading={loading}
      title={<Text strong>Data consumers</Text>}
      className="h-full"
    >
      <div className="grid grid-cols-[1fr_auto_auto] gap-x-4 gap-y-2">
        <Text type="secondary" className="text-xs">
          Consumer
        </Text>
        <Text type="secondary" className="text-right text-xs">
          Reqs
        </Text>
        <Text type="secondary" className="text-right text-xs">
          Viol
        </Text>

        {items.map((item) => (
          <Fragment key={item.name}>
            <Text ellipsis={{ tooltip: item.name }} className="min-w-0">
              {item.name}
            </Text>
            <Text className="text-right">
              {item.requests.toLocaleString()}
            </Text>
            <Text
              strong
              type={item.violations > 0 ? "danger" : "success"}
              className="text-right"
            >
              {item.violations.toLocaleString()}
            </Text>
          </Fragment>
        ))}
      </div>
    </Card>
  );
};
