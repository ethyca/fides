import { Box, Heading, Text } from "fidesui";
import type { NextPage } from "next";

import { useFlags } from "~/features/common/features";
import Layout from "~/features/common/Layout";
import OpenIDAuthenticationSection from "~/features/openid-authentication/SSOProvidersSection";
import {
  DEFAULT_ORGANIZATION_FIDES_KEY,
  useGetOrganizationByFidesKeyQuery,
} from "~/features/organization";
import { OrganizationForm } from "~/features/organization/OrganizationForm";

const OrganizationPage: NextPage = () => {
  const { data: organization } = useGetOrganizationByFidesKeyQuery(
    DEFAULT_ORGANIZATION_FIDES_KEY,
  );
  const {
    flags: { openIDAuthentication },
  } = useFlags();

  return (
    <Layout title="Organization">
      <Box data-testid="organization-management">
        <Heading marginBottom={4} fontSize="2xl">
          Organization Management
        </Heading>
        <Box maxWidth="600px">
          <Text marginBottom={10} fontSize="sm">
            Please use this section to manage your organization&lsquo;s details,
            including key information that will be recorded in the RoPA (Record
            of Processing Activities).
          </Text>
          <Box background="gray.50" padding={2}>
            <OrganizationForm organization={organization} />
          </Box>
          {openIDAuthentication && <OpenIDAuthenticationSection />}
        </Box>
      </Box>
    </Layout>
  );
};
export default OrganizationPage;
