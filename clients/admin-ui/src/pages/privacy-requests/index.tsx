import type { NextPage } from "next";

import FixedLayout from "~/features/common/FixedLayout";
import PrivacyRequestsContainer from "~/features/privacy-requests/PrivacyRequestsContainer";

const PrivacyRequests: NextPage = () => (
  <FixedLayout title="Privacy Requests" mainProps={{ overflowY: "scroll" }}>
    <PrivacyRequestsContainer />
  </FixedLayout>
);
export default PrivacyRequests;
