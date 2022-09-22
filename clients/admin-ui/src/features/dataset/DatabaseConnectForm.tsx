import { Box, Button, Text, useToast, VStack } from "@fidesui/react";
import { Form, Formik } from "formik";
import { useRouter } from "next/router";
import { useDispatch } from "react-redux";
import * as Yup from "yup";

import ConfirmationModal from "~/features/common/ConfirmationModal";
import { useFeatures } from "~/features/common/features.slice";
import { CustomSwitch, CustomTextInput } from "~/features/common/form/inputs";
import { getErrorMessage } from "~/features/common/helpers";
import { useCreateClassificationMutation } from "~/features/common/plus.slice";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import { DEFAULT_ORGANIZATION_FIDES_KEY } from "~/features/organization";
import { Dataset, GenerateTypes, System, ValidTargets } from "~/types/api";

import {
  setActiveDatasetFidesKey,
  useCreateDatasetMutation,
  useGenerateDatasetMutation,
} from "./dataset.slice";

const isDataset = (sd: System | Dataset): sd is Dataset =>
  !("system_type" in sd);

const initialValues = { url: "", classify: false, classifyConfirmed: false };

type FormValues = typeof initialValues;

const ValidationSchema = Yup.object().shape({
  url: Yup.string().required().label("Database URL"),
  classify: Yup.boolean(),
  // If classify is true, then the choice must be confirmed. The URL is also tested so that we don't
  // show the confirmation modal if the form is invalid.
  classifyConfirmed: Yup.boolean().when(["url", "classify"], {
    is: (url: string, classify: boolean) => url && classify,
    then: Yup.boolean().equals([true]),
  }),
});

const DatabaseConnectForm = () => {
  const [generateMutation, { isLoading: isGenerating }] =
    useGenerateDatasetMutation();
  const [createMutation, { isLoading: isCreating }] =
    useCreateDatasetMutation();
  const [classifyMutation, { isLoading: isClassifying }] =
    useCreateClassificationMutation();
  const isLoading = isGenerating || isCreating || isClassifying;

  const toast = useToast();
  const router = useRouter();
  const features = useFeatures();
  const dispatch = useDispatch();

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

  /**
   * Trigger the classify mutation and pick out the result or error. The Dataset should be already
   * have been created.
   */
  const classify = async (
    dataset: Dataset
  ): Promise<
    | {
      error: string;
    }
    | {
      status: string;
    }
  > => {
    const result = await classifyMutation({ fides_key: dataset.fides_key });

    if ("error" in result) {
      return {
        error: getErrorMessage(result.error),
      };
    }

    return {
      status: result.data.status,
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

    // Default generate flow:
    if (!values.classify) {
      toast(
        successToastParams(`Generated ${createResult.dataset.name} dataset`)
      );
      router.push(`/dataset/${createResult.dataset.fides_key}`);
      return;
    }

    // Additional steps when using classify:
    const classifyResult = await classify(createResult.dataset);
    if ("error" in classifyResult) {
      toast(errorToastParams(classifyResult.error));
      return;
    }

    toast(successToastParams(`Generate and classify are now in progress`));
    dispatch(setActiveDatasetFidesKey(createResult.dataset.fides_key));
    router.push(`/dataset`);
  };

  return (
    <Formik
      initialValues={{ ...initialValues, classify: features.plus }}
      validationSchema={ValidationSchema}
      onSubmit={handleSubmit}
      validateOnChange={false}
      validateOnBlur={false}
    >
      {({
        isSubmitting,
        errors,
        values,
        submitForm,
        resetForm,
        setFieldValue,
      }) => (
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
          <ConfirmationModal
            title="Generate and classify this dataset"
            message="You have chosen to generate and classify this dataset. This process may take several minutes. In the meantime you can continue using Fides. You will receive a notification when the process is complete."
            isOpen={errors.classifyConfirmed !== undefined}
            onClose={() => {
              resetForm({ values: { ...values, classifyConfirmed: false } });
            }}
            onConfirm={() => {
              setFieldValue("classifyConfirmed", true);

              // Formik needs a moment after setting the field before it can submit.
              // https://github.com/jaredpalmer/formik/issues/529#issuecomment-740042815
              setTimeout(() => {
                submitForm();
              }, 0);
            }}
          />
        </Form>
      )}
    </Formik>
  );
};

export default DatabaseConnectForm;
