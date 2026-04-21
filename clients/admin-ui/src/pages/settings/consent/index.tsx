import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/query";
import { Button, Flex, Form, Input, Spin, useMessage } from "fidesui";
import isEqual from "lodash/isEqual";
import type { NextPage } from "next";
import { useEffect, useMemo, useState } from "react";

import { useAppSelector } from "~/app/hooks";
import { useFeatures } from "~/features/common/features";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import { useGetPurposesQuery } from "~/features/common/purpose.slice";
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

  const message = useMessage();
  const [form] = Form.useForm<FormValues>();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (values: FormValues) => {
    setIsSubmitting(true);
    try {
      const handleResult = (
        result:
          | { data: object }
          | { error: FetchBaseQueryError | SerializedError },
      ) => {
        if (isErrorResult(result)) {
          const errorMsg = getErrorMessage(
            result.error,
            `An unexpected error occurred while saving. Please try again.`,
          );
          message.error(errorMsg);
        } else {
          message.success("Settings saved successfully");
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
    } finally {
      setIsSubmitting(false);
    }
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

  const allValues = Form.useWatch([], form);
  const [submittable, setSubmittable] = useState(false);

  useEffect(() => {
    form
      .validateFields({ validateOnly: true })
      .then(() => setSubmittable(true))
      .catch(() => setSubmittable(false));
  }, [form, allValues]);

  const isDirty = useMemo(
    () => (!allValues ? false : !isEqual(allValues, initialValues)),
    [allValues, initialValues],
  );

  const hasLegacyLegalBasisOverrides = useMemo(() => {
    return (
      tcfPurposeOverrides?.some(
        (po) =>
          !po.is_included ||
          po.required_legal_basis === TCFLegalBasisEnum.CONSENT ||
          po.required_legal_basis === TCFLegalBasisEnum.LEGITIMATE_INTERESTS,
      ) || false
    );
  }, [tcfPurposeOverrides]);

  const isPublisherRestrictionsFlagEnabled =
    useFeatures()?.flags?.publisherRestrictions;

  // Stable key for reinitialize behavior
  const formKey = useMemo(() => JSON.stringify(initialValues), [initialValues]);

  return (
    <Layout title="Consent Configuration">
      {isHealthCheckLoading ||
      isPurposesLoading ||
      isTcfPurposeOverridesLoading ||
      isApiConfigSetLoading ||
      isConfigSetLoading ? (
        <Spin />
      ) : (
        <div data-testid="consent-configuration">
          <PageHeader heading="Consent settings" />
          <Flex vertical gap="middle" className="mb-3">
            <SettingsBox title="Transparency & Consent Framework settings">
              <FrameworkStatus name="TCF" enabled={isTcfEnabled} />
            </SettingsBox>
            {/* New publisher restrictions configuration */}
            {isTcfEnabled &&
              !hasLegacyLegalBasisOverrides &&
              isPublisherRestrictionsFlagEnabled && (
                <PublisherRestrictionsConfig
                  isTCFOverrideEnabled={isTcfOverrideEnabled}
                />
              )}
          </Flex>
          <Form<FormValues>
            form={form}
            layout="vertical"
            onFinish={handleSubmit}
            initialValues={initialValues}
            key={formKey}
          >
            {/* Hidden fields for values managed imperatively by child components */}
            <Form.Item name="purposeOverrides" hidden noStyle>
              <Input />
            </Form.Item>
            <Form.Item name={["gpp", "enabled"]} hidden noStyle>
              <Input />
            </Form.Item>
            <Form.Item
              name={["tcfPublisherSettings", "publisher_country_code"]}
              hidden
              noStyle
            >
              <Input />
            </Form.Item>
            <Flex vertical gap="large">
              {/* Legacy vendor overrides */}
              {isTcfEnabled &&
                (hasLegacyLegalBasisOverrides ||
                  !isPublisherRestrictionsFlagEnabled) && (
                  <SettingsBox title="Vendor overrides">
                    <TCFOverrideToggle
                      defaultChecked={isTcfOverrideEnabled}
                      disabled={isPatchConfigSettingsLoading}
                    />
                    {isTcfOverrideEnabled && (
                      <Flex vertical gap="small" className="mt-2">
                        <p>
                          The table below allows you to adjust which TCF
                          purposes you allow as part of your user facing notices
                          and business activites.
                        </p>
                        <p>
                          To configure this section, select the purposes you
                          allow and where available, the appropriate legal bases
                          (either Consent or Legitimate Interest).
                        </p>
                        <DeprecatedPurposeOverrides />
                      </Flex>
                    )}
                  </SettingsBox>
                )}
              <PublisherSettings />
              <GppConfiguration />
              <Button
                htmlType="submit"
                type="primary"
                disabled={!isDirty || !submittable}
                loading={isSubmitting}
                data-testid="save-btn"
                className="self-start"
              >
                Save
              </Button>
            </Flex>
          </Form>
        </div>
      )}
    </Layout>
  );
};
export default ConsentConfigPage;
