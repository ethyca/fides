import { Alert, Flex } from "fidesui";

import Layout from "~/features/common/Layout";

const DISABLED_MONITORS_MESSAGE = "Action center is currently disabled.";

export const DisabledMonitorsPage = () => (
  <Layout title="Action center" mainProps={{ className: "h-full" }}>
    <Flex justify="center" align="center" className="h-full">
      <Alert
        message="Coming soon..."
        description={DISABLED_MONITORS_MESSAGE}
        type="info"
        showIcon
      />
    </Flex>
  </Layout>
);
