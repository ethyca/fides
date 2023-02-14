import {
  Button,
  Flex,
  Heading,
  Image,
  Stack,
  Text,
  useToast,
} from "@fidesui/react";
import produce from "immer";
import type { NextPage } from "next";
import Head from "next/head";
import { useRouter } from "next/router";
import React, { useCallback, useEffect, useState } from "react";

import { setConsentCookie } from "fides-consent";
import { useAppSelector } from "~/app/hooks";
import { inspectForBrowserIdentities } from "~/common/browser-identities";
import { useLocalStorage } from "~/common/hooks";
import { ErrorToastOptions, SuccessToastOptions } from "~/common/toast-options";
import ConsentItemCard from "~/components/ConsentItemCard";
import { config } from "~/constants";
import { selectConfigConsentOptions } from "~/features/common/config.slice";
import {
  useLazyGetConsentRequestPreferencesQuery,
  usePostConsentRequestVerificationMutation,
  useUpdateConsentRequestPreferencesMutation,
} from "~/features/consent/consent.slice";
import {
  makeConsentItems,
  makeCookieKeyConsent,
} from "~/features/consent/helpers";
import { ApiUserConsents, ConsentItem } from "~/features/consent/types";
import { useGetIdVerificationConfigQuery } from "~/features/id-verification";

const Consent: NextPage = () => {
  const [consentRequestId] = useLocalStorage("consentRequestId", "");
  const [verificationCode] = useLocalStorage("verificationCode", "");
  const router = useRouter();
  const toast = useToast();
  const [consentItems, setConsentItems] = useState<ConsentItem[]>([]);
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

  const updateConsentItems = useCallback(
    (data: ApiUserConsents) => {
      const updatedConsentItems = makeConsentItems(data, consentOptions);
      setConsentItems(updatedConsentItems);
      setConsentCookie(makeCookieKeyConsent(updatedConsentItems));
    },
    [consentOptions]
  );

  /**
   * Set the consent value for an option in the `consentItems` array. We're storing a whole array in
   * the state, so we need to use `produce` to modify a single property but still get a new object
   * that works with React rendering.
   */
  const setConsentValue = useCallback(
    (item: ConsentItem, value: boolean) => {
      const updatedConsentItems = produce(consentItems, (draftItems) => {
        const itemToUpdate = draftItems.find(
          (candidate) => candidate.fidesDataUseKey === item.fidesDataUseKey
        );
        if (!itemToUpdate) {
          return;
        }
        itemToUpdate.consentValue = value;
      });
      setConsentItems(updatedConsentItems);
    },
    [consentItems]
  );

  /**
   * When the Id verification method is known, trigger the request that will
   * return the consent choices saved on the backend.
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
      updateConsentItems(postConsentRequestVerificationMutationResult.data);
    }
  }, [
    postConsentRequestVerificationMutationResult,
    updateConsentItems,
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
      updateConsentItems(getConsentRequestPreferencesQueryResult.data);
    }
  }, [
    getConsentRequestPreferencesQueryResult,
    updateConsentItems,
    toastError,
    redirectToIndex,
  ]);

  /**
   * Update the consent choices on the backend.
   */
  const saveUserConsentOptions = useCallback(() => {
    const consent = consentItems.map((d) => ({
      data_use: d.fidesDataUseKey,
      data_use_description: d.description,
      opt_in: Boolean(d.consentValue),
    }));

    const executableOptions = consentItems.map((d) => ({
      data_use: d.fidesDataUseKey,
      executable: d.executable ?? false,
    }));

    const browserIdentity = inspectForBrowserIdentities();
    const browserIdentityBody = browserIdentity
      ? { ga_client_id: browserIdentity.gaClientId }
      : undefined;

    updateConsentRequestPreferencesMutationTrigger({
      id: consentRequestId,
      body: {
        code: verificationCode,
        policy_key: config.consent?.policy_key,
        consent,
        executable_options: executableOptions,
        browser_identity: browserIdentityBody,
      },
    });
  }, [
    consentItems,
    consentRequestId,
    verificationCode,
    updateConsentRequestPreferencesMutationTrigger,
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
      updateConsentItems(updateConsentRequestPreferencesMutationResult.data);
      toast({
        title: "Your consent preferences have been saved",
        ...SuccessToastOptions,
      });
      redirectToIndex();
    }
  }, [
    updateConsentRequestPreferencesMutationResult,
    updateConsentItems,
    toastError,
    toast,
    redirectToIndex,
  ]);

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
            height="56px"
            width="304px"
            alt="Logo"
          />
        </Flex>
      </header>

      <main data-testid="consent">
        <Stack align="center" py={["6", "16"]} px={5} spacing={8}>
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
              maxWidth={624}
              textAlign="center"
              color="gray.600"
            >
              When you use our services, you’re trusting us with your
              information. We understand this is a big responsibility and work
              hard to protect your information and put you in control.
            </Text>
          </Stack>

          <Flex m={-2} flexDirection="column">
            {consentItems.map((item) => (
              <ConsentItemCard
                key={item.fidesDataUseKey}
                item={item}
                setConsentValue={(value) => {
                  setConsentValue(item, value);
                }}
              />
            ))}
          </Flex>

          <Stack direction="row" justifyContent="flex-start" width="720px">
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
      </main>
    </div>
  );
};

export default Consent;
