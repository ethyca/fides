import type { NextPage } from "next";
import Layout from "~/features/common/Layout";
import Setup from "../../features/config-wizard/setup";

const ConfigWizard: NextPage = () => (
  <Layout title="Config Wizard">
    <Setup />
  </Layout>
);

export default ConfigWizard;
