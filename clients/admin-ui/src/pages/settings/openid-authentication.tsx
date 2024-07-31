import { Box, Heading, Text } from "fidesui";
import type { NextPage } from "next";

import Layout from "~/features/common/Layout";
import { OpenIDProviderForm } from "~/features/openid-authentication/OpenIDProviderForm";
import { useGetAllOpenIDProvidersQuery } from "~/features/openid-authentication/openprovider.slice";
import { OpenIDProvider } from "~/types/api";

const OpenIDAuthenticationPage: NextPage = () => {
  const { data } = useGetAllOpenIDProvidersQuery();

  const renderItems: () => JSX.Element[] | undefined = () =>
    data?.map((item: OpenIDProvider) => (
      <Box key={item.provider} background="gray.50" padding={2}>
        <OpenIDProviderForm openIDProvider={item} />
      </Box>
    ));

  return (
    <Layout title="OpenID Authentication">
      <Box data-testid="openid-authentication-management">
        <Heading marginBottom={4} fontSize="2xl">
          OpenID Authentication
        </Heading>
        <Box maxWidth="600px">
          <Text marginBottom={10} fontSize="sm">
            Please use this section to manage your organization&apos;s OpenID
            Providers, including key information necessary for configuring and
            maintaining secure and efficient authentication services.
          </Text>
          <Box background="gray.50" padding={2}>
            <OpenIDProviderForm />
          </Box>
          {renderItems()}
        </Box>
      </Box>
    </Layout>
  );
};
export default OpenIDAuthenticationPage;
