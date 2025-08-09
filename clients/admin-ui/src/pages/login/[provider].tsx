import { Center, Spinner, useToast } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import { useEffect, useState } from "react";
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

  useEffect(() => {
    if (!authMethodsLoading && !authMethods?.sso) {
      router.push("/login/error/sso-not-enabled");
      return;
    }

    if (!providersLoading && openidProviders && pathHasProvider) {
      const hasProviderMatch = openidProviders.some(
        (provider) => provider.identifier === providerId,
      );

      if (!hasProviderMatch) {
        const searchParams = new URLSearchParams();
        searchParams.set("providerIdentifier", providerId);
        router.push(
          `/login/error/sso-provider-not-found?${searchParams.toString()}`,
        );
      }
    }
  }, [
    authMethods?.sso,
    authMethodsLoading,
    openidProviders,
    pathHasProvider,
    providerId,
    providersLoading,
    router,
  ]);

  useEffect(() => {
    if (!router.query || !router.query.provider || !router.query.code) {
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
  }, [router, toast, dispatch, router.query, loginRequest]);

  return <Pending />;
};

export default LoginWithOIDC;
