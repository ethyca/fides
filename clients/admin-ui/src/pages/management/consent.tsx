/* eslint-disable react/no-array-index-key */
import {
  Box,
  Button,
  Flex,
  Heading,
  Spinner,
  Switch,
  Text,
  useToast,
} from "@fidesui/react";
import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/dist/query";
import { FieldArray, Form, Formik, FormikHelpers } from "formik";
import type { NextPage } from "next";
import { ChangeEvent, FC, useMemo } from "react";

import { useAppSelector } from "~/app/hooks";
import DocsLink from "~/features/common/DocsLink";
import { useFeatures } from "~/features/common/features";
import { CustomSwitch } from "~/features/common/form/inputs";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import Layout from "~/features/common/Layout";
import {
  selectPurposes,
  useGetPurposesQuery,
} from "~/features/common/purpose.slice";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import {
  useGetHealthQuery,
  useGetTcfPurposeOverridesQuery,
  usePatchTcfPurposeOverridesMutation,
} from "~/features/plus/plus.slice";
import {
  useGetConfigurationSettingsQuery,
  usePatchConfigurationSettingsMutation,
} from "~/features/privacy-requests/privacy-requests.slice";
import { TCFLegalBasisEnum, TCFPurposeOverrideSchema } from "~/types/api";

const LegalBasisContainer: FC<{
  purpose: number;
}> = ({ children, purpose }) => {
  const hiddenPurposes = [1, 3, 4, 5, 6];

  return (
    <Flex
      flex="1"
      justifyContent="center"
      alignItems="center"
      borderRight="solid 1px black"
      height="100%"
    >
      {hiddenPurposes.includes(purpose) ? null : <Box>{children}</Box>}
    </Flex>
  );
};

type FormPurposeOverride = {
  purpose: number;
  is_included: boolean;
  is_consent: boolean;
  is_legitimate_interest: boolean;
};

type FormValues = { purposeOverrides: FormPurposeOverride[] };

const ConsentConfigPage: NextPage = () => {
  const { isLoading: isHealthCheckLoading } = useGetHealthQuery();
  const { tcf: isTcfEnabled } = useFeatures();
  const { data: tcfPurposeOverrides, isLoading: isTcfPurposeOverridesLoading } =
    useGetTcfPurposeOverridesQuery(undefined, {
      skip: isHealthCheckLoading || !isTcfEnabled,
    });
  const [
    patchTcfPurposeOverridesTrigger,
    { isLoading: isLoadingPatchMutation },
  ] = usePatchTcfPurposeOverridesMutation();
  const { data: apiConfigSet, isLoading: isApiConfigSetLoading } =
    useGetConfigurationSettingsQuery({ api_set: true });
  const { data: configSet, isLoading: isConfigSetLoading } =
    useGetConfigurationSettingsQuery({ api_set: false });
  const [
    patchConfigSettingsTrigger,
    { isLoading: isPatchConfigSettingsLoading },
  ] = usePatchConfigurationSettingsMutation();

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
  const { purposes: purposeMapping } = useAppSelector(selectPurposes);

  const toast = useToast();

  const handleSubmit = async (
    values: FormValues,
    formikHelpers: FormikHelpers<FormValues>
  ) => {
    const handleResult = (
      result: { data: {} } | { error: FetchBaseQueryError | SerializedError }
    ) => {
      toast.closeAll();
      if (isErrorResult(result)) {
        const errorMsg = getErrorMessage(
          result.error,
          `An unexpected error occurred while saving TCF Purpose Overrides. Please try again.`
        );
        toast(errorToastParams(errorMsg));
      } else {
        toast(successToastParams("TCF Purpose Overrides saved successfully"));
        // Reset state such that isDirty will be checked again before next save
        formikHelpers.resetForm({ values });
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

    const result = await patchTcfPurposeOverridesTrigger(payload);

    handleResult(result);
  };

  const handleOverrideOnChange = async (e: ChangeEvent<HTMLInputElement>) => {
    const handleResult = (
      result: { data: {} } | { error: FetchBaseQueryError | SerializedError }
    ) => {
      toast.closeAll();
      if (isErrorResult(result)) {
        const errorMsg = getErrorMessage(
          result.error,
          `An unexpected error occurred while saving TCF Purpose Override setting. Please try again.`
        );
        toast(errorToastParams(errorMsg));
      }
    };

    const result = await patchConfigSettingsTrigger({
      consent: {
        override_vendor_purposes: e.target.checked,
      },
    });
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
              } as FormPurposeOverride)
          )
        : [],
    }),
    [tcfPurposeOverrides]
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
          <Heading marginBottom={4} fontSize="2xl">
            Global Consent Settings
          </Heading>
          <Box maxWidth="600px">
            <Text marginBottom={2} fontSize="md">
              TCF status: {isTcfEnabled ? "Enabled ✅" : "Disabled ❌"}
            </Text>
            <Text mb={10} fontSize="sm">
              To {isTcfEnabled ? "disable" : "enable"} TCF, please contact your
              Fides Administrator or Ethyca support
            </Text>
            {isTcfEnabled ? (
              <>
                <Text marginBottom={2} fontSize="sm">
                  Override vendor purposes:{" "}
                  <Switch
                    size="sm"
                    colorScheme="purple"
                    isChecked={isOverrideEnabled}
                    onChange={handleOverrideOnChange}
                    isDisabled={isPatchConfigSettingsLoading}
                  />
                </Text>
                <Text mb={2} fontSize="sm" fontStyle="italic">
                  {isOverrideEnabled
                    ? "The table below allows you to adjust which TCF purposes you allow as part of your user facing notices and business activites."
                    : "Toggle on if you want to globally change any flexiable legal bases or remove TCF purposes from your CMP."}
                </Text>
              </>
            ) : null}
            {isOverrideEnabled && isTcfEnabled ? (
              <Text marginBottom={10} fontSize="sm">
                To configure this section, select the purposes you allow and
                where available, the appropriate legal basis (either Consent or
                Legitmate Intererest). Read the guide on{" "}
                <DocsLink href="https://ethyca.com">
                  {" "}
                  TCF Override here.{" "}
                </DocsLink>
              </Text>
            ) : null}
          </Box>

          {isOverrideEnabled ? (
            <Box>
              <Formik<FormValues>
                initialValues={initialValues}
                enableReinitialize
                onSubmit={handleSubmit}
              >
                {({ values, dirty, isValid, setFieldValue }) => (
                  <Form>
                    <FieldArray
                      name="purposeOverrides"
                      render={() => (
                        <Flex flexDirection="column">
                          <Flex width="100%" borderBottom="solid 1px black">
                            <Box width="600px" />
                            <Flex
                              flex="1"
                              justifyContent="center"
                              alignItems="center"
                            >
                              <Text>Include in CMP</Text>
                            </Flex>
                            <Flex
                              flex="1"
                              justifyContent="center"
                              alignItems="center"
                            >
                              <Text>Require Consent</Text>
                            </Flex>
                            <Flex
                              flex="1"
                              justifyContent="center"
                              alignItems="center"
                            >
                              <Text>Use Legitmate Interest</Text>
                            </Flex>
                          </Flex>
                          {values.purposeOverrides.map((po, index) => (
                            <Flex
                              key={po.purpose}
                              width="100%"
                              height="40px"
                              alignItems="center"
                            >
                              <Flex
                                width="600px"
                                borderRight="solid 1px black"
                                p={0}
                                alignItems="center"
                                height="100%"
                              >
                                Purpose {po.purpose}:{" "}
                                {purposeMapping[po.purpose].name}
                              </Flex>

                              <Flex
                                flex="1"
                                justifyContent="center"
                                alignItems="center"
                                borderRight="solid 1px black"
                                height="100%"
                              >
                                <Box>
                                  <CustomSwitch
                                    name={`purposeOverrides[${index}].is_included`}
                                    onChange={(
                                      e: ChangeEvent<HTMLInputElement>
                                    ) => {
                                      if (!e.target.checked) {
                                        setFieldValue(
                                          `purposeOverrides[${index}].is_consent`,
                                          false
                                        );
                                        setFieldValue(
                                          `purposeOverrides[${index}].is_legitimate_interest`,
                                          false
                                        );
                                      }
                                    }}
                                  />
                                </Box>
                              </Flex>
                              <LegalBasisContainer purpose={po.purpose}>
                                <CustomSwitch
                                  isDisabled={
                                    !values.purposeOverrides[index]
                                      .is_included ||
                                    values.purposeOverrides[index]
                                      .is_legitimate_interest
                                  }
                                  name={`purposeOverrides[${index}].is_consent`}
                                />
                              </LegalBasisContainer>
                              <LegalBasisContainer purpose={po.purpose}>
                                <CustomSwitch
                                  isDisabled={
                                    !values.purposeOverrides[index]
                                      .is_included ||
                                    values.purposeOverrides[index].is_consent
                                  }
                                  name={`purposeOverrides[${index}].is_legitimate_interest`}
                                />
                              </LegalBasisContainer>
                            </Flex>
                          ))}
                        </Flex>
                      )}
                    />
                    <Box mt={6}>
                      <Button
                        type="submit"
                        variant="primary"
                        size="sm"
                        isDisabled={
                          isLoadingPatchMutation || !dirty || !isValid
                        }
                        isLoading={isLoadingPatchMutation}
                        data-testid="save-btn"
                      >
                        Save
                      </Button>
                    </Box>
                  </Form>
                )}
              </Formik>
            </Box>
          ) : null}
        </Box>
      )}
    </Layout>
  );
};
export default ConsentConfigPage;
