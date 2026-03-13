import { Flex } from "fidesui";

import type {
  DataConsumerRequestsResponse,
  DataConsumersByViolationsResponse,
} from "../types";
import { DataConsumersCard } from "./DataConsumersCard";
import { ViolationRateCard } from "./ViolationRateCard";
import { ViolationsOverTimeCard } from "./ViolationsOverTimeCard";

interface SummaryCardsProps {
  requestsData?: DataConsumerRequestsResponse;
  consumersData?: DataConsumersByViolationsResponse;
  loading?: boolean;
}

export const SummaryCards = ({
  requestsData,
  consumersData,
  loading,
}: SummaryCardsProps) => (
  <Flex className="grid grid-cols-3 gap-4">
    <ViolationsOverTimeCard
      data={requestsData?.items ?? []}
      totalViolations={requestsData?.violations ?? 0}
      trend={requestsData?.trend ?? 0}
      loading={loading}
    />
    <ViolationRateCard
      violations={requestsData?.violations ?? 0}
      totalRequests={requestsData?.total_requests ?? 0}
      trend={requestsData?.trend ?? 0}
      topPolicies={requestsData?.top_policies ?? []}
      totalPolicies={requestsData?.total_policies ?? 0}
      loading={loading}
    />
    <DataConsumersCard
      data={consumersData?.items ?? []}
      activeCount={consumersData?.active_consumers ?? 0}
      loading={loading}
    />
  </Flex>
);
