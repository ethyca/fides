import {
  AntButton as Button,
  Box,
  Heading,
  Text,
  useDisclosure,
} from "fidesui";

import AddSSOProviderModal from "~/features/openid-authentication/AddSSOProviderModal";
import { useGetAllOpenIDProvidersQuery } from "~/features/openid-authentication/openprovider.slice";
import SSOProvider from "~/features/openid-authentication/SSOProvider";
import { OpenIDProvider } from "~/types/api/models/OpenIDProvider";

const SSOProvidersSection = () => {
  const { onOpen, isOpen, onClose } = useDisclosure();
  const { data: openidProviders } = useGetAllOpenIDProvidersQuery();

  const renderItems: () => JSX.Element[] | undefined = () =>
    openidProviders?.map((item: OpenIDProvider) => (
      <SSOProvider key={item.identifier} openIDProvider={item} />
    ));

  return (
    <Box maxWidth="600px" marginTop="40px">
      <Heading
        marginBottom={4}
        fontSize="lg"
        display="flex"
        justifyContent="space-between"
      >
        SSO Providers
        {openidProviders && openidProviders.length < 5 && (
          <Button onClick={onOpen} data-testid="add-sso-provider-btn">
            Add SSO Provider
          </Button>
        )}
      </Heading>
      <Text marginBottom="30px" fontSize="sm">
        Use this area to add and manage SSO providers for you organization.
        Select “Add SSO provider” to add a new provider.
      </Text>
      {renderItems()}
      <AddSSOProviderModal isOpen={isOpen} onClose={onClose} />
    </Box>
  );
};

export default SSOProvidersSection;
