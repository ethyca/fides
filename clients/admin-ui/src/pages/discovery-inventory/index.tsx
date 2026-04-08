import { Typography } from "fidesui";
import type { NextPage } from "next";

import Layout from "~/features/common/Layout";

const { Title, Text } = Typography;

const DiscoveryInventoryDashboard: NextPage = () => (
  <Layout title="Discovery & Inventory">
    <Title level={1}>Helios</Title>
    <Text type="secondary">
      Discovery &amp; Inventory dashboard — What data do we have, where is it,
      and what does it look like?
    </Text>
  </Layout>
);

export default DiscoveryInventoryDashboard;
