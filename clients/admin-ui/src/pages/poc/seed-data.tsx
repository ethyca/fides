import { Layout, Typography } from "fidesui";
import type { NextPage } from "next";

import PageHeader from "~/features/common/PageHeader";
import SeedDataPanel from "~/features/seed-data/SeedDataPanel";

const { Content } = Layout;
const { Paragraph } = Typography;

const SeedDataPage: NextPage = () => {
  return (
    <Content className="overflow-auto px-10 py-6">
      <PageHeader heading="Sample data seeding" />
      <Paragraph type="secondary" className="mb-4">
        Populate this environment with synthetic sample data for demos, testing,
        and internal development. Not intended for production use.
      </Paragraph>
      <SeedDataPanel />
    </Content>
  );
};

export default SeedDataPage;
