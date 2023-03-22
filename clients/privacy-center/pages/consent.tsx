import {
  Button,
  Divider,
  Flex,
  Heading,
  Image,
  Stack,
  Text,
  useToast,
} from "@fidesui/react";
import type { NextPage } from "next";
import Head from "next/head";
import { useRouter } from "next/router";
import React, { useCallback, useEffect, useMemo } from "react";

import {
  getConsentContext,
  resolveConsentValue,
  setConsentCookie,
} from "fides-consent";
import { useAppDispatch, useAppSelector } from "~/app/hooks";
import { inspectForBrowserIdentities } from "~/common/browser-identities";
import { useLocalStorage } from "~/common/hooks";
import { ErrorToastOptions, SuccessToastOptions } from "~/common/toast-options";
import ConsentItemCard from "~/components/ConsentItemCard";
import { config } from "~/constants";
import {
  selectConfigConsentOptions,
  updateConsentOptionsFromApi,
} from "~/features/common/config.slice";
import {
  selectFidesKeyToConsent,
  selectPersistedFidesKeyToConsent,
  updateConsentFromApi,
  useLazyGetConsentRequestPreferencesQuery,
  usePostConsentRequestVerificationMutation,
  useUpdateConsentRequestPreferencesMutation,
} from "~/features/consent/consent.slice";
import { getGpcStatus, makeCookieKeyConsent } from "~/features/consent/helpers";
import { useGetIdVerificationConfigQuery } from "~/features/id-verification";
import { ConsentPreferences } from "~/types/api";
import { GpcBanner } from "~/features/consent/GpcMessages";
import { GpcStatus } from "~/features/consent/types";

const Consent: NextPage = () => {
  const [consentRequestId] = useLocalStorage("consentRequestId", "");
  const [verificationCode] = useLocalStorage("verificationCode", "");
  const router = useRouter();
  const toast = useToast();
  const dispatch = useAppDispatch();
  const fidesKeyToConsent = useAppSelector(selectFidesKeyToConsent);
  const persistedFidesKeyToConsent = useAppSelector(
    selectPersistedFidesKeyToConsent
  );
  const consentOptions = useAppSelector(selectConfigConsentOptions);

  const getIdVerificationConfigQueryResult = useGetIdVerificationConfigQuery();
  const [
    postConsentRequestVerificationMutationTrigger,
    postConsentRequestVerificationMutationResult,
  ] = usePostConsentRequestVerificationMutation();
  const [
    getConsentRequestPreferencesQueryTrigger,
    getConsentRequestPreferencesQueryResult,
  ] = useLazyGetConsentRequestPreferencesQuery();
  const [
    updateConsentRequestPreferencesMutationTrigger,
    updateConsentRequestPreferencesMutationResult,
  ] = useUpdateConsentRequestPreferencesMutation();

  const consentContext = useMemo(() => getConsentContext(), []);

  // TODO(#2299): Use error utils from shared package.
  const toastError = useCallback(
    ({
      title = "An error occurred while retrieving user consent preferences.",
      error,
    }: {
      title?: string;
      error?: any;
    }) => {
      toast({
        title,
        description: error?.data?.detail,
        ...ErrorToastOptions,
      });
    },
    [toast]
  );

  const redirectToIndex = useCallback(() => {
    router.push("/");
  }, [router]);

  /**
   * Populate the store with the consent preferences returned by the API.
   */
  const storeConsentPreferences = useCallback(
    (data: ConsentPreferences) => {
      dispatch(updateConsentOptionsFromApi(data));
      dispatch(updateConsentFromApi(data));
    },
    [dispatch]
  );

  /**
   * The consent cookie is updated only when the "persisted" consent preferences are updated. This
   * ensures the browser's behavior matches what the server expects.
   */
  useEffect(() => {
    setConsentCookie(
      makeCookieKeyConsent({
        consentOptions,
        fidesKeyToConsent: persistedFidesKeyToConsent,
        consentContext,
      })
    );
  }, [consentOptions, persistedFidesKeyToConsent, consentContext]);

  /**
   * When the Id verification method is known, trigger the request that will
   * return the consent choices saved on the server.
   */
  useEffect(() => {
    if (!consentRequestId) {
      toastError({ title: "No consent request in progress." });
      redirectToIndex();
      return;
    }

    if (getIdVerificationConfigQueryResult.isError) {
      toastError({ error: getIdVerificationConfigQueryResult.error });
      return;
    }

    if (!getIdVerificationConfigQueryResult.isSuccess) {
      return;
    }

    const privacyCenterConfig = getIdVerificationConfigQueryResult.data;
    if (
      privacyCenterConfig.identity_verification_required &&
      !verificationCode
    ) {
      toastError({ title: "Identity verification is required." });
      redirectToIndex();
      return;
    }

    if (privacyCenterConfig.identity_verification_required) {
      postConsentRequestVerificationMutationTrigger({
        id: consentRequestId,
        code: verificationCode,
      });
    } else {
      getConsentRequestPreferencesQueryTrigger({
        id: consentRequestId,
      });
    }
  }, [
    consentRequestId,
    verificationCode,
    getIdVerificationConfigQueryResult,
    postConsentRequestVerificationMutationTrigger,
    getConsentRequestPreferencesQueryTrigger,
    toastError,
    redirectToIndex,
  ]);

  /**
   * Initialize consent items from the request verification response.
   */
  useEffect(() => {
    if (postConsentRequestVerificationMutationResult.isError) {
      toastError({
        error: postConsentRequestVerificationMutationResult.error,
      });
      redirectToIndex();
      return;
    }

    if (postConsentRequestVerificationMutationResult.isSuccess) {
      storeConsentPreferences(
        postConsentRequestVerificationMutationResult.data
      );
    }
  }, [
    postConsentRequestVerificationMutationResult,
    storeConsentPreferences,
    toastError,
    redirectToIndex,
  ]);

  /**
   * Initialize consent items from the unverified preferences response.
   */
  useEffect(() => {
    if (getConsentRequestPreferencesQueryResult.isError) {
      toastError({
        error: getConsentRequestPreferencesQueryResult.error,
      });
      redirectToIndex();
      return;
    }

    if (getConsentRequestPreferencesQueryResult.isSuccess) {
      storeConsentPreferences(getConsentRequestPreferencesQueryResult.data);
    }
  }, [
    getConsentRequestPreferencesQueryResult,
    storeConsentPreferences,
    toastError,
    redirectToIndex,
  ]);

  /**
   * Update the consent choices on the backend.
   */
  const saveUserConsentOptions = useCallback(() => {
    const consent = consentOptions.map((option) => {
      const defaultValue = resolveConsentValue(option.default, consentContext);
      const value = fidesKeyToConsent[option.fidesDataUseKey] ?? defaultValue;
      const gpcStatus = getGpcStatus({
        value,
        consentOption: option,
        consentContext,
      });

      return {
        data_use: option.fidesDataUseKey,
        data_use_description: option.description,
        opt_in: value,
        has_gpc_flag: gpcStatus !== GpcStatus.NONE,
        conflicts_with_gpc: gpcStatus === GpcStatus.OVERRIDDEN,
      };
    });

    const executableOptions = consentOptions.map((option) => ({
      data_use: option.fidesDataUseKey,
      executable: option.executable ?? false,
    }));

    const browserIdentity = inspectForBrowserIdentities();

    updateConsentRequestPreferencesMutationTrigger({
      id: consentRequestId,
      body: {
        code: verificationCode,
        policy_key: config.consent?.policy_key,
        consent,
        executable_options: executableOptions,
        browser_identity: browserIdentity,
      },
    });
  }, [
    consentContext,
    consentOptions,
    consentRequestId,
    fidesKeyToConsent,
    updateConsentRequestPreferencesMutationTrigger,
    verificationCode,
  ]);

  /**
   * Handle consent update result.
   */
  useEffect(() => {
    if (updateConsentRequestPreferencesMutationResult.isError) {
      toastError({
        title: "An error occurred while saving user consent preferences",
        error: updateConsentRequestPreferencesMutationResult.error,
      });
      return;
    }

    if (updateConsentRequestPreferencesMutationResult.isSuccess) {
      storeConsentPreferences(
        updateConsentRequestPreferencesMutationResult.data
      );
      toast({
        title: "Your consent preferences have been saved",
        ...SuccessToastOptions,
      });
      redirectToIndex();
    }
  }, [
    updateConsentRequestPreferencesMutationResult,
    storeConsentPreferences,
    toastError,
    toast,
    redirectToIndex,
  ]);

  const items = useMemo(
    () =>
      consentOptions.map((option) => {
        const defaultValue = resolveConsentValue(
          option.default,
          consentContext
        );
        const value = fidesKeyToConsent[option.fidesDataUseKey] ?? defaultValue;
        const gpcStatus = getGpcStatus({
          value,
          consentOption: option,
          consentContext,
        });

        return {
          option,
          value,
          gpcStatus,
        };
      }),
    [consentContext, consentOptions, fidesKeyToConsent]
  );

  return (
    <div>
      <Head>
        <title>Privacy Center</title>
        <meta name="description" content="Privacy Center" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <header>
        <Flex
          bg="gray.100"
          minHeight={14}
          p={1}
          width="100%"
          justifyContent="center"
          alignItems="center"
        >
          <Image
            src={config.logo_path}
            height="68px"
            alt="Logo"
          />
        </Flex>
      </header>

      <Stack as="main" align="center" data-testid="consent">
        <Stack align="center" py={["6", "16"]} spacing={8} maxWidth="720px">
          <Stack align="center" spacing={3}>
            <Heading
              fontSize={["3xl", "4xl"]}
              color="gray.600"
              fontWeight="semibold"
              textAlign="center"
            >
              Manage your consent
            </Heading>
            <Text
              fontSize={["small", "medium"]}
              fontWeight="medium"
              maxWidth="624px"
              textAlign="center"
              color="gray.600"
            >
              When you use our services, you&apos;re trusting us with your
              information. We understand this is a big responsibility and work
              hard to protect your information and put you in control.
            </Text>
          </Stack>

          {consentContext.globalPrivacyControl ? <GpcBanner /> : null}

          <Stack direction="column" spacing={4}>
            {items.map((item, index) => (
              <React.Fragment key={item.option.fidesDataUseKey}>
                {index > 0 ? <Divider /> : null}
                <ConsentItemCard {...item} />
              </React.Fragment>
            ))}

            <Stack
              direction="row"
              justifyContent="flex-start"
              paddingX={12}
              width="full"
            >
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  router.push("/");
                }}
              >
                Cancel
              </Button>
              <Button
                bg="primary.800"
                _hover={{ bg: "primary.400" }}
                _active={{ bg: "primary.500" }}
                colorScheme="primary"
                size="sm"
                onClick={() => {
                  saveUserConsentOptions();
                }}
                data-testid="save-btn"
              >
                Save
              </Button>
            </Stack>
          </Stack>
        </Stack>
      </Stack>
    </div>
  );
};

export default Consent;
