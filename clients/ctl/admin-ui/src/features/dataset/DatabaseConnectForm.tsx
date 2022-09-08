import { Box, Button, Text, useToast, VStack } from "@fidesui/react";
import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/dist/query";
import { Form, Formik, FormikHelpers } from "formik";
import { useRouter } from "next/router";
import * as Yup from "yup";

import {
  Dataset,
  GenerateResponse,
  GenerateTypes,
  ValidTargets,
} from "~/types/api";

import { CustomTextInput } from "../common/form/inputs";
import { getErrorMessage } from "../common/helpers";
import { successToastParams } from "../common/toast";
import {
  setActiveDataset,
  useCreateDatasetMutation,
  useGenerateDatasetMutation,
} from "./dataset.slice";

const initialValues = { url: "" };

type FormValues = typeof initialValues;

const ValidationSchema = Yup.object().shape({
  url: Yup.string().required().label("Database URL"),
});

const DatabaseConnectForm = () => {
  // TODO: where should this come from?
  const organizationKey = "default_organization";
  const [generate, { isLoading: isGenerating }] = useGenerateDatasetMutation();
  const [createDataset, { isLoading: isCreating }] = useCreateDatasetMutation();
  const isLoading = isGenerating || isCreating;

  const toast = useToast();
  const router = useRouter();

  const handleSubmit = async (
    values: FormValues,
    formikHelpers: FormikHelpers<FormValues>
  ) => {
    const { setErrors } = formikHelpers;

    const handleError = (error: FetchBaseQueryError | SerializedError) => {
      const errorMessage = getErrorMessage(error);
      setErrors({ url: errorMessage });
    };

    const handleGenerateResults = async (
      results: GenerateResponse["generate_results"]
    ) => {
      if (results && results.length) {
        const newDataset = results[0] as Dataset;
        const createResult = await createDataset(newDataset);
        if ("error" in createResult) {
          handleError(createResult.error);
        } else {
          toast(successToastParams("Successfully loaded new dataset"));
          setActiveDataset(createResult.data);
          router.push(`/dataset/${createResult.data.fides_key}`);
        }
      }
    };

    const response = await generate({
      organization_key: organizationKey,
      generate: {
        config: { connection_string: values.url },
        target: ValidTargets.DB,
        type: GenerateTypes.DATASETS,
      },
    });

    if ("error" in response) {
      const errorMessage = getErrorMessage(response.error);
      setErrors({ url: errorMessage });
    } else {
      handleGenerateResults(response.data.generate_results);
    }
  };

  return (
    <Formik
      initialValues={initialValues}
      validationSchema={ValidationSchema}
      onSubmit={handleSubmit}
      validateOnChange={false}
      validateOnBlur={false}
    >
      {({ isSubmitting }) => (
        <Form>
          <VStack spacing={8} align="left">
            <Text size="sm" color="gray.700">
              Connect to one of your databases using a connection URL. You may
              have received this URL from a colleague or your Ethyca developer
              support engineer.
            </Text>
            <Box>
              <CustomTextInput name="url" label="Database URL" />
            </Box>
            <Box>
              <Button
                size="sm"
                colorScheme="primary"
                type="submit"
                isLoading={isSubmitting || isLoading}
                isDisabled={isSubmitting || isLoading}
                data-testid="create-dataset-btn"
              >
                Generate dataset
              </Button>
            </Box>
          </VStack>
        </Form>
      )}
    </Formik>
  );
};

export default DatabaseConnectForm;
