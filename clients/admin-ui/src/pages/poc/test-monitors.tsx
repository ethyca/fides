import { Flex, Layout, Typography } from "fidesui";
import type { NextPage } from "next";

import PageHeader from "~/features/common/PageHeader";
import TestDatastoreMonitor from "~/features/test-monitors/TestDatastoreMonitor";
import TestWebsiteMonitor from "~/features/test-monitors/TestWebsiteMonitor";

const { Content } = Layout;
const { Paragraph } = Typography;

const TestMonitors: NextPage = () => {
  return (
    <Content className="overflow-auto px-10 py-6">
      <PageHeader heading="Test monitors" />
      <Paragraph type="secondary">
        Developer tool for seeding test data via the configurable test monitors.
      </Paragraph>

      <Flex gap="large" align="start" wrap="wrap" className="mt-4">
        <div className="min-w-80 flex-1">
          <TestDatastoreMonitor />
        </div>
        <div className="min-w-80 flex-1">
          <TestWebsiteMonitor />
        </div>
      </Flex>
    </Content>
  );
};

export default TestMonitors;
