import { Card, Col, Divider, Row, Text } from "fidesui";
import { Fragment } from "react";

import { useGetConsumersByViolationsQuery } from "./access-control.slice";
import { useRequestLogFilterContext } from "./hooks/useRequestLogFilters";

export const DataConsumersCard = () => {
  const { filters } = useRequestLogFilterContext();

  const { data, isLoading } = useGetConsumersByViolationsQuery({
    ...filters,
    order_by: "violation_count",
    size: 5,
  });

  const items = data?.items ?? [];

  return (
    <Card
      loading={isLoading}
      title={<Text strong>Data consumers</Text>}
      className="h-full"
    >
      <Row wrap={false}>
        <Col flex="auto">
          <Text type="secondary" className="text-xs">
            Consumer
          </Text>
        </Col>
        <Col flex="none">
          <Text type="secondary" className="text-xs">
            Reqs.
          </Text>
        </Col>
        <Col flex="none" className="ml-4">
          <Text type="secondary" className="text-xs">
            Viol.
          </Text>
        </Col>
      </Row>

      {items.map((item, index) => (
        <Fragment key={item.name}>
          <Divider className={index === 0 ? "my-2" : "my-1.5"} />
          <Row wrap={false} align="middle">
            <Col flex="auto" className="min-w-0">
              <Text ellipsis={{ tooltip: item.name }}>{item.name}</Text>
            </Col>
            <Col flex="none" className="text-right">
              {item.requests.toLocaleString()}
            </Col>
            <Col flex="none" className="ml-4 text-right">
              <Text strong type={item.violations > 0 ? "danger" : "success"}>
                {item.violations.toLocaleString()}
              </Text>
            </Col>
          </Row>
        </Fragment>
      ))}
    </Card>
  );
};
