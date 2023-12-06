/* eslint-disable react/no-array-index-key */
import {
  Badge,
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
import QuestionTooltip from "~/features/common/QuestionTooltip";
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
  endCol?: boolean;
}> = ({ children, purpose, endCol }) => {
  const hiddenPurposes = [1, 3, 4, 5, 6];

  return (
    <Flex
      flex="1"
      justifyContent="center"
      alignItems="center"
      borderLeft="solid 1px"
      borderRight={endCol ? "solid 1px" : "unset"}
      borderColor="gray.200"
      height="100%"
      minWidth="36px"
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
          `An unexpected error occurred while saving vendor override settings. Please try again.`
        );
        toast(errorToastParams(errorMsg));
      }
    };

    const result = await patchConfigSettingsTrigger({
      consent: {
        override_vendor_purposes: e.target.checked,
      },
    });

    if (e.target.checked) {
      await patchTcfPurposeOverridesTrigger(
        tcfPurposeOverrides!.map((po) => ({
          ...po,
          is_included: true,
          required_legal_basis: undefined,
        }))
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
            Consent settings
          </Heading>
          <Box>
            <Box backgroundColor="gray.50" borderRadius="4px" padding="14px">
              <Text
                fontSize="md"
                fontWeight="bold"
                lineHeight={5}
                color="gray.700"
              >
                Transparency & Consent Framework settings
              </Text>
              <Text
                mb={2}
                mt={3}
                fontSize="sm"
                lineHeight="5"
                fontWeight="medium"
                color="gray.700"
              >
                TCF status{" "}
                {isTcfEnabled ? (
                  <Badge backgroundColor="green.100">Enabled </Badge>
                ) : (
                  <Badge backgroundColor="red.100">Disabled</Badge>
                )}
              </Text>
              <Text
                fontSize="sm"
                lineHeight="5"
                fontWeight="medium"
                color="gray.700"
              >
                To {isTcfEnabled ? "disable" : "enable"} TCF, please contact
                your Fides administrator or{" "}
                <DocsLink href="mailto:support@ethyca.com">
                  Ethyca support
                </DocsLink>
                .
              </Text>
            </Box>

            <Box
              mt="24px"
              backgroundColor="gray.50"
              borderRadius="4px"
              padding="14px"
            >
              <Text
                fontSize="md"
                fontWeight="bold"
                lineHeight={5}
                color="gray.700"
                mb={3}
              >
                Vendor overrides
              </Text>
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
                      size="sm"
                      colorScheme="purple"
                      isChecked={isOverrideEnabled}
                      onChange={handleOverrideOnChange}
                      isDisabled={isPatchConfigSettingsLoading}
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
            </Box>
          </Box>

          {isOverrideEnabled ? (
            <Box mt={4}>
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
                        <Flex flexDirection="column" minWidth="944px">
                          <Flex
                            width="100%"
                            border="solid 1px"
                            borderColor="gray.200"
                            backgroundColor="gray.50"
                            height="36px"
                          >
                            <Flex
                              width="600px"
                              pl="4"
                              fontSize="xs"
                              fontWeight="medium"
                              lineHeight="4"
                              alignItems="center"
                              borderRight="solid 1px"
                              borderColor="gray.200"
                            >
                              TCF purpose
                            </Flex>
                            <Flex
                              flex="1"
                              alignItems="center"
                              borderRight="solid 1px"
                              borderColor="gray.200"
                              minWidth="36px"
                            >
                              <Text
                                pl="4"
                                fontSize="xs"
                                fontWeight="medium"
                                lineHeight="4"
                              >
                                Allowed
                              </Text>
                            </Flex>
                            <Flex
                              flex="1"
                              alignItems="center"
                              borderRight="solid 1px"
                              borderColor="gray.200"
                            >
                              <Text
                                pl="4"
                                fontSize="xs"
                                fontWeight="medium"
                                lineHeight="4"
                              >
                                Consent
                              </Text>
                            </Flex>
                            <Flex flex="1" alignItems="center">
                              <Text
                                pl="4"
                                fontSize="xs"
                                fontWeight="medium"
                                lineHeight="4"
                              >
                                Legitimate interest
                              </Text>
                            </Flex>
                          </Flex>
                          {values.purposeOverrides.map((po, index) => (
                            <Flex
                              key={po.purpose}
                              width="100%"
                              height="36px"
                              alignItems="center"
                              borderBottom="solid 1px"
                              borderColor="gray.200"
                            >
                              <Flex
                                width="600px"
                                borderLeft="solid 1px"
                                borderColor="gray.200"
                                p={0}
                                alignItems="center"
                                height="100%"
                                pl="4"
                                fontSize="xs"
                                fontWeight="normal"
                                lineHeight="4"
                              >
                                Purpose {po.purpose}:{" "}
                                {purposeMapping[po.purpose].name}
                              </Flex>

                              <Flex
                                flex="1"
                                justifyContent="center"
                                alignItems="center"
                                borderLeft="solid 1px"
                                borderColor="gray.200"
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
                              <LegalBasisContainer purpose={po.purpose} endCol>
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
