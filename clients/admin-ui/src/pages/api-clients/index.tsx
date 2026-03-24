import type { NextPage } from "next";

import FixedLayout from "~/features/common/FixedLayout";
import PageHeader from "~/features/common/PageHeader";
import OAuthClientsList from "~/features/oauth/OAuthClientsTable";

const ApiClientsPage: NextPage = () => {
  return (
    <FixedLayout title="API Clients">
      <PageHeader
        heading="API Clients"
        breadcrumbItems={[{ title: "All API clients" }]}
        isSticky={false}
      />
      <OAuthClientsList />
    </FixedLayout>
  );
};

export default ApiClientsPage;
