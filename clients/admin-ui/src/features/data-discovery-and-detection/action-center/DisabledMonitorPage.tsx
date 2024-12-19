import { AntAlert as Alert, AntFlex as Flex, Spinner } from "fidesui";

import Layout from "~/features/common/Layout";

interface DisabledMonitorPageProps {
  isConfigLoading: boolean;
}

const DISABLED_MONITOR_MESSAGE = "Action center is currently disabled.";

export const DisabledMonitorPage = ({
  isConfigLoading,
}: DisabledMonitorPageProps) => (
  <Layout title="Action center" mainProps={{ className: "h-full" }}>
    <Flex justify="center" align="center" className="h-full">
      {isConfigLoading ? (
        <Spinner color="minos.500" />
      ) : (
        <Alert
          message="Coming soon..."
          description={DISABLED_MONITOR_MESSAGE}
          type="info"
          showIcon
        />
      )}
    </Flex>
  </Layout>
);
