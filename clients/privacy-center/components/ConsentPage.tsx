"use client";

import {
  FidesCookie,
  getConsentContext,
  getOrMakeFidesCookie,
  initializeI18n,
  loadMessagesFromFiles,
  PrivacyExperience,
  saveFidesCookie,
  setupI18n,
} from "fides-js";
import { Stack, useToast } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/navigation";
import React, { useCallback, useEffect, useMemo, useState } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import { useLocalStorage } from "~/common/hooks";
import useI18n from "~/common/hooks/useI18n";
import { ErrorToastOptions } from "~/common/toast-options";
import ConsentDescription from "~/components/consent/ConsentDescription";
import ConsentHeading from "~/components/consent/ConsentHeading";
import ConsentToggles from "~/components/consent/ConsentToggles";
import {
  updateConsentOptionsFromApi,
  useConfig,
} from "~/features/common/config.slice";
import {
  selectIsNoticeDriven,
  useSettings,
} from "~/features/common/settings.slice";
import {
  selectPersistedFidesKeyToConsent,
  selectPrivacyExperience,
  updateUserConsentPreferencesFromApi,
  useLazyGetConsentRequestPreferencesQuery,
  usePostConsentRequestVerificationMutation,
} from "~/features/consent/consent.slice";
import { GpcBanner } from "~/features/consent/GpcMessages";
import { useSubscribeToPrivacyExperienceQuery } from "~/features/consent/hooks";
import { useGetIdVerificationConfigQuery } from "~/features/id-verification";
import { ConsentPreferences } from "~/types/api";

const ConsentPage: NextPage = () => {
  const settings = useSettings();
  const { BASE_64_COOKIE } = settings;
  const [consentRequestId] = useLocalStorage("consentRequestId", "");
  const [verificationCode] = useLocalStorage("verificationCode", "");
  const router = useRouter();
  const toast = useToast();
  const dispatch = useAppDispatch();
  const persistedFidesKeyToConsent = useAppSelector(
    selectPersistedFidesKeyToConsent,
  );
  const config = useConfig();
  const consentOptions = useMemo(
    () => config.consent?.page.consentOptions ?? [],
    [config],
  );
  const { setI18nInstance } = useI18n();
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
    [toast],
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
    [dispatch],
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
      saveFidesCookie(cookie, BASE_64_COOKIE);
    }
  }, [
    consentOptions,
    persistedFidesKeyToConsent,
    consentContext,
    isNoticeDriven,
    BASE_64_COOKIE,
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
      !privacyCenterConfig.disable_consent_identity_verification &&
      !verificationCode
    ) {
      toastError({ title: "Identity verification is required." });
      redirectToIndex();
      return;
    }

    if (!privacyCenterConfig.disable_consent_identity_verification) {
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
        postConsentRequestVerificationMutationResult.data,
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
   * Initialize internalization library.
   */
  const experience = useAppSelector(selectPrivacyExperience);
  const { IS_OVERLAY_ENABLED } = settings;
  const isConfigDrivenConsent = !IS_OVERLAY_ENABLED;
  const [isI18nInitialized, setIsI18nInitialized] = useState(false);

  useEffect(() => {
    const i18n = setupI18n();

    // 1. Config driven consent
    if (isConfigDrivenConsent) {
      // If we're in config driven consent then
      // still load the static messages in order to have default english
      // messages available
      loadMessagesFromFiles(i18n);
      setI18nInstance(i18n);
      setIsI18nInitialized(true);
      return;
    }

    // 2. Notice driven consent
    if (!experience) {
      return;
    }

    initializeI18n(
      i18n,
      window?.navigator,
      experience as PrivacyExperience,
      {
        debug: process.env.NODE_ENV === "development",
      },
      {},
    );

    setI18nInstance(i18n);
    setIsI18nInitialized(true);
  }, [experience, setI18nInstance, isConfigDrivenConsent]);

  return (
    <Stack as="main" align="center" data-testid="consent">
      {/* Wait until i18n is initalized so we can diplay the correct language and
       also we can use the correct history ids */}
      {isI18nInitialized && (
        <Stack
          align="center"
          py={["6", "16"]}
          spacing={8}
          maxWidth="720px"
          px={[4, 6, 0]}
        >
          <Stack align="center" spacing={3}>
            <ConsentHeading />
            <ConsentDescription />
          </Stack>
          {consentContext.globalPrivacyControl ? <GpcBanner /> : null}
          <ConsentToggles storePreferences={storeConsentPreferences} />
        </Stack>
      )}
    </Stack>
  );
};

export default ConsentPage;
