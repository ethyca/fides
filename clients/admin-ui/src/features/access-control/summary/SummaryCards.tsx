import { Col, Row } from "fidesui";

import type {
  AccessControlSummaryResponse,
  ConsumerRequestsByConsumerResponse,
} from "../types";
import { ViolationsChartCard } from "../ViolationsChartCard";
import { DataConsumersCard } from "./DataConsumersCard";

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
    <Col span={16}>
      <ViolationsChartCard />
    </Col>
    <Col span={8}>
      <DataConsumersCard
        data={consumersData?.items ?? []}
        activeCount={summaryData?.active_consumers ?? 0}
        loading={loading}
      />
    </Col>
  </Row>
);
