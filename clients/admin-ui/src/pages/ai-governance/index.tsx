import { Typography } from "fidesui";
import type { NextPage } from "next";

import Layout from "~/features/common/Layout";

const { Title, Text } = Typography;

const AIGovernanceDashboard: NextPage = () => (
  <Layout title="AI Governance">
    <Title level={1}>Astralis</Title>
    <Text type="secondary">
      AI Governance dashboard — Who can access what data, for what purpose, and
      is it compliant?
    </Text>
  </Layout>
);

export default AIGovernanceDashboard;
