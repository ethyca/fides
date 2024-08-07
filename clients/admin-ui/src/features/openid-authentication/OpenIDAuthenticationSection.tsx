import { Box, Button, Heading, useDisclosure } from "fidesui";

import AddSSOProviderModal from "~/features/openid-authentication/AddSSOProviderModal";
import { useGetAllOpenIDProvidersQuery } from "~/features/openid-authentication/openprovider.slice";
import SSOProvider from "~/features/openid-authentication/SSOProvider";
import { OpenIDProvider } from "~/types/api/models/OpenIDProvider";


const OpenIDAuthenticationSection = () => {
    const { onOpen, isOpen, onClose } = useDisclosure();
    const { data: openidProviders } = useGetAllOpenIDProvidersQuery();

    const renderItems: () => JSX.Element[] | undefined = () =>
      openidProviders?.map((item: OpenIDProvider) => (
        <SSOProvider key={item.id} openIDProvider={item} />
      ));

    return (
      <Box maxWidth="600px" marginTop="40px">
        <Heading marginBottom={4} fontSize="lg" display="flex" justifyContent="space-between">
          SSO Providers
          <Button
              size="sm"
              variant="outline"
              onClick={onOpen}
              data-testid="add-sso-provider-btn"
            >
              Add SSO Provider
          </Button>
        </Heading>
        {openidProviders?.length > 0 && renderItems()}
        {openidProviders?.length > 0 && renderItems()}
      <AddSSOProviderModal isOpen={isOpen} onClose={onClose} />
      </Box>
    );
  };

export default OpenIDAuthenticationSection;
