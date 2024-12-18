import { Box, Text } from "fidesui";

import Layout from "~/features/common/Layout";
import { PRIVACY_NOTICES_ROUTE } from "~/features/common/nav/v2/routes";
import PageHeader from "~/features/common/PageHeader";
import PrivacyNoticeForm from "~/features/privacy-notices/PrivacyNoticeForm";

const NewPrivacyNoticePage = () => (
  <Layout title="New privacy notice">
    <PageHeader
      heading="Privacy Notices"
      breadcrumbItems={[
        { title: "All privacy Notices", href: PRIVACY_NOTICES_ROUTE },
        { title: "New privacy notice" },
      ]}
    />
    <Box width={{ base: "100%", lg: "70%" }}>
      <Text fontSize="sm" mb={8}>
        Configure your privacy notice including consent mechanism, associated
        data uses and the locations in which this should be displayed to users.
      </Text>
      <Box data-testid="new-privacy-notice-page">
        <PrivacyNoticeForm />
      </Box>
    </Box>
  </Layout>
);

export default NewPrivacyNoticePage;
