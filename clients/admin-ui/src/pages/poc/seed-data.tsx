import { Typography } from "fidesui";
import type { NextPage } from "next";

import Layout from "~/features/common/Layout";
import { SidePanel } from "~/features/common/SidePanel";
import SeedDataPanel from "~/features/seed-data/SeedDataPanel";

const { Paragraph } = Typography;

const SeedDataPage: NextPage = () => {
  return (
    <>
      <SidePanel>
        <SidePanel.Identity title="Sample data seeding" />
      </SidePanel>
      <Layout title="Sample data seeding">
        <Paragraph type="secondary" className="mb-4">
          Populate this environment with synthetic sample data for demos,
          testing, and internal development. Not intended for production use.
        </Paragraph>
        <SeedDataPanel />
      </Layout>
    </>
  );
};

export default SeedDataPage;
