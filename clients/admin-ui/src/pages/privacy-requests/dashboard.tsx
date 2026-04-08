import { Typography } from "fidesui";
import type { NextPage } from "next";

import Layout from "~/features/common/Layout";

const { Title, Text } = Typography;

const PrivacyRequestsDashboard: NextPage = () => (
  <Layout title="Privacy Requests">
    <Title level={1}>Lethe</Title>
    <Text type="secondary">
      Privacy Requests dashboard — How do we honor data subject rights?
    </Text>
  </Layout>
);

export default PrivacyRequestsDashboard;
