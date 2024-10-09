import {
  FidesCookie,
  getConsentContext,
  getOrMakeFidesCookie,
  GpcStatus,
  resolveLegacyConsentValue,
  saveFidesCookie,
} from "fides-js";
import { Divider, Stack, useToast } from "fidesui";
import { useRouter } from "next/router";
import React, { useCallback, useEffect, useMemo } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import { inspectForBrowserIdentities } from "~/common/browser-identities";
import { useLocalStorage } from "~/common/hooks";
import { ErrorToastOptions, SuccessToastOptions } from "~/common/toast-options";
import { useConfig } from "~/features/common/config.slice";
import {
  changeConsent,
  selectFidesKeyToConsent,
  useUpdateConsentRequestPreferencesDeprecatedMutation,
} from "~/features/consent/consent.slice";
import { getGpcStatus, makeNoticeConsent } from "~/features/consent/helpers";
import { ConsentMethod, ConsentPreferences } from "~/types/api";

import ConsentItem from "./ConsentItem";
import SaveCancel from "./SaveCancel";

const ConfigDrivenConsent = ({
  storePreferences,
  base64Cookie,
}: {
  storePreferences: (data: ConsentPreferences) => void;
  base64Cookie: boolean;
}) => {
  const config = useConfig();
  const consentOptions = useMemo(
    () => config.consent?.page.consentOptions ?? [],
    [config],
  );
  const toast = useToast();
  const router = useRouter();
  const dispatch = useAppDispatch();
  const consentContext = useMemo(() => getConsentContext(), []);
  const fidesKeyToConsent = useAppSelector(selectFidesKeyToConsent);
  const [consentRequestId] = useLocalStorage("consentRequestId", "");
  const [verificationCode] = useLocalStorage("verificationCode", "");
  const [
    updateConsentRequestPreferencesMutationTrigger,
    updateConsentRequestPreferencesMutationResult,
  ] = useUpdateConsentRequestPreferencesDeprecatedMutation();

  /**
   * Update the consent choices on the backend.
   */
  const saveUserConsentOptions = useCallback(() => {
    const newConsent = makeNoticeConsent({
      consentOptions,
      fidesKeyToConsent,
      consentContext,
    });
    const consent = consentOptions.map((option) => {
      const defaultValue = resolveLegacyConsentValue(
        option.default!,
        consentContext,
      );
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
    const cookie: FidesCookie = getOrMakeFidesCookie();
    cookie.fides_meta.consentMethod = ConsentMethod.SAVE; // include the consentMethod as extra metadata
    saveFidesCookie({ ...cookie, consent: newConsent }, base64Cookie);

    const executableOptions = consentOptions.map((option) => ({
      data_use: option.fidesDataUseKey,
      executable: option.executable ?? false,
    }));

    const browserIdentity = inspectForBrowserIdentities();

    updateConsentRequestPreferencesMutationTrigger({
      id: consentRequestId,
      body: {
        code: verificationCode,
        policy_key: config.consent?.page.policy_key,
        consent,
        executable_options: executableOptions,
        browser_identity: browserIdentity,
      },
    });
  }, [
    config,
    consentContext,
    consentOptions,
    consentRequestId,
    fidesKeyToConsent,
    updateConsentRequestPreferencesMutationTrigger,
    verificationCode,
    base64Cookie,
  ]);

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

  useEffect(() => {
    if (updateConsentRequestPreferencesMutationResult.isError) {
      toastError({
        title: "An error occurred while saving user consent preferences",
        error: updateConsentRequestPreferencesMutationResult.error,
      });
      return;
    }

    if (updateConsentRequestPreferencesMutationResult.isSuccess) {
      storePreferences(updateConsentRequestPreferencesMutationResult.data);
      toast({
        title: "Your consent preferences have been saved",
        ...SuccessToastOptions,
      });
      router.push("/");
    }
  }, [
    updateConsentRequestPreferencesMutationResult,
    storePreferences,
    toastError,
    toast,
    router,
  ]);

  const handleCancel = () => {
    router.push("/");
  };

  const items = useMemo(
    () =>
      consentOptions.map((option) => {
        const defaultValue = resolveLegacyConsentValue(
          option.default!,
          consentContext,
        );
        const value = fidesKeyToConsent[option.fidesDataUseKey] ?? defaultValue;
        const gpcStatus = getGpcStatus({
          value,
          consentOption: option,
          consentContext,
        });

        return {
          ...option,
          value,
          gpcStatus,
        };
      }),
    [consentContext, consentOptions, fidesKeyToConsent],
  );

  return (
    <Stack spacing={4} paddingX={12}>
      {items.map((item, index) => {
        const { fidesDataUseKey, highlight, url, name, description } = item;
        const handleChange = (value: boolean) => {
          dispatch(changeConsent({ key: fidesDataUseKey, value }));
        };
        return (
          <React.Fragment key={fidesDataUseKey}>
            {index > 0 ? <Divider /> : null}
            <ConsentItem
              id={fidesDataUseKey}
              name={name}
              description={description}
              highlight={highlight}
              url={url}
              value={item.value}
              gpcStatus={item.gpcStatus}
              onChange={handleChange}
            />
          </React.Fragment>
        );
      })}
      <SaveCancel
        onSave={saveUserConsentOptions}
        onCancel={handleCancel}
        cancelLabel="Cancel"
        saveLabel="Save"
      />
    </Stack>
  );
};

export default ConfigDrivenConsent;
