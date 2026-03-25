import { Layout, Typography } from "fidesui";
import type { NextPage } from "next";

import PageHeader from "~/features/common/PageHeader";
import SeedDataPanel from "~/features/seed-data/SeedDataPanel";

const { Content } = Layout;
const { Paragraph } = Typography;

const SeedDataPage: NextPage = () => {
  return (
    <Content className="overflow-auto px-10 py-6">
      <PageHeader heading="Seed data" />
      <Paragraph type="secondary" className="mb-4">
        Seed demo data into this environment for testing and development.
      </Paragraph>
      <SeedDataPanel />
    </Content>
  );
};

export default SeedDataPage;
