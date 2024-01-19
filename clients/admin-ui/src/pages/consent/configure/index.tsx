import { Box, Flex, Heading, Text } from "@fidesui/react";
import React from "react";

import FixedLayout from "~/features/common/FixedLayout";
import { ConsentManagementTable } from "~/features/configure-consent/ConsentManagementTable";

type Props = {
  title: string;
  description: string;
};

const ConsentMetadata: React.FC<Props> = ({ title, description }) => (
  <>
    <Box mb={4}>
      <Heading fontSize="2xl" fontWeight="semibold" mb={2} data-testid="header">
        {title}
      </Heading>
    </Box>
    <Flex>
      <Text fontSize="sm" mb={8} width={{ base: "100%", lg: "50%" }}>
        {description}
      </Text>
    </Flex>
  </>
);


const ConfigureConsentPage = () => {
  const { tcf: isTcfEnabled } = useFeatures();

  if (isTcfEnabled) {
    return (
      <Layout title="Consent reporting">
        <ConsentMetadata
          includeAddVendors
          title="Manage your vendors"
          description="Use the table below to manage your vendors. Modify the legal basis for a vendor if permitted and view and group your views by applying different filters"
        />
        <ConsentManagementTable />
      </Layout>
    );
  }

  return (
    <Layout title="Consent reporting">
      <ConsentMetadata
        title="Consent reporting"
        description="Your current cookies and tracking information."
      />
      <ConfigureConsent />
    </Layout>
  );
};

const ConfigureConsentPage = () => (
  <FixedLayout
    title="Configure consent"
    mainProps={{
      padding: "40px",
      paddingRight: "48px",
    }}
  >
    <ConsentMetadata
      title="Manage your vendors"
      description="Use the table below to manage your vendors. Modify the legal basis for a vendor if permitted and view and group your views by applying different filters"
    />
    <ConsentManagementTable />
  </FixedLayout>
);

export default ConfigureConsentPage;
