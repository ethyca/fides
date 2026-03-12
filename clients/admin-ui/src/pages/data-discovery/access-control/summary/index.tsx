import { Segmented } from "fidesui";
import type { NextPage } from "next";
import { useMemo, useState } from "react";

import {
  useGetDataConsumerRequestsQuery,
  useGetDataConsumersByViolationsQuery,
} from "~/features/access-control/access-control.slice";
import AccessControlTabs from "~/features/access-control/AccessControlTabs";
import { FindingsTable } from "~/features/access-control/summary/FindingsTable";
import { SummaryCards } from "~/features/access-control/summary/SummaryCards";
import type { TimeRange } from "~/features/access-control/types";
import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";

const TIME_RANGE_OPTIONS = [
  { label: "24H", value: "24h" },
  { label: "7D", value: "7d" },
  { label: "30D", value: "30d" },
];

const TIME_RANGE_DAYS: Record<TimeRange, number> = {
  "24h": 1,
  "7d": 7,
  "30d": 30,
};

const getDateRange = (timeRange: TimeRange) => {
  const end = new Date();
  const start = new Date();
  start.setDate(start.getDate() - TIME_RANGE_DAYS[timeRange]);
  return { start_date: start.toISOString(), end_date: end.toISOString() };
};

const AccessControlSummaryPage: NextPage = () => {
  const [timeRange, setTimeRange] = useState<TimeRange>("7d");
  const dateRange = useMemo(() => getDateRange(timeRange), [timeRange]);

  const { data: requestsData, isLoading: requestsLoading } =
    useGetDataConsumerRequestsQuery(dateRange);

  const { data: consumersData, isLoading: consumersLoading } =
    useGetDataConsumersByViolationsQuery({
      ...dateRange,
      group_by: "consumer",
      order_by: "violation_count",
    });

  const loading = requestsLoading || consumersLoading;

  return (
    <Layout title="Access control">
      <PageHeader heading="Access control" isSticky />
      <div className="px-6">
        <AccessControlTabs />
        <div className="mb-4">
          <Segmented
            options={TIME_RANGE_OPTIONS}
            value={timeRange}
            onChange={(val) => setTimeRange(val as TimeRange)}
          />
        </div>
        <SummaryCards
          requestsData={requestsData}
          consumersData={consumersData?.items}
          loading={loading}
        />
        <FindingsTable />
      </div>
    </Layout>
  );
};

export default AccessControlSummaryPage;
