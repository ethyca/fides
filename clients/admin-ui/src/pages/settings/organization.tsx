import { Box, Heading, Text } from "fidesui";
import type { NextPage } from "next";

import { useFlags } from "~/features/common/features";
import Layout from "~/features/common/Layout";
import { OpenIDProviderForm } from "~/features/openid-authentication/OpenIDProviderForm";
import { useGetAllOpenIDProvidersQuery } from "~/features/openid-authentication/openprovider.slice";
import {
  DEFAULT_ORGANIZATION_FIDES_KEY,
  useGetOrganizationByFidesKeyQuery,
} from "~/features/organization";
import { OrganizationForm } from "~/features/organization/OrganizationForm";
import { OpenIDProvider } from "~/types/api/models/OpenIDProvider";

const OpenIDAuthenticationSection = () => {
  const { data: openidProviders } = useGetAllOpenIDProvidersQuery();

  const renderItems: () => JSX.Element[] | undefined = () =>
    openidProviders?.map((item: OpenIDProvider) => (
      <Box key={item.provider} background="gray.50" padding={2}>
        <OpenIDProviderForm openIDProvider={item} />
      </Box>
    ));

  return (
    <Box maxWidth="600px">
      <Heading marginBottom={4} fontSize="lg">
        Add new OpenID Provider
      </Heading>
      <Box background="gray.50" padding={2} marginY={10}>
        <OpenIDProviderForm />
      </Box>
      {openidProviders?.length > 0 && (<>
        <Heading marginBottom={4} fontSize="lg">
          Edit existing OpenID Providers
        </Heading>
        <Box background="gray.50" padding={2} marginY={10}>
          {renderItems()}
        </Box>
      </>)
      }
    </Box>
  );
};

const OrganizationPage: NextPage = () => {
  const { data: organization } = useGetOrganizationByFidesKeyQuery(
    DEFAULT_ORGANIZATION_FIDES_KEY
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
