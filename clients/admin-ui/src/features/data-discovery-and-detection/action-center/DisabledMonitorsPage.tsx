import { AntAlert as Alert, AntFlex as Flex, Spinner } from "fidesui";

import Layout from "~/features/common/Layout";

interface DisabledMonitorsPageProps {
  isConfigLoading: boolean;
}

const DISABLED_MONITORS_MESSAGE = "Action center is currently disabled.";

export const DisabledMonitorsPage = ({
  isConfigLoading,
}: DisabledMonitorsPageProps) => (
  <Layout title="Action center" mainProps={{ className: "h-full" }}>
    <Flex justify="center" align="center" className="h-full">
      {isConfigLoading ? (
        <Spinner color="primary.900" />
      ) : (
        <Alert
          message="Coming soon..."
          description={DISABLED_MONITORS_MESSAGE}
          type="info"
          showIcon
        />
      )}
    </Flex>
  </Layout>
);
