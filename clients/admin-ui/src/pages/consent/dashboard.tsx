import { Typography } from "fidesui";
import type { NextPage } from "next";

import Layout from "~/features/common/Layout";

const { Title, Text } = Typography;

const ConsentDashboard: NextPage = () => (
  <Layout title="Consent">
    <Title level={1}>Janus</Title>
    <Text type="secondary">
      Consent dashboard — What data can we use, under what terms?
    </Text>
  </Layout>
);

export default ConsentDashboard;
