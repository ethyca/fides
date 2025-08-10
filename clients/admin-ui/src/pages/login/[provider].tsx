import { Center, Spinner, useToast } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import { useEffect } from "react";
import { useDispatch } from "react-redux";

import {
  login,
  useGetAuthenticationMethodsQuery,
  useLoginWithOIDCMutation,
} from "~/features/auth";
import { LoginWithOIDCRequest } from "~/features/auth/types";
import { useGetAllOpenIDProvidersSimpleQuery } from "~/features/openid-authentication/openprovider.slice";

const Pending = () => (
  <Center h="100%" w="100%">
    <Spinner color="primary" size="xl" />
  </Center>
);

const LoginWithOIDC: NextPage = () => {
  const router = useRouter();
  const dispatch = useDispatch();
  const [loginRequest] = useLoginWithOIDCMutation();
  const toast = useToast();

  const { data: authMethods, isLoading: authMethodsLoading } =
    useGetAuthenticationMethodsQuery();
  const { data: openidProviders, isLoading: providersLoading } =
    useGetAllOpenIDProvidersSimpleQuery();

  const providerId =
    typeof router.query.provider === "string" ? router.query.provider : "";
  const pathHasProvider = providerId.length > 0;
  const providerMatches = (openidProviders ?? []).filter(
    (provider) => provider.identifier === providerId,
  );
  const providerMatch = providerMatches.length > 0 ? providerMatches[0] : null;
  const hasProviderMatch = Boolean(providerMatch);

  useEffect(() => {
    // Waiting for Provider information.
    if (authMethodsLoading || providersLoading) {
      return;
    }

    if (!authMethods?.sso) {
      router.push("/login/error/sso-not-enabled");
      return;
    }

    // Route did not match a configured Provider.
    if (pathHasProvider && !hasProviderMatch) {
      const searchParams = new URLSearchParams();
      searchParams.set("providerIdentifier", providerId);
      router.push(
        `/login/error/sso-provider-not-found?${searchParams.toString()}`,
      );
      return;
    }

    // Can't continue until we check if we have a query, it may be null initially.
    if (!router.query) {
      return;
    }

    // Now that we have the query, check for a provider and code, we cannot proceed without these.
    if (!router.query.provider || !router.query.code) {
      // Redirect to an error page for the provider type so that we can offer rich information.
      router.push(`/login/error/provider/${providerMatch?.provider}`);
      return;
    }

    const data: LoginWithOIDCRequest = {
      provider: router.query.provider as string,
      code: router.query.code as string,
    };
    loginRequest(data)
      .unwrap()
      .then((response) => {
        dispatch(login(response));
        router.push("/");
      })
      .catch((error) => {
        toast({
          status: "error",
          description: error?.data?.detail,
        });
        router.push("/login");
      });
  }, [
    router,
    toast,
    dispatch,
    router.query,
    loginRequest,
    providerId,
    authMethodsLoading,
    authMethods?.sso,
    providersLoading,
    openidProviders,
    pathHasProvider,
    hasProviderMatch,
    providerMatch?.provider,
  ]);

  return <Pending />;
};

export default LoginWithOIDC;
