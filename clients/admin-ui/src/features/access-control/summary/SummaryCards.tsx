import { Flex } from "fidesui";

import type {
  DataConsumerRequestsResponse,
  DataConsumerSummary,
} from "../types";
import DataConsumersCard from "./DataConsumersCard";
import ViolationRateCard from "./ViolationRateCard";
import ViolationsOverTimeCard from "./ViolationsOverTimeCard";

interface SummaryCardsProps {
  requestsData?: DataConsumerRequestsResponse;
  consumersData?: DataConsumerSummary[];
  loading?: boolean;
}

const SummaryCards = ({
  requestsData,
  consumersData,
  loading,
}: SummaryCardsProps) => (
  <Flex gap={16} className="[&>*]:flex-1">
    <ViolationsOverTimeCard
      data={requestsData?.items ?? []}
      loading={loading}
    />
    <ViolationRateCard
      violations={requestsData?.violations ?? 0}
      totalRequests={requestsData?.total_requests ?? 0}
      loading={loading}
    />
    <DataConsumersCard data={consumersData ?? []} loading={loading} />
  </Flex>
);

export default SummaryCards;
