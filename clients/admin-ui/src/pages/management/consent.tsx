/* eslint-disable react/no-array-index-key */
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

import { selectPurposes } from "~/features/common/purpose.slice";
import { useAppSelector } from "~/app/hooks";
import DocsLink from "~/features/common/DocsLink";
import { CustomSwitch } from "~/features/common/form/inputs";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import Layout from "~/features/common/Layout";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import { useFeatures } from "~/features/common/features";
import {
  useGetTcfPurposeOverridesQuery,
  usePatchTcfPurposeOverridesMutation,
  useGetHealthQuery,
} from "~/features/plus/plus.slice";
import { TCFPurposeOverrideSchema } from "~/types/api";

type FormValues = { purposeOverrides: TCFPurposeOverrideSchema[] };

const ConsentConfigPage: NextPage = () => {
  const { isLoading: isHealthCheckLoading } = useGetHealthQuery();
  const { tcf: isTcfEnabled } = useFeatures();
  const { data: tcfPurposeOverrides } = useGetTcfPurposeOverridesQuery(
    undefined,
    {
      skip: isHealthCheckLoading || !isTcfEnabled,
    }
  );
  const [patchTcfPurposeOverridesTrigger] =
    usePatchTcfPurposeOverridesMutation();
  const purposes = useAppSelector(selectPurposes);

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

    const payload: TCFPurposeOverrideSchema[] = [...values.purposeOverrides];

    const result = await patchTcfPurposeOverridesTrigger(payload);

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
          {tcfPurposeOverrides
            ? tcfPurposeOverrides.map((tp) => <div>{tp.purpose} </div>)
            : null}
        </Box>
      </Box>
    </Layout>
  );
};
export default ConsentConfigPage;
