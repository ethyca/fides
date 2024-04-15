import { useState } from "react";

import Layout from "~/features/common/Layout";
import TestMonitorResultTable from "~/features/data-discovery-and-detection/TestMonitorResultTable";
import TestMonitorTable from "~/features/data-discovery-and-detection/TestMonitorTable";
import { DiscoveryMonitorConfig } from "~/types/api";

const TestDiscoveryPage = () => {
  const [monitor, setMonitor] = useState<DiscoveryMonitorConfig | undefined>(
    undefined
  );

  return (
    <Layout title="Detection Results">
      {monitor ? (
        <TestMonitorResultTable configId={monitor.id!} />
      ) : (
        <TestMonitorTable viewMonitorResults={setMonitor} />
      )}
    </Layout>
  );
};

export default TestDiscoveryPage;
