import Restrict from "common/Restrict";
import { Box, Text } from "fidesui";
import type { NextPage } from "next";

import { useFeatures } from "~/features/common/features";
import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import OpenIDAuthenticationSection from "~/features/openid-authentication/SSOProvidersSection";
import {
  DEFAULT_ORGANIZATION_FIDES_KEY,
  useGetOrganizationByFidesKeyQuery,
} from "~/features/organization";
import { OrganizationForm } from "~/features/organization/OrganizationForm";
import { ScopeRegistryEnum } from "~/types/api";

const OrganizationPage: NextPage = () => {
  const { data: organization } = useGetOrganizationByFidesKeyQuery(
    DEFAULT_ORGANIZATION_FIDES_KEY,
  );
  const {
    plus: hasPlus,
    flags: { ssoAuthentication },
  } = useFeatures();

  return (
    <Layout title="Organization">
      <Box data-testid="organization-management">
        <PageHeader heading="Organization Management" />
        <Box maxWidth="600px">
          <Text pb={6} fontSize="sm">
            Please use this section to manage your organization&lsquo;s details,
            including key information that will be recorded in the RoPA (Record
            of Processing Activities).
          </Text>
          <Box background="gray.50" padding={2}>
            <OrganizationForm organization={organization} />
          </Box>
          {ssoAuthentication && hasPlus && (
            <Restrict scopes={[ScopeRegistryEnum.OPENID_PROVIDER_CREATE]}>
              <OpenIDAuthenticationSection />
            </Restrict>
          )}
        </Box>
      </Box>
    </Layout>
  );
};
export default OrganizationPage;
