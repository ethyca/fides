import { Box, Button, Text, useToast } from "@fidesui/react";
import { Form, Formik, FormikHelpers, useFormikContext } from "formik";
import yaml from "js-yaml";
import { useRouter } from "next/router";

import { CustomTextArea } from "../common/form/inputs";
import { getErrorFromResult, isYamlException } from "../common/helpers";
import { successToastParams } from "../common/toast";
import { setActiveDataset, useCreateDatasetMutation } from "./dataset.slice";
import { Dataset } from "./types";

const initialValues = { datasetYaml: "" };
type FormValues = typeof initialValues;

// handle the common case where everything is nested under a `dataset` key
interface NestedDataset {
  dataset: Dataset[];
}
export function isDatasetArray(value: unknown): value is NestedDataset {
  return (
    typeof value === "object" &&
    value != null &&
    "dataset" in value &&
    Array.isArray((value as any).dataset)
  );
}

const DatasetYamlForm = () => {
  const [createDataset] = useCreateDatasetMutation();
  const toast = useToast();
  const router = useRouter();

  const handleCreate = async (
    newValues: FormValues,
    formikHelpers: FormikHelpers<FormValues>
  ) => {
    const { setErrors } = formikHelpers;
    const parsedYaml = yaml.load(newValues.datasetYaml, { json: true });
    let dataset: Dataset;
    if (isDatasetArray(parsedYaml)) {
      [dataset] = parsedYaml.dataset;
    } else {
      // cast to a Dataset and let the backend do validation
      dataset = parsedYaml as Dataset;
    }

    const result = await createDataset(dataset);
    const error = getErrorFromResult(result);
    if (error) {
      setErrors({ datasetYaml: error });
    } else if ("data" in result) {
      toast(successToastParams("Successfully loaded new dataset YAML"));
      setActiveDataset(result.data);
      router.push(`/dataset/${result.data.fides_key}`);
    }
  };

  const validate = (newValues: FormValues) => {
    try {
      const parsedYaml = yaml.load(newValues.datasetYaml, { json: true });
      if (!parsedYaml) {
        return { datasetYaml: "Could not parse the supplied YAML" };
      }
    } catch (error) {
      if (isYamlException(error)) {
        return {
          datasetYaml: `Could not parse the supplied YAML: \n\n${error.message}`,
        };
      }
      return { datasetYaml: "Could not parse the supplied YAML" };
    }
    return {};
  };

  return (
    <Formik
      initialValues={initialValues}
      validate={validate}
      onSubmit={handleCreate}
      validateOnChange={false}
      validateOnBlur={false}
    >
      {({ isSubmitting }) => (
        <Form>
          <Text size="sm" color="gray.700" mb={4}>
            Get started creating your first dataset by pasting your dataset yaml
            below! You may have received this yaml from a colleague or your
            Ethyca developer support engineer.
          </Text>
          {/* note: the error is more helpful in a monospace font, so apply Menlo to the whole Box */}
          <Box mb={4} whiteSpace="pre-line" fontFamily="Menlo">
            <CustomTextArea
              name="datasetYaml"
              textAreaProps={{
                fontWeight: 400,
                lineHeight: "150%",
                color: "gray.800",
                fontSize: "13px",
                height: "50vh",
              }}
            />
          </Box>
          <Button
            size="sm"
            colorScheme="primary"
            type="submit"
            disabled={isSubmitting}
          >
            Create dataset
          </Button>
        </Form>
      )}
    </Formik>
  );
};

export default DatasetYamlForm;
