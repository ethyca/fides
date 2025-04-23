/* eslint-disable react/no-array-index-key */
import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/dist/query";
import {
  AntButton as Button,
  Box,
  Flex,
  Spinner,
  Stack,
  Text,
  useToast,
} from "fidesui";
import { Form, Formik } from "formik";
import type { NextPage } from "next";
import { useMemo } from "react";

import { useAppSelector } from "~/app/hooks";
import { useFeatures } from "~/features/common/features";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import { useGetPurposesQuery } from "~/features/common/purpose.slice";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import {
  selectGppSettings,
  selectPlusConsentSettings,
  useGetConfigurationSettingsQuery,
  usePatchConfigurationSettingsMutation,
} from "~/features/config-settings/config-settings.slice";
import DeprecatedPurposeOverrides from "~/features/consent-settings/DeprecatedPurposeOverrides";
import FrameworkStatus from "~/features/consent-settings/FrameworkStatus";
import GppConfiguration from "~/features/consent-settings/GppConfiguration";
import PublisherSettings, {
  TCFPublisherSettings,
} from "~/features/consent-settings/PublisherSettings";
import SettingsBox from "~/features/consent-settings/SettingsBox";
import { PublisherRestrictionsConfig } from "~/features/consent-settings/tcf/PublisherRestrictionsConfig";
import { TCFOverrideToggle } from "~/features/consent-settings/tcf/TCFOverrideToggle";
import {
  useGetHealthQuery,
  useGetTcfPurposeOverridesQuery,
  usePatchTcfPurposeOverridesMutation,
} from "~/features/plus/plus.slice";
import {
  PrivacyExperienceGPPSettings,
  TCFLegalBasisEnum,
  TCFPurposeOverrideSchema,
} from "~/types/api";

type FormPurposeOverride = {
  purpose: number;
  is_included: boolean;
  is_consent: boolean;
  is_legitimate_interest: boolean;
};

type FormValues = {
  purposeOverrides: FormPurposeOverride[];
  gpp: PrivacyExperienceGPPSettings;
  tcfPublisherSettings: TCFPublisherSettings;
};

const ConsentConfigPage: NextPage = () => {
  const { isLoading: isHealthCheckLoading } = useGetHealthQuery();
  const { tcf: isTcfEnabled } = useFeatures();
  const { data: tcfPurposeOverrides, isLoading: isTcfPurposeOverridesLoading } =
    useGetTcfPurposeOverridesQuery(undefined, {
      skip: isHealthCheckLoading || !isTcfEnabled,
    });
  const [
    patchTcfPurposeOverridesTrigger,
    { isLoading: isPatchConfigSettingsLoading },
  ] = usePatchTcfPurposeOverridesMutation();
  const { data: apiConfigSet, isLoading: isApiConfigSetLoading } =
    useGetConfigurationSettingsQuery({ api_set: true });
  const { data: configSet, isLoading: isConfigSetLoading } =
    useGetConfigurationSettingsQuery({ api_set: false });
  const [patchConfigSettingsTrigger] = usePatchConfigurationSettingsMutation();
  const gppSettings = useAppSelector(selectGppSettings);
  const plusConsentSettings = useAppSelector(selectPlusConsentSettings);

  const isTcfOverrideEnabled = useMemo(() => {
    if (
      apiConfigSet &&
      apiConfigSet?.consent &&
      "override_vendor_purposes" in apiConfigSet.consent
    ) {
      return apiConfigSet.consent.override_vendor_purposes;
    }
    if (
      configSet &&
      configSet?.consent &&
      "override_vendor_purposes" in configSet.consent
    ) {
      return configSet.consent.override_vendor_purposes;
    }

    return false;
  }, [apiConfigSet, configSet]);

  const { isLoading: isPurposesLoading } = useGetPurposesQuery();

  const toast = useToast();

  const handleSubmit = async (values: FormValues) => {
    const handleResult = (
      result:
        | { data: object }
        | { error: FetchBaseQueryError | SerializedError },
    ) => {
      toast.closeAll();
      if (isErrorResult(result)) {
        const errorMsg = getErrorMessage(
          result.error,
          `An unexpected error occurred while saving. Please try again.`,
        );
        toast(errorToastParams(errorMsg));
      } else {
        toast(successToastParams("Settings saved successfully"));
      }
    };

    const payload: TCFPurposeOverrideSchema[] = [
      ...values.purposeOverrides.map((po) => {
        let requiredLegalBasis;
        if (po.is_consent) {
          requiredLegalBasis = TCFLegalBasisEnum.CONSENT;
        }

        if (po.is_legitimate_interest) {
          requiredLegalBasis = TCFLegalBasisEnum.LEGITIMATE_INTERESTS;
        }

        return {
          purpose: po.purpose,
          is_included: po.is_included,
          required_legal_basis: requiredLegalBasis,
        };
      }),
    ];

    // Try to patch TCF overrides first
    if (isTcfOverrideEnabled) {
      const result = await patchTcfPurposeOverridesTrigger(payload);
      if (isErrorResult(result)) {
        handleResult(result);
        return;
      }
    }
    // Then we update config values
    // For GPP, do not pass in `enabled`
    const { enabled, ...updatedGpp } = values.gpp;
    const configResult = await patchConfigSettingsTrigger({
      gpp: updatedGpp,
      plus_consent_settings: {
        tcf_publisher_country_code:
          values.tcfPublisherSettings.publisher_country_code ?? null,
      },
    });
    handleResult(configResult);
  };

  const initialValues = useMemo(
    () => ({
      purposeOverrides: tcfPurposeOverrides
        ? tcfPurposeOverrides.map(
            (po) =>
              ({
                purpose: po.purpose,
                is_included: po.is_included,
                is_consent:
                  po.required_legal_basis === TCFLegalBasisEnum.CONSENT,
                is_legitimate_interest:
                  po.required_legal_basis ===
                  TCFLegalBasisEnum.LEGITIMATE_INTERESTS,
              }) as FormPurposeOverride,
          )
        : [],
      gpp: gppSettings,
      tcfPublisherSettings: {
        publisher_country_code: plusConsentSettings.tcf_publisher_country_code,
      },
    }),
    [tcfPurposeOverrides, gppSettings, plusConsentSettings],
  );

  const hasLegacyLegalBasisOverrides = useMemo(() => {
    return (
      isTcfOverrideEnabled &&
      tcfPurposeOverrides?.some(
        (po) =>
          !po.is_included ||
          po.required_legal_basis === TCFLegalBasisEnum.CONSENT ||
          po.required_legal_basis === TCFLegalBasisEnum.LEGITIMATE_INTERESTS,
      )
    );
  }, [tcfPurposeOverrides, isTcfOverrideEnabled]);

  return (
    <Layout title="Consent Configuration">
      {isHealthCheckLoading ||
      isPurposesLoading ||
      isTcfPurposeOverridesLoading ||
      isApiConfigSetLoading ||
      isConfigSetLoading ? (
        <Flex justifyContent="center" alignItems="center" height="100%">
          <Spinner />
        </Flex>
      ) : (
        <Box data-testid="consent-configuration">
          <PageHeader heading="Consent settings" />
          <Stack spacing={3} mb={3}>
            <SettingsBox title="Transparency & Consent Framework settings">
              <FrameworkStatus name="TCF" enabled={isTcfEnabled} />
            </SettingsBox>
            {isTcfEnabled && !hasLegacyLegalBasisOverrides && (
              <PublisherRestrictionsConfig
                isTCFOverrideEnabled={isTcfOverrideEnabled}
              />
            )}
          </Stack>
          <Formik<FormValues>
            initialValues={initialValues}
            enableReinitialize
            onSubmit={handleSubmit}
          >
            {({ dirty, isValid, isSubmitting }) => (
              <Form>
                <Stack spacing={6}>
                  {hasLegacyLegalBasisOverrides && (
                    <SettingsBox title="Vendor overrides" fontSize="sm">
                      <TCFOverrideToggle
                        defaultChecked
                        disabled={isPatchConfigSettingsLoading}
                      />
                      <Stack mt={2} spacing={2}>
                        <Text>
                          The table below allows you to adjust which TCF
                          purposes you allow as part of your user facing notices
                          and business activites.
                        </Text>
                        <Text>
                          To configure this section, select the purposes you
                          allow and where available, the appropriate legal bases
                          (either Consent or Legitimate Interest).
                        </Text>
                        <DeprecatedPurposeOverrides />
                      </Stack>
                    </SettingsBox>
                  )}
                  <PublisherSettings />
                  <GppConfiguration />
                  <Button
                    htmlType="submit"
                    type="primary"
                    disabled={!dirty || !isValid}
                    loading={isSubmitting}
                    data-testid="save-btn"
                    className="self-start"
                  >
                    Save
                  </Button>
                </Stack>
              </Form>
            )}
          </Formik>
        </Box>
      )}
    </Layout>
  );
};
export default ConsentConfigPage;
