import {
  AntAlert as Alert,
  AntParagraph as Paragraph,
  AntText as Text,
  AntTitle as Title,
} from "fidesui";
import { useRouter } from "next/router";

import ErrorLayout from "~/features/login/error-layout";
import { useGetAllOpenIDProvidersSimpleQuery } from "~/features/openid-authentication/openprovider.slice";
import { OpenIDProvider } from "~/types/api";

const useProvider: () => {
  provider: OpenIDProvider | undefined;
  loading: boolean;
} = () => {
  const router = useRouter();
  const providerTypeParam = router.query?.providerType;
  const providerType = (
    typeof providerTypeParam === "string" ? providerTypeParam : ""
  ).trim();
  const { data: openidProviders, isLoading: providersLoading } =
    useGetAllOpenIDProvidersSimpleQuery();

  const matchedProviders = (openidProviders ?? []).filter(
    (provider) =>
      provider.provider.toLowerCase() === providerType.toLowerCase(),
  );
  return { provider: matchedProviders[0], loading: providersLoading };
};

const Index = () => {
  const { provider } = useProvider();
  return (
    <ErrorLayout>
      <Alert
        showIcon
        type="error"
        message={
          <Title level={2}>
            Missing parameters in SSO provider login redirect
          </Title>
        }
        description={
          <Paragraph>
            Missing required parameters for
            <Text code>{provider?.name}</Text>, please contact your
            administrator or log in another way.
          </Paragraph>
        }
      />
    </ErrorLayout>
  );
};

export default Index;
