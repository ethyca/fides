import {
  Box,
  Button,
  DeleteIcon,
  Flex,
  Heading,
  IconButton,
  Link,
  Text,
  useToast,
} from "@fidesui/react";
import type { NextPage } from "next";
import { AddIcon } from "@chakra-ui/icons";

import { Form, Formik, FormikHelpers, FieldArray } from "formik";
import { CustomTextInput } from "~/features/common/form/inputs";
import FormSection from "~/features/common/form/FormSection";

import {useAppSelector } from "~/app/hooks"
import Layout from "~/features/common/Layout";
import {
  selectCORSDomains,
  useCreateConfigurationSettingsMutation,
  useGetConfigurationSettingsQuery,
} from "~/features/privacy-requests/privacy-requests.slice";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { FetchBaseQueryError } from "@reduxjs/toolkit/dist/query";
import { SerializedError } from "@reduxjs/toolkit";
import { errorToastParams, successToastParams } from "~/features/common/toast";


type FormValues = {
  domains: string[]
}

const CORSConfigurationPage: NextPage = () => {
  const { isLoading:isLoadingGetQuery } = useGetConfigurationSettingsQuery();
  const corsDomains = useAppSelector(selectCORSDomains());
  const [patchConfigSettingsTrigger,  {isLoading: isLoadingPatchMutation}] = useCreateConfigurationSettingsMutation();
  
  const toast = useToast();
  if (isLoadingGetQuery) {
    return <div>loading</div>;
  }


  const handleSubmit = async (
    values: FormValues,
    formikHelpers: FormikHelpers<FormValues>
  )=>{

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
        toast(successToastParams("CORS domains saved successfully"))
        // Reset state such that isDirty will be checked again before next save
        formikHelpers.resetForm({ values });
      }
    };

    const result = await patchConfigSettingsTrigger({
      security:{
        cors_origins: values.domains
      }
    })

    handleResult(result)
  }


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
            <Formik<FormValues>
              initialValues={corsDomains}
              enableReinitialize
              onSubmit={handleSubmit}
            >
              {({ dirty, values, isValid }) => (
                <Form>
                  <FieldArray
                    name="domains"
                    render={(arrayHelpers) => {
                      return (
                        <Flex flexDir="column">
                          {values.domains.map(
                            (_: string, index: number) => (
                              <Flex flexDir="row" key={index} my={3}>
                                <CustomTextInput
                                  variant="stacked"
                                  name={`domains[${index}]`}
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
                      );
                    }}
                  />

                  <Box mt={6}>
                    <Button
                      type="submit"
                      variant="primary"
                      size="sm"
                      isDisabled={isLoadingPatchMutation|| !dirty || !isValid}
                      isLoading={isLoadingPatchMutation}
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
    </Layout>
  );
};
export default CORSConfigurationPage;
