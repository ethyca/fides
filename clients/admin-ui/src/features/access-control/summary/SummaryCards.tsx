import type {
  AccessControlSummaryResponse,
  ConsumerRequestsByConsumerResponse,
  TimeseriesResponse,
} from "../types";
import { DataConsumersCard } from "./DataConsumersCard";
import { ViolationRateCard } from "./ViolationRateCard";
import { ViolationsOverTimeCard } from "./ViolationsOverTimeCard";

interface SummaryCardsProps {
  summaryData?: AccessControlSummaryResponse;
  timeseriesData?: TimeseriesResponse;
  consumersData?: ConsumerRequestsByConsumerResponse;
  loading?: boolean;
}

export const SummaryCards = ({
  summaryData,
  timeseriesData,
  consumersData,
  loading,
}: SummaryCardsProps) => (
  <div className="grid grid-cols-3 gap-4">
    <ViolationsOverTimeCard
      data={timeseriesData?.items ?? []}
      totalViolations={summaryData?.violations ?? 0}
      trend={summaryData?.trend ?? 0}
      loading={loading}
    />
    <ViolationRateCard
      violations={summaryData?.violations ?? 0}
      totalRequests={summaryData?.total_requests ?? 0}
      trend={summaryData?.trend ?? 0}
      totalPolicies={summaryData?.total_policies ?? 0}
      loading={loading}
    />
    <DataConsumersCard
      data={consumersData?.items ?? []}
      activeCount={summaryData?.active_consumers ?? 0}
      loading={loading}
    />
  </div>
);
