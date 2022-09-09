import { Box, Button, Text } from "@fidesui/react";
import { Form, Formik, FormikHelpers } from "formik";
import yaml from "js-yaml";

import { CustomTextArea } from "~/features/common/form/inputs";
import { getErrorMessage, isYamlException } from "~/features/common/helpers";
import { RTKResult } from "~/features/common/types";

const initialValues = { yaml: "" };
type FormValues = typeof initialValues;

interface Props<T> {
  description: string;
  submitButtonText: string;
  onCreate: (yaml: unknown) => RTKResult<T>;
  onSuccess: (data: T) => void;
}

const YamlForm = <T extends unknown>({
  description,
  submitButtonText,
  onCreate,
  onSuccess,
}: Props<T>) => {
  const handleCreate = async (
    newValues: FormValues,
    formikHelpers: FormikHelpers<FormValues>
  ) => {
    const { setErrors } = formikHelpers;
    const parsedYaml = yaml.load(newValues.yaml, { json: true });
    const result = await onCreate(parsedYaml);

    if ("error" in result) {
      const errorMessage = getErrorMessage(result.error);
      setErrors({ yaml: errorMessage });
    } else if ("data" in result) {
      onSuccess(result.data);
    }
  };

  const validate = (newValues: FormValues) => {
    try {
      const parsedYaml = yaml.load(newValues.yaml, { json: true });
      if (!parsedYaml) {
        return { yaml: "Could not parse the supplied YAML" };
      }
    } catch (error) {
      if (isYamlException(error)) {
        return {
          yaml: `Could not parse the supplied YAML: \n\n${error.message}`,
        };
      }
      return { yaml: "Could not parse the supplied YAML" };
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
            {description}
          </Text>
          {/* note: the error is more helpful in a monospace font, so apply Menlo to the whole Box */}
          <Box mb={4} whiteSpace="pre-line" fontFamily="Menlo">
            <CustomTextArea
              name="yaml"
              textAreaProps={{
                fontWeight: 400,
                lineHeight: "150%",
                color: "gray.800",
                fontSize: "13px",
                height: "50vh",
                width: "100%",
                mb: "2",
              }}
            />
          </Box>
          <Button
            size="sm"
            colorScheme="primary"
            type="submit"
            disabled={isSubmitting}
            data-testid="submit-yaml-btn"
          >
            {submitButtonText}
          </Button>
        </Form>
      )}
    </Formik>
  );
};

export default YamlForm;
