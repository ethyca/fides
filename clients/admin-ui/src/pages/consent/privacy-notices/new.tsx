import { Box, Heading, Text } from "@fidesui/react";

import Layout from "~/features/common/Layout";
import BackButton from "~/features/common/nav/v2/BackButton";
import { PRIVACY_NOTICES_ROUTE } from "~/features/common/nav/v2/routes";
import PrivacyNoticeForm from "~/features/privacy-notices/PrivacyNoticeForm";

const NewPrivacyNoticePage = () => (
  <Layout title="New privacy notice">
    <Box mb={4}>
      <BackButton backPath={PRIVACY_NOTICES_ROUTE} />
      <Heading fontSize="2xl" fontWeight="semibold" mb={2} data-testid="header">
        New privacy notice
      </Heading>
    </Box>
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
