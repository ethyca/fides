import { Box, Button, Text } from "@fidesui/react";
import { Form, Formik } from "formik";
import yaml from "js-yaml";

import { CustomTextArea } from "../common/form/inputs";
import { isYamlException } from "../common/helpers";

const initialValues = { datasetYaml: "" };
type FormValues = typeof initialValues;

const DatasetYamlForm = () => {
  const handleCreate = (newValues: FormValues) => {
    const parsedYaml = yaml.load(newValues.datasetYaml, { json: true });
    console.log({ parsedYaml });
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
