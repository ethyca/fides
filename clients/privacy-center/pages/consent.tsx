import { Stack, useToast } from "@fidesui/react";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import React, { useCallback, useEffect, useMemo } from "react";

import {
  FidesCookie,
  getConsentContext,
  saveFidesCookie,
  getOrMakeFidesCookie,
} from "fides-js";
import { useAppDispatch, useAppSelector } from "~/app/hooks";

import { useLocalStorage } from "~/common/hooks";
import { ErrorToastOptions } from "~/common/toast-options";
import {
  updateConsentOptionsFromApi,
  useConfig,
} from "~/features/common/config.slice";
import {
  selectPersistedFidesKeyToConsent,
  updateUserConsentPreferencesFromApi,
  useLazyGetConsentRequestPreferencesQuery,
  usePostConsentRequestVerificationMutation,
} from "~/features/consent/consent.slice";
import { makeCookieKeyConsent } from "~/features/consent/helpers";
import { useGetIdVerificationConfigQuery } from "~/features/id-verification";
import { ConsentPreferences } from "~/types/api";
import { GpcBanner } from "~/features/consent/GpcMessages";
import ConsentToggles from "~/components/consent/ConsentToggles";
import { useSubscribeToPrivacyExperienceQuery } from "~/features/consent/hooks";
import ConsentHeading from "~/components/consent/ConsentHeading";
import ConsentDescription from "~/components/consent/ConsentDescription";
import { selectIsNoticeDriven } from "~/features/common/settings.slice";

const Consent: NextPage = () => {
  const [consentRequestId] = useLocalStorage("consentRequestId", "");
  const [verificationCode] = useLocalStorage("verificationCode", "");
  const router = useRouter();
  const toast = useToast();
  const dispatch = useAppDispatch();
  const persistedFidesKeyToConsent = useAppSelector(
    selectPersistedFidesKeyToConsent
  );
  const config = useConfig();
  const consentOptions = useMemo(
    () => config.consent?.page.consentOptions ?? [],
    [config]
  );
  useSubscribeToPrivacyExperienceQuery();

  const getIdVerificationConfigQueryResult = useGetIdVerificationConfigQuery();
  const [
    postConsentRequestVerificationMutationTrigger,
    postConsentRequestVerificationMutationResult,
  ] = usePostConsentRequestVerificationMutation();
  const [
    getConsentRequestPreferencesQueryTrigger,
    getConsentRequestPreferencesQueryResult,
  ] = useLazyGetConsentRequestPreferencesQuery();
  const isNoticeDriven = useAppSelector(selectIsNoticeDriven);

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
      dispatch(updateUserConsentPreferencesFromApi(data));
    },
    [dispatch]
  );

  /**
   * The consent cookie is updated only when the "persisted" consent preferences are updated. This
   * ensures the browser's behavior matches what the server expects.
   *
   * Notice driven consent does not need to set a new consent object
   */
  useEffect(() => {
    const cookie: FidesCookie = getOrMakeFidesCookie();
    if (isNoticeDriven) {
      saveFidesCookie(cookie);
    } else {
      const newConsent = makeCookieKeyConsent({
        consentOptions,
        fidesKeyToConsent: persistedFidesKeyToConsent,
        consentContext,
      });
      saveFidesCookie({ ...cookie, consent: newConsent });
    }
  }, [
    consentOptions,
    persistedFidesKeyToConsent,
    consentContext,
    isNoticeDriven,
  ]);

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

  return (
    <Stack as="main" align="center" data-testid="consent">
      <Stack align="center" py={["6", "16"]} spacing={8} maxWidth="720px">
        <Stack align="center" spacing={3}>
          <ConsentHeading />
          <ConsentDescription />
        </Stack>
        {consentContext.globalPrivacyControl ? <GpcBanner /> : null}
        <ConsentToggles storePreferences={storeConsentPreferences} />
      </Stack>
    </Stack>
  );
};

export default Consent;
