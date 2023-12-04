/* eslint-disable react/no-array-index-key */
import { AddIcon } from "@chakra-ui/icons";
import {
  Box,
  Button,
  DeleteIcon,
  Flex,
  Heading,
  IconButton,
  Spinner,
  Text,
  useToast,
} from "@fidesui/react";
import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/dist/query";
import { FieldArray, Form, Formik, FormikHelpers } from "formik";
import type { NextPage } from "next";
import * as Yup from "yup";

import { useAppSelector } from "~/app/hooks";
import DocsLink from "~/features/common/DocsLink";
import FormSection from "~/features/common/form/FormSection";
import { CustomTextInput } from "~/features/common/form/inputs";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import Layout from "~/features/common/Layout";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import {
  CORSOrigins,
  selectApplicationConfig,
  selectCORSOrigins,
  useGetConfigurationSettingsQuery,
  usePutConfigurationSettingsMutation,
} from "~/features/privacy-requests/privacy-requests.slice";
import { ApplicationConfig } from "~/types/api";
import { useGetTcfPurposeOverridesQuery} from "~/features/plus/plus.slice"

type FormValues = CORSOrigins;

const ConsentConfigPage: NextPage = () => {
  const { isLoading: isLoadingGetQuery } = useGetConfigurationSettingsQuery();
  const corsOrigins = useAppSelector(selectCORSOrigins());
  const applicationConfig = useAppSelector(selectApplicationConfig());
  const [putConfigSettingsTrigger, { isLoading: isLoadingPutMutation }] =
    usePutConfigurationSettingsMutation();
  const {data: tcfPurposeOverrides} = useGetTcfPurposeOverridesQuery();

  const toast = useToast();

  const ValidationSchema = Yup.object().shape({
    cors_origins: Yup.array()
      .nullable()
      .of(Yup.string().required().trim().url().label("URL")),
  });

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
          `An unexpected error occurred while saving CORS domains. Please try again.`
        );
        toast(errorToastParams(errorMsg));
      } else {
        toast(successToastParams("CORS domains saved successfully"));
        // Reset state such that isDirty will be checked again before next save
        formikHelpers.resetForm({ values });
      }
    };

    const payloadOrigins =
      values.cors_origins && values.cors_origins.length > 0
        ? values.cors_origins
        : undefined;

    const payload: ApplicationConfig = {
      ...applicationConfig,
      security: {
        cors_origins: payloadOrigins,
      },
    };

    const result = await putConfigSettingsTrigger(payload);

    handleResult(result);
  };

  return (
    <Layout title="Consent Configuration">
      <Box data-testid="consent-configuration">
        <Heading marginBottom={4} fontSize="2xl">
          Global Consent Settings
        </Heading>
        <Box maxWidth="600px">
          <Text marginBottom={2} fontSize="md">
            Manage domains for your organization
          </Text>
          <Text mb={10} fontSize="sm">
            You must add domains associated with your organization to Fides to
            ensure features such as consent function correctly. For more
            information on managing domains on Fides, click here{" "}
            <DocsLink href="https://fid.es/cors-configuration">
              docs.ethyca.com
            </DocsLink>
            .
          </Text>
        </Box>

        <Box maxW="600px">
          {tcfPurposeOverrides? tcfPurposeOverrides.map((tp)=> (<div>{tp.purpose} </div>)): null}
        </Box>
      </Box>
    </Layout>
  );
};
export default ConsentConfigPage;
