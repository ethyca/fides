import { Col, Row } from "fidesui";

import {
  useGetAccessControlSummaryQuery,
  useGetConsumersByViolationsQuery,
} from "./access-control.slice";
import { DataConsumersCard } from "./DataConsumersCard";
import { useRequestLogFilterContext } from "./hooks/useRequestLogFilters";
import { ViolationRateCard } from "./ViolationRateCard";
import { ViolationsChartCard } from "./ViolationsChartCard";

export const SummaryCards = () => {
  const { filters } = useRequestLogFilterContext();

  const { data: summaryData, isLoading: summaryLoading } =
    useGetAccessControlSummaryQuery(filters);

  const { data: consumersData, isLoading: consumersLoading } =
    useGetConsumersByViolationsQuery({
      ...filters,
      order_by: "violation_count",
    });

  const loading = summaryLoading || consumersLoading;

  return (
    <Row gutter={16}>
      <Col span={14}>
        <ViolationsChartCard />
      </Col>
      <Col span={5}>
        <ViolationRateCard
          violations={summaryData?.violations ?? 0}
          totalRequests={summaryData?.total_requests ?? 0}
          trend={summaryData?.trend ?? 0}
          loading={loading}
        />
      </Col>
      <Col span={5}>
        <DataConsumersCard
          data={consumersData?.items ?? []}
          loading={loading}
        />
      </Col>
    </Row>
  );
};
