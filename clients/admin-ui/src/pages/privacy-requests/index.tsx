import type { NextPage } from "next";

import Layout from "~/features/common/Layout";
import PrivacyRequestsContainer from "~/features/privacy-requests/PrivacyRequestsContainer";

const PrivacyRequests: NextPage = () => (
  <Layout title="Privacy Requests">
    <PrivacyRequestsContainer />
  </Layout>
);
export default PrivacyRequests;
