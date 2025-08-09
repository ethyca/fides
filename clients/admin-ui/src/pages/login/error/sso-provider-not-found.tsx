import {
  AntAlert as Alert,
  AntButton as Button,
  AntText as Text,
  Center,
} from "fidesui";
import NextLink from "next/link";
import { useSearchParams } from "next/navigation";

const NotFoundMessage = () => {
  const searchParams = useSearchParams();
  const providerId = searchParams?.get("providerIdentifier");

  if (providerId && providerId.length > 0) {
    return (
      <Text>
        An SSO provider with the ID <Text code>{providerId}</Text> could not be
        found.
      </Text>
    );
  }

  return <p>No matching SSO Provider could be found.</p>;
};

const SsoProviderNotFound = () => {
  return (
    <Center
      h="100%"
      w="100%"
      display="flex"
      justifyContent="center"
      flexDirection="column"
      rowGap={10}
    >
      <Alert
        showIcon
        type="error"
        message="SSO provider not found"
        description={
          <>
            <NotFoundMessage />
            <p>Please contact your administrator or login another way.</p>
          </>
        }
      />
      <NextLink href="/login" passHref legacyBehavior>
        <Button type="primary">Back to Login</Button>
      </NextLink>
    </Center>
  );
};

export default SsoProviderNotFound;
