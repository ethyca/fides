import { Typography } from "fidesui";
import type { NextPage } from "next";

import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import { useGetQueueMonitorQuery } from "~/features/queue-monitor/queue-monitor.slice";
import QueueMonitorTable from "~/features/queue-monitor/QueueMonitorTable";

const { Text } = Typography;

const QueuesPage: NextPage = () => {
  const { data, isLoading, error } = useGetQueueMonitorQuery(undefined, {
    pollingInterval: 1000,
  });

  return (
    <Layout title="SQS Queue Monitor">
      <PageHeader heading="SQS Queue Monitor" />
      {error && (
        <Text type="danger" data-testid="queue-monitor-error">
          Failed to fetch queue data. Retrying...
        </Text>
      )}
      <QueueMonitorTable
        queues={data?.queues ?? []}
        isLoading={isLoading && !data}
      />
    </Layout>
  );
};

export default QueuesPage;
