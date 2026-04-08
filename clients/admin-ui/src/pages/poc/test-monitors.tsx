import { Flex, Typography } from "fidesui";
import type { NextPage } from "next";

import Layout from "~/features/common/Layout";
import { SidePanel } from "~/features/common/SidePanel";
import TestDatastoreMonitor from "~/features/test-monitors/TestDatastoreMonitor";
import TestWebsiteMonitor from "~/features/test-monitors/TestWebsiteMonitor";

const { Paragraph } = Typography;

const TestMonitors: NextPage = () => {
  return (
    <>
      <SidePanel>
        <SidePanel.Identity title="Test monitors" />
      </SidePanel>
      <Layout title="Test monitors">
        <Paragraph type="secondary">
          Developer tool for seeding test data via the configurable test
          monitors.
        </Paragraph>

        <Flex gap="large" align="start" wrap="wrap" className="mt-4">
          <div className="min-w-80 flex-1">
            <TestDatastoreMonitor />
          </div>
          <div className="min-w-80 flex-1">
            <TestWebsiteMonitor />
          </div>
        </Flex>
      </Layout>
    </>
  );
};

export default TestMonitors;
