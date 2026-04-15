import { Button, Typography } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";

import FixedLayout from "~/features/common/FixedLayout";
import {
  DATA_CONSUMERS_NEW_ROUTE,
  INTEGRATION_MANAGEMENT_ROUTE,
} from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import DataConsumersTable from "~/features/data-consumers/DataConsumersTable";

const DataConsumersPage: NextPage = () => {
  const router = useRouter();

  return (
    <FixedLayout title="Data consumers">
      <PageHeader
        heading="Data consumers"
        rightContent={
          <Button
            type="primary"
            onClick={() => router.push(DATA_CONSUMERS_NEW_ROUTE)}
            data-testid="add-consumer-button"
          >
            + Add consumer
          </Button>
        }
      >
        <Typography.Text type="secondary">
          Teams, projects, agents, and service accounts that access data. Import
          consumers automatically by connecting an{" "}
          <Typography.Link href={INTEGRATION_MANAGEMENT_ROUTE}>
            identity provider integration
          </Typography.Link>{" "}
          like Google Groups, Active Directory, or Okta.
        </Typography.Text>
      </PageHeader>
      <DataConsumersTable />
    </FixedLayout>
  );
};

export default DataConsumersPage;
