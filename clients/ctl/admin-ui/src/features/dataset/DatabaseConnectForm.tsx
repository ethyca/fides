import { Box, Button, Text, useToast, VStack } from "@fidesui/react";
import { Form, Formik } from "formik";
import { useRouter } from "next/router";
import * as Yup from "yup";

import { useFeatures } from "~/features/common/features.slice";
import { CustomSwitch, CustomTextInput } from "~/features/common/form/inputs";
import { getErrorMessage } from "~/features/common/helpers";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import { DEFAULT_ORGANIZATION_FIDES_KEY } from "~/features/organization";
import { Dataset, GenerateTypes, System, ValidTargets } from "~/types/api";

import {
  setActiveDataset,
  useCreateDatasetMutation,
  useGenerateDatasetMutation,
} from "./dataset.slice";

const isDataset = (sd: System | Dataset): sd is Dataset =>
  !("system_type" in sd);

const initialValues = { url: "", classify: false };

type FormValues = typeof initialValues;

const ValidationSchema = Yup.object().shape({
  url: Yup.string().required().label("Database URL"),
});

const DatabaseConnectForm = () => {
  const [generateMutation, { isLoading: isGenerating }] =
    useGenerateDatasetMutation();
  const [createMutation, { isLoading: isCreating }] =
    useCreateDatasetMutation();
  const isLoading = isGenerating || isCreating;

  const toast = useToast();
  const router = useRouter();
  const features = useFeatures();

  /**
   * Trigger the generate mutation and pick out the result dataset or the error if generate failed.
   */
  const generate = async (
    values: FormValues
  ): Promise<
    | {
        error: string;
      }
    | {
        dataset: Dataset;
      }
  > => {
    const result = await generateMutation({
      organization_key: DEFAULT_ORGANIZATION_FIDES_KEY,
      generate: {
        config: { connection_string: values.url },
        target: ValidTargets.DB,
        type: GenerateTypes.DATASETS,
      },
    });

    if ("error" in result) {
      return {
        error: getErrorMessage(result.error),
      };
    }

    const dataset = result.data.generate_results?.[0];
    if (!(dataset && isDataset(dataset))) {
      return {
        error: "Unable to generate a dataset with this connection.",
      };
    }

    return {
      dataset,
    };
  };

  /**
   * Trigger the create mutation and pick out the result or error. The datasetBody is a Dateset that
   * has not yet been persisted.
   */
  const create = async (
    datasetBody: Dataset
  ): Promise<
    | {
        error: string;
      }
    | {
        dataset: Dataset;
      }
  > => {
    const result = await createMutation(datasetBody);

    if ("error" in result) {
      return {
        error: getErrorMessage(result.error),
      };
    }

    return {
      dataset: result.data,
    };
  };

  const handleSubmit = async (values: FormValues) => {
    const generateResult = await generate(values);
    if ("error" in generateResult) {
      toast(errorToastParams(generateResult.error));
      return;
    }

    const createResult = await create(generateResult.dataset);
    if ("error" in createResult) {
      toast(errorToastParams(createResult.error));
      return;
    }

    toast(successToastParams("Successfully loaded new dataset"));
    setActiveDataset(createResult.dataset);
    router.push(`/dataset/${createResult.dataset.fides_key}`);
  };

  return (
    <Formik
      initialValues={{ ...initialValues, classify: features.plus }}
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

            {features.plus ? (
              <CustomSwitch
                name="classify"
                label="Classify dataset"
                tooltip="In addition to generating the Dataset, Fidescls will scan the database to determine the locations of possible PII and suggest labels based on the contents of your tables."
              />
            ) : null}

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
