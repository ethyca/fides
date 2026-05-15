import type { NextPage } from "next";

import Layout from "~/features/common/Layout";
import { DashboardGraphqlProvider } from "~/features/dashboard-graphql/DashboardGraphqlProvider";
import { DashboardGraphqlView } from "~/features/dashboard-graphql/DashboardGraphqlView";

const DashboardGraphqlPage: NextPage = () => (
  <Layout title="Dashboard (GraphQL)" padded={false}>
    <DashboardGraphqlProvider>
      <DashboardGraphqlView />
    </DashboardGraphqlProvider>
  </Layout>
);

export default DashboardGraphqlPage;
