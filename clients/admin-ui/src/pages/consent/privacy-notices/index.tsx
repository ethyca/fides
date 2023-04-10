import { Box } from "@fidesui/react";

import Layout from "~/features/common/Layout";
import PrivacyNoticesTable from "~/features/privacy-notices/PrivacyNoticesTable";

const PrivacyNoticesPage = () => (
  <Layout title="Privacy notices">
    <Box data-testid="privacy-notices-page">
      <PrivacyNoticesTable />
    </Box>
  </Layout>
);

export default PrivacyNoticesPage;
