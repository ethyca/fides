import { AntAlert as Alert, AntText as Text } from "fidesui";
import { useSearchParams } from "next/navigation";

import ErrorLayout from "~/features/login/error-layout";

const useProviderId = () => {
  const searchParams = useSearchParams();
  const providerId = searchParams?.get("providerIdentifier");
  return (providerId ?? "").trim();
};

const NotFoundMessage = ({ providerId }: { providerId: string }) => {
  if (providerId.length > 0) {
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
  const providerId = useProviderId();

  return (
    <ErrorLayout>
      <Alert
        showIcon
        type="error"
        message="SSO provider not found"
        description={
          <>
            <NotFoundMessage providerId={providerId} />
            <p>
              Please a share link to this page with your administrator or login
              another way.
            </p>
          </>
        }
      />
    </ErrorLayout>
  );
};

export default SsoProviderNotFound;
