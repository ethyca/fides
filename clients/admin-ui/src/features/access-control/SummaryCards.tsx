import { Col, Row } from "fidesui";

import type {
  AccessControlSummaryResponse,
  ConsumerRequestsByConsumerResponse,
} from "./types";
import { DataConsumersCard } from "./DataConsumersCard";
import { ViolationRateCard } from "./ViolationRateCard";
import { ViolationsChartCard } from "./ViolationsChartCard";

interface SummaryCardsProps {
  summaryData?: AccessControlSummaryResponse;
  consumersData?: ConsumerRequestsByConsumerResponse;
  loading?: boolean;
}

export const SummaryCards = ({
  summaryData,
  consumersData,
  loading,
}: SummaryCardsProps) => (
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
        activeCount={summaryData?.active_consumers ?? 0}
        loading={loading}
      />
    </Col>
  </Row>
);
