/* eslint-disable react/no-array-index-key */
import { AddIcon } from "@chakra-ui/icons";
import {
  Box,
  Button,
  DeleteIcon,
  Flex,
  Heading,
  IconButton,
  Link,
  Spinner,
  Text,
  useToast,
} from "@fidesui/react";
import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/dist/query";
import { FieldArray, Form, Formik, FormikHelpers } from "formik";
import type { NextPage } from "next";

import { useAppSelector } from "~/app/hooks";
import FormSection from "~/features/common/form/FormSection";
import { CustomTextInput } from "~/features/common/form/inputs";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import Layout from "~/features/common/Layout";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import {
  CORSOrigins,
  selectCORSOrigins,
  useCreateConfigurationSettingsMutation,
  useGetConfigurationSettingsQuery,
} from "~/features/privacy-requests/privacy-requests.slice";

type FormValues = CORSOrigins;

const CORSConfigurationPage: NextPage = () => {
  const { isLoading: isLoadingGetQuery } = useGetConfigurationSettingsQuery();
  const corsOrigins = useAppSelector(selectCORSOrigins());
  const [patchConfigSettingsTrigger, { isLoading: isLoadingPatchMutation }] =
    useCreateConfigurationSettingsMutation();

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
          `An unexpected error occurred while saving CORS domains. Please try again.`
        );
        toast(errorToastParams(errorMsg));
      } else {
        toast(successToastParams("CORS domains saved successfully"));
        // Reset state such that isDirty will be checked again before next save
        formikHelpers.resetForm({ values });
      }
    };

    const result = await patchConfigSettingsTrigger({
      security: {
        cors_origins: values.cors_origins,
      },
    });

    handleResult(result);
  };

  return (
    <Layout title="CORS Configuration">
      <Box data-testid="cors-configuration">
        <Heading marginBottom={4} fontSize="2xl">
          CORS Configuration
        </Heading>
        <Box maxWidth="600px">
          <Text marginBottom={2} fontSize="md">
            Add your CORS domains below
          </Text>
          <Text mb={10} fontSize="sm">
            Please visit{" "}
            <Link
              color="complimentary.500"
              href="https://docs.ethyca.com"
              isExternal
            >
              docs.ethyca.com
            </Link>{" "}
            for more information on how to configure CORS domains.
          </Text>
        </Box>

        <Box maxW="600px">
          <FormSection title="CORS Domains">
            {isLoadingGetQuery || isLoadingPatchMutation ? (
              <Flex justifyContent="center">
                <Spinner />
              </Flex>
            ) : (
              <Formik<FormValues>
                initialValues={corsOrigins}
                enableReinitialize
                onSubmit={handleSubmit}
              >
                {({ dirty, values, isValid }) => (
                  <Form>
                    <FieldArray
                      name="cors_origins"
                      render={(arrayHelpers) => (
                        <Flex flexDir="column">
                          {values.cors_origins!.map(
                            (_: string, index: number) => (
                              <Flex flexDir="row" key={index} my={3}>
                                <CustomTextInput
                                  variant="stacked"
                                  name={`cors_origins[${index}]`}
                                />

                                <IconButton
                                  ml={8}
                                  aria-label="delete-cors-domain"
                                  variant="outline"
                                  zIndex={2}
                                  size="sm"
                                  onClick={() => {
                                    arrayHelpers.remove(index);
                                  }}
                                >
                                  <DeleteIcon />
                                </IconButton>
                              </Flex>
                            )
                          )}

                          <Flex justifyContent="center" mt={3}>
                            <Button
                              aria-label="add-cors-domain"
                              variant="outline"
                              size="sm"
                              onClick={() => {
                                arrayHelpers.push("");
                              }}
                              rightIcon={<AddIcon />}
                            >
                              Add CORS domain
                            </Button>
                          </Flex>
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
            )}
          </FormSection>
        </Box>
      </Box>
    </Layout>
  );
};
export default CORSConfigurationPage;
