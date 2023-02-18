/* eslint-disable @typescript-eslint/no-unused-vars */
import {
  Center,
  Flex,
  FormControl,
  FormLabel,
  forwardRef,
  Spinner,
} from "@fidesui/react";
import { FieldArray, Form, Formik, FormikHelpers, FormikProps } from "formik";
import { useImperativeHandle, useMemo, useRef } from "react";

import { useAlert } from "~/features/common/hooks";
import { useGetCustomFieldDefinitionsByResourceTypeQuery } from "~/features/plus/plus.slice";
import { CustomFieldDefinitionWithId, ResourceTypes } from "~/types/api";

import { CUSTOM_LABEL_STYLES } from "./form/CustomInput";
import { Layout } from "./Layout";

const initialValues = {
  customFieldDefinitions: [] as CustomFieldDefinitionWithId[],
};

type FormValues = typeof initialValues;

type ChooseFromLibraryProps = {
  onSubmitComplete: () => void;
  resourceType: ResourceTypes;
};

const ChooseFromLibrary = forwardRef(
  ({ onSubmitComplete, resourceType }: ChooseFromLibraryProps, ref) => {
    const { errorAlert, successAlert } = useAlert();
    const formRef = useRef(null);

    const { data, isFetching, isLoading, isSuccess } =
      useGetCustomFieldDefinitionsByResourceTypeQuery(resourceType);

    const handleSubmit = async (
      values: FormValues,
      helpers: FormikHelpers<FormValues>
    ) => {
      onSubmitComplete();
    };

    useImperativeHandle(
      ref,
      () => ({
        getDirty() {
          let value = false;
          if (formRef.current) {
            value = (formRef.current as FormikProps<FormValues>).dirty;
          }
          return value;
        },
        submitForm() {
          if (formRef.current) {
            (formRef.current as FormikProps<FormValues>).submitForm();
          }
        },
      }),
      []
    );

    initialValues.customFieldDefinitions = useMemo(() => data || [], [data]);

    return (
      <Layout>
        {(isFetching || isLoading) && (
          <Center>
            <Spinner />
          </Center>
        )}
        {isSuccess && data && (
          <Formik
            enableReinitialize
            initialValues={initialValues}
            innerRef={formRef}
            onSubmit={handleSubmit}
            validationOnBlur={false}
            validationOnChange={false}
          >
            {(props: FormikProps<FormValues>) => (
              <Form data-testid="choose-from-library-form" noValidate>
                <Flex
                  flexDirection="column"
                  gap="12px"
                  paddingTop="6px"
                  paddingBottom="24px"
                >
                  <FieldArray
                    name="customFieldDefinitions"
                    render={(fieldArrayProps) => {
                      const { customFieldDefinitions } = props.values;
                      return (
                        <Flex flexDirection="column" gap="24px">
                          <Flex flexDirection="column">
                            {customFieldDefinitions.map((value, index) => (
                              <Flex
                                alignItems="baseline"
                                flexGrow={1}
                                gap="12px"
                                // eslint-disable-next-line react/no-array-index-key
                                key={index}
                                mt={index > 0 ? "12px" : undefined}
                              >
                                <FormControl display="flex">
                                  <FormLabel
                                    htmlFor={`customFieldDefinitions[${index}]`}
                                    {...CUSTOM_LABEL_STYLES}
                                  >
                                    {value.name}
                                  </FormLabel>
                                </FormControl>
                              </Flex>
                            ))}
                          </Flex>
                        </Flex>
                      );
                    }}
                  />
                </Flex>
              </Form>
            )}
          </Formik>
        )}
      </Layout>
    );
  }
);

export { ChooseFromLibrary };
