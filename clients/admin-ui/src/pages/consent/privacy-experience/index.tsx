import { Box, Heading, Text } from "fidesui";
import React from "react";

import FixedLayout from "~/features/common/FixedLayout";
import { PrivacyExperiencesTable } from "~/features/privacy-experience/PrivacyExperiencesTable";

const PrivacyExperiencePage = () => (
  <FixedLayout title="Privacy experiences">
    <Box mb={4} data-testid="privacy-experience-page">
      <Heading fontSize="2xl" fontWeight="semibold" mb={2} data-testid="header">
        Privacy experience
      </Heading>
    </Box>
    <Text fontSize="sm" mb={8} width={{ base: "100%", lg: "70%" }}>
      Based on your privacy notices, Fides has created the banner and modal
      privacy experience configuration below. Each experience contains privacy
      notices and locations where the notices will be displayed. Edit each
      banner, modal, or privacy center to adjust the included privacy notices,
      locations, and text that is displayed to your users. When you’re ready to
      include these privacy notices on your website, copy the JavaScript using
      the button on this page and place it on your website.
    </Text>
    <Box>
      <PrivacyExperiencesTable />
    </Box>
  </FixedLayout>
);

export default PrivacyExperiencePage;
