import { AntButton as Button, Box, DeleteIcon, Flex, Text } from "fidesui";
import { FieldArray, Form, Formik } from "formik";
import * as Yup from "yup";

import FormSection from "~/features/common/form/FormSection";
import { CustomTextInput } from "~/features/common/form/inputs";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { useAlert } from "~/features/common/hooks";
import {
  useGetPrivacyRequestRedactionPatternsQuery,
  useUpdatePrivacyRequestRedactionPatternsMutation,
} from "~/features/privacy-requests/privacy-request-redaction-patterns.slice";

interface PatternItem {
  id: string;
  value: string;
}

interface PrivacyRequestRedactionPatternsFormValues {
  patterns: PatternItem[];
}

// Centralized validation function for pattern values
const validatePatternNonEmpty = (value: string | undefined | null): boolean => {
  return !!(value && value.trim().length > 0);
};

const ValidationSchema = Yup.object().shape({
  patterns: Yup.array()
    .nullable()
    .of(
      Yup.object().shape({
        id: Yup.string().required(),
        value: Yup.string()
          .required()
          .test(
            "is-valid-pattern",
            "Pattern cannot be empty",
            validatePatternNonEmpty,
          )
          .label("Pattern"),
      }),
    ),
});

const PrivacyRequestRedactionPatternsPage = () => {
  const { errorAlert, successAlert } = useAlert();

  const { data: currentPatterns } =
    useGetPrivacyRequestRedactionPatternsQuery(undefined);
  const [updatePatterns, { isLoading: isUpdating }] =
    useUpdatePrivacyRequestRedactionPatternsMutation();

  const handleSubmit = async (
    values: PrivacyRequestRedactionPatternsFormValues,
  ) => {
    // Filter out empty patterns and trim whitespace
    const cleanedPatterns = values.patterns
      .filter((pattern) => validatePatternNonEmpty(pattern.value))
      .map((pattern) => pattern.value.trim());

    const payload = await updatePatterns({ patterns: cleanedPatterns });

    if (isErrorResult(payload)) {
      errorAlert(
        getErrorMessage(payload.error),
        "Failed to update privacy request redaction patterns",
      );
    } else {
      successAlert("Privacy request redaction patterns updated successfully.");
    }
  };

  const initialValues: PrivacyRequestRedactionPatternsFormValues = {
    patterns: (currentPatterns?.patterns || []).map((pattern, index) => ({
      id: `pattern-${index}`,
      value: pattern,
    })),
  };

  return (
    <Box data-testid="privacy-request-redaction-patterns">
      <Box maxW="600px">
        <Text fontSize="sm" pb={6}>
          List of regex patterns used to mask dataset, collection, and field
          names in DSR package reports. Names matching these patterns will be
          replaced with position-based identifiers (e.g. dataset_1,
          collection_2, field_3).
        </Text>
        <FormSection
          data-testid="privacy-request-redaction-patterns-form"
          title="Regex patterns"
        >
          <Formik<PrivacyRequestRedactionPatternsFormValues>
            initialValues={initialValues}
            enableReinitialize
            onSubmit={handleSubmit}
            validationSchema={ValidationSchema}
            validateOnChange
          >
            {({ dirty, values, isValid }) => (
              <Form>
                <FieldArray
                  name="patterns"
                  render={(arrayHelpers) => (
                    <Flex flexDir="column">
                      {values.patterns.map((patternItem, index) => (
                        <Flex flexDir="row" key={patternItem.id} my={3}>
                          <CustomTextInput
                            variant="stacked"
                            name={`patterns[${index}].value`}
                            placeholder="Enter regex pattern (e.g., sensitive_.*)"
                          />

                          <Button
                            aria-label="remove-pattern"
                            className="z-[2] ml-4"
                            icon={<DeleteIcon />}
                            onClick={() => {
                              arrayHelpers.remove(index);
                            }}
                          />
                        </Flex>
                      ))}

                      <Flex justifyContent="center" mt={3}>
                        <Button
                          aria-label="add-pattern"
                          className="w-full"
                          onClick={() => {
                            arrayHelpers.push({
                              id: `pattern-new-${values.patterns.length}`,
                              value: "",
                            });
                          }}
                        >
                          Add regex pattern +
                        </Button>
                      </Flex>
                    </Flex>
                  )}
                />

                <Box mt={6} textAlign="right">
                  <Button
                    htmlType="submit"
                    type="primary"
                    disabled={isUpdating || !dirty || !isValid}
                    loading={isUpdating}
                    data-testid="save-btn"
                  >
                    Save
                  </Button>
                </Box>
              </Form>
            )}
          </Formik>
        </FormSection>
      </Box>
    </Box>
  );
};

export default PrivacyRequestRedactionPatternsPage;
