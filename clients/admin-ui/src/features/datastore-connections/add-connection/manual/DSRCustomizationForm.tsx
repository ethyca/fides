import { useAlert } from "common/hooks";
import { Box, HStack, Text, TrashCanSolidIcon, VStack } from "fidesui";
import { FieldArray, Form, Formik, FormikProps } from "formik";
import { useRouter } from "next/router";
import React from "react";
import * as Yup from "yup";

import { useAppSelector } from "~/app/hooks";
import { ControlledSelect } from "~/features/common/form/ControlledSelect";
import { DATASTORE_CONNECTION_ROUTE } from "~/features/common/nav/routes";
import { useGetAllDataCategoriesQuery } from "~/features/taxonomy";
import { selectDataCategories } from "~/features/taxonomy/taxonomy.slice";

import CustomInput from "../forms/CustomInput";
import { ButtonGroup as ManualButtonGroup } from "./ButtonGroup";
import { Field } from "./types";

type DSRCustomizationFormProps = {
  data: Field[];
  isSubmitting: boolean;
  onSaveClick: (values: any, actions: any) => void;
};

const DSRCustomizationForm = ({
  data = [],
  isSubmitting = false,
  onSaveClick,
}: DSRCustomizationFormProps) => {
  const { isLoading: isLoadingDataCategories } = useGetAllDataCategoriesQuery();
  const allDataCategories = useAppSelector(selectDataCategories);

  const router = useRouter();
  const { errorAlert } = useAlert();

  const handleCancel = () => {
    router.push(DATASTORE_CONNECTION_ROUTE);
  };

  const handleSubmit = (values: any, actions: any) => {
    const uniqueValues = new Set(values.fields.map((f: Field) => f.pii_field));
    if (uniqueValues.size < values.fields.length) {
      errorAlert("PII Field must be unique");
      return;
    }
    onSaveClick(values, actions);
  };

  if (isLoadingDataCategories) {
    return null;
  }

  return (
    <Formik
      enableReinitialize
      initialValues={{
        fields:
          data.length > 0
            ? data
            : ([
                {
                  pii_field: "",
                  dsr_package_label: "",
                  data_categories: [],
                },
              ] as Field[]),
      }}
      onSubmit={handleSubmit}
      validateOnBlur={false}
      validateOnChange={false}
      validationSchema={Yup.object({
        fields: Yup.array().of(
          Yup.object().shape({
            pii_field: Yup.string()
              .required("PII Field is required")
              .min(1, "PII Field must have at least one character")
              .max(200, "PII Field has a maximum of 200 characters")
              .label("PII Field"),
            dsr_package_label: Yup.string()
              .required("DSR Package Label is required")
              .min(1, "DSR Package Label must have at least one character")
              .max(200, "DSR Package Label has a maximum of 200 characters")
              .label("DSR Package Label"),
            data_categories: Yup.array(Yup.string()).label("Data Categories"),
          }),
        ),
      })}
    >
      {/* @ts-ignore */}
      {(props: FormikProps<Values>) => (
        <Form style={{ marginTop: 0 }} noValidate>
          <VStack align="stretch">
            <FieldArray
              name="fields"
              render={(fieldArrayProps) => {
                const { fields } = props.values;
                return (
                  <>
                    <HStack
                      color="gray.900"
                      flex="1"
                      fontSize="14px"
                      fontWeight="semibold"
                      lineHeight="20px"
                      mb="6px"
                      spacing="24px"
                    >
                      <Box w="416px">PII Field</Box>
                      <Box w="416px">DSR Package Label</Box>
                      <Box w="416px">Data Categories</Box>
                      <Box visibility="hidden">
                        <TrashCanSolidIcon />
                      </Box>
                    </HStack>
                    <Box>
                      {fields && fields.length > 0
                        ? fields.map((_field: Field, index: number) => (
                            <HStack
                              // eslint-disable-next-line react/no-array-index-key
                              key={index}
                              mt={index > 0 ? "12px" : undefined}
                              spacing="24px"
                              align="flex-start"
                            >
                              <Box minH="57px" w="416px">
                                <CustomInput
                                  autoFocus={index === 0}
                                  displayHelpIcon={false}
                                  isRequired
                                  name={`fields.${index}.pii_field`}
                                />
                              </Box>
                              <Box minH="57px" w="416px">
                                <CustomInput
                                  displayHelpIcon={false}
                                  isRequired
                                  name={`fields.${index}.dsr_package_label`}
                                />
                              </Box>
                              <Box minH="57px" w="416px">
                                <ControlledSelect
                                  name={`fields.${index}.data_categories`}
                                  options={allDataCategories.map(
                                    (data_category) => ({
                                      value: data_category.fides_key,
                                      label: data_category.fides_key,
                                    }),
                                  )}
                                  isRequired
                                  mode="multiple"
                                />
                              </Box>
                              <Box
                                h="57px"
                                visibility={index > 0 ? "visible" : "hidden"}
                              >
                                <TrashCanSolidIcon
                                  onClick={() => fieldArrayProps.remove(index)}
                                  _hover={{ cursor: "pointer" }}
                                />
                              </Box>
                            </HStack>
                          ))
                        : null}
                    </Box>
                    <Text
                      color="complimentary.500"
                      fontWeight="medium"
                      fontSize="sm"
                      mb="24px !important"
                      mt="24px !important"
                      onClick={() => {
                        fieldArrayProps.push({
                          pii_field: "",
                          dsr_package_label: "",
                          data_categories: [],
                        });
                      }}
                      _hover={{ cursor: "pointer" }}
                    >
                      Add new PII field
                    </Text>
                    <ManualButtonGroup
                      isSubmitting={isSubmitting}
                      onCancelClick={handleCancel}
                    />
                  </>
                );
              }}
            />
          </VStack>
        </Form>
      )}
    </Formik>
  );
};

export default DSRCustomizationForm;
