import { Box, Heading, Text } from "@fidesui/react";
import React from "react";

import Layout from "~/features/common/Layout";
import { PrivacyExperiencesTable } from "~/features/privacy-experience/PrivacyExperiencesTable";

const PrivacyExperiencePage = () => (
  <Layout title="Privacy experiences">
    <Box mb={4}>
      <Heading fontSize="2xl" fontWeight="semibold" mb={2} data-testid="header">
        Privacy experience
      </Heading>
    </Box>
    <Text fontSize="sm" mb={8} width={{ base: "100%", lg: "70%" }}>
      Based on your privacy notices, Fides has created the overlay and privacy
      experience configuration below. Your privacy notices will be presented by
      region in these components. Edit each component to adjust the text that
      displays in the privacy center, overlay, and banners that show your
      notices. When you’re ready to include these privacy notices on your
      website, copy the javascript using the button on this page and place it on
      your website.
    </Text>
    <Box data-testid="privacy-experience-page">
      <PrivacyExperiencesTable />
    </Box>
  </Layout>
);

export default PrivacyExperiencePage;
