/* eslint-disable react/no-array-index-key */
import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/dist/query";
import {
  AntButton as Button,
  AntSwitch as Switch,
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
import DocsLink from "~/features/common/DocsLink";
import { useFeatures } from "~/features/common/features";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import { useGetPurposesQuery } from "~/features/common/purpose.slice";
import QuestionTooltip from "~/features/common/QuestionTooltip";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import {
  selectGppSettings,
  useGetConfigurationSettingsQuery,
  usePatchConfigurationSettingsMutation,
} from "~/features/config-settings/config-settings.slice";
import FrameworkStatus from "~/features/consent-settings/FrameworkStatus";
import GppConfiguration from "~/features/consent-settings/GppConfiguration";
import PurposeOverrides from "~/features/consent-settings/PurposeOverrides";
import SettingsBox from "~/features/consent-settings/SettingsBox";
import {
  useGetHealthQuery,
  useGetTcfPurposeOverridesQuery,
  usePatchTcfPurposeOverridesMutation,
} from "~/features/plus/plus.slice";
import {
  PrivacyExperienceGPPSettings,
  TCFLegalBasisEnum,
  TCFPublisherSettings,
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
  const [patchTcfPurposeOverridesTrigger] =
    usePatchTcfPurposeOverridesMutation();
  const { data: apiConfigSet, isLoading: isApiConfigSetLoading } =
    useGetConfigurationSettingsQuery({ api_set: true });
  const { data: configSet, isLoading: isConfigSetLoading } =
    useGetConfigurationSettingsQuery({ api_set: false });
  const [
    patchConfigSettingsTrigger,
    { isLoading: isPatchConfigSettingsLoading },
  ] = usePatchConfigurationSettingsMutation();
  const gppSettings = useAppSelector(selectGppSettings);

  const isOverrideEnabled = useMemo(() => {
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
    if (isOverrideEnabled) {
      const result = await patchTcfPurposeOverridesTrigger(payload);
      if (isErrorResult(result)) {
        handleResult(result);
        return;
      }
    }
    // Then do GPP (do not pass in `enabled`)
    const { enabled, ...updatedGpp } = values.gpp;
    const gppResult = await patchConfigSettingsTrigger({ gpp: updatedGpp });
    handleResult(gppResult);
  };

  const handleOverrideOnChange = async (checked: boolean) => {
    const handleResult = (
      result:
        | { data: object }
        | { error: FetchBaseQueryError | SerializedError },
    ) => {
      toast.closeAll();
      if (isErrorResult(result)) {
        const errorMsg = getErrorMessage(
          result.error,
          `An unexpected error occurred while saving vendor override settings. Please try again.`,
        );
        toast(errorToastParams(errorMsg));
      }
    };

    const result = await patchConfigSettingsTrigger({
      consent: {
        override_vendor_purposes: checked,
      },
    });

    if (checked) {
      await patchTcfPurposeOverridesTrigger(
        tcfPurposeOverrides!.map((po) => ({
          ...po,
          is_included: true,
          required_legal_basis: undefined,
        })),
      );
    }

    handleResult(result);
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
      tcfPublisherSettings: {},
    }),
    [tcfPurposeOverrides, gppSettings],
  );

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

            <SettingsBox title="Vendor overrides">
              {isTcfEnabled ? (
                <>
                  <Text
                    mb={2}
                    fontSize="sm"
                    lineHeight="5"
                    fontWeight="medium"
                    color="gray.700"
                  >
                    Configure overrides for TCF related purposes.
                  </Text>
                  <Flex alignItems="center" marginBottom={2}>
                    <Switch
                      size="small"
                      checked={isOverrideEnabled}
                      onChange={handleOverrideOnChange}
                      disabled={isPatchConfigSettingsLoading}
                    />
                    <Text
                      px={2}
                      fontSize="sm"
                      lineHeight="5"
                      fontWeight="medium"
                      color="gray.700"
                    >
                      Override vendor purposes
                    </Text>
                    <QuestionTooltip label="Toggle on if you want to globally change any flexible legal bases or remove TCF purposes from your CMP" />
                  </Flex>
                  <Text
                    mb={2}
                    fontSize="sm"
                    lineHeight="5"
                    fontWeight="medium"
                    color="gray.700"
                  >
                    {isOverrideEnabled
                      ? "The table below allows you to adjust which TCF purposes you allow as part of your user facing notices and business activites."
                      : null}
                  </Text>
                </>
              ) : null}
              {isOverrideEnabled && isTcfEnabled ? (
                <Text
                  fontSize="sm"
                  lineHeight="5"
                  fontWeight="medium"
                  color="gray.700"
                >
                  To configure this section, select the purposes you allow and
                  where available, the appropriate legal bases (either Consent
                  or Legitimate Interest).{" "}
                  <DocsLink href="https://fid.es/tcf-overrides">
                    Read the guide on vendor overrides here.{" "}
                  </DocsLink>
                </Text>
              ) : null}
            </SettingsBox>
          </Stack>
          <Formik<FormValues>
            initialValues={initialValues}
            enableReinitialize
            onSubmit={handleSubmit}
          >
            {({ dirty, isValid, isSubmitting }) => (
              <Form>
                <Stack spacing={6}>
                  {isOverrideEnabled ? <PurposeOverrides /> : null}
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
