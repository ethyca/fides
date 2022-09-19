import { Box, Button, Divider, Heading, Stack, useToast } from "@fidesui/react";
import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/dist/query/fetchBaseQuery";
import { Form, Formik, FormikHelpers } from "formik";
import React, { Fragment, useState } from "react";
import * as Yup from "yup";

import { useAppSelector } from "~/app/hooks";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { AddIcon } from "~/features/common/Icon";
import {
  selectDataQualifiers,
  useGetAllDataQualifiersQuery,
} from "~/features/data-qualifier/data-qualifier.slice";
import {
  selectDataSubjects,
  useGetAllDataSubjectsQuery,
} from "~/features/data-subjects/data-subject.slice";
import {
  selectDataUses,
  useGetAllDataUsesQuery,
} from "~/features/data-use/data-use.slice";
import {
  selectDataCategories,
  useGetAllDataCategoriesQuery,
} from "~/features/taxonomy/taxonomy.slice";
import { PrivacyDeclaration, System } from "~/types/api";

import {
  CustomMultiSelect,
  CustomSelect,
  CustomTextInput,
} from "../common/form/inputs";
import { useUpdateSystemMutation } from "../system/system.slice";
import PrivacyDeclarationAccordion from "./PrivacyDeclarationAccordion";

type FormValues = PrivacyDeclaration;

const ValidationSchema = Yup.object().shape({
  name: Yup.string().required().label("Declaration name"),
  data_categories: Yup.array(Yup.string())
    .min(1, "Must assign at least one data category")
    .label("Data categories"),
  data_use: Yup.string().required().label("Data use"),
  data_subjects: Yup.array(Yup.string())
    .min(1, "Must assign at least one data subject")
    .label("Data subjects"),
});

const transformFormValuesToDeclaration = (
  formValues: FormValues
): PrivacyDeclaration => ({
  ...formValues,
  data_qualifier:
    formValues.data_qualifier === "" ? undefined : formValues.data_qualifier,
});

interface Props {
  system: System;
  onCancel: () => void;
  onSuccess: (system: System) => void;
}

const PrivacyDeclarationForm = ({ system, onCancel, onSuccess }: Props) => {
  const toast = useToast();
  const [formDeclarations, setFormDeclarations] = useState<
    PrivacyDeclaration[]
  >(system?.privacy_declarations ? [...system.privacy_declarations] : []);
  const [updateSystem] = useUpdateSystemMutation();
  const [isLoading, setIsLoading] = useState(false);

  // Query subscriptions:
  useGetAllDataCategoriesQuery();
  useGetAllDataSubjectsQuery();
  useGetAllDataQualifiersQuery();
  useGetAllDataUsesQuery();

  const allDataCategories = useAppSelector(selectDataCategories);
  const allDataSubjects = useAppSelector(selectDataSubjects);
  const allDataUses = useAppSelector(selectDataUses);
  const allDataQualifiers = useAppSelector(selectDataQualifiers);

  const initialValues = {
    name: "",
    data_categories: [],
    data_subjects: [],
    data_use: "",
    data_qualifier: "",
  };

  const handleSubmit = async () => {
    const systemBodyWithDeclaration = {
      ...system,
      privacy_declarations: formDeclarations,
    };

    const handleResult = (
      result:
        | { data: System }
        | { error: FetchBaseQueryError | SerializedError }
    ) => {
      if (isErrorResult(result)) {
        const errorMsg = getErrorMessage(
          result.error,
          "An unexpected error occurred while updating the system. Please try again."
        );

        toast({
          status: "error",
          description: errorMsg,
        });
      } else {
        toast.closeAll();
        onSuccess(result.data);
      }
    };

    setIsLoading(true);

    const updateSystemResult = await updateSystem(systemBodyWithDeclaration);

    handleResult(updateSystemResult);
    setIsLoading(false);
  };

  const addDeclaration = (
    values: PrivacyDeclaration,
    formikHelpers: FormikHelpers<PrivacyDeclaration>
  ) => {
    const { resetForm } = formikHelpers;
    if (formDeclarations.filter((d) => d.name === values.name).length > 0) {
      toast({
        status: "error",
        description:
          "A declaration already exists with that name in this system. Please use a different name.",
      });
    } else {
      toast.closeAll();
      setFormDeclarations([
        ...formDeclarations,
        transformFormValuesToDeclaration(values),
      ]);
      resetForm({
        values: {
          name: "",
          data_subjects: [],
          data_categories: [],
          data_use: "",
          data_qualifier: "",
        },
      });
    }
  };

  return (
    <Formik
      enableReinitialize
      initialValues={initialValues}
      onSubmit={addDeclaration}
      validationSchema={ValidationSchema}
    >
      {({ dirty }) => (
        <Form data-testid="privacy-declaration-form">
          <Stack spacing={10}>
            <Heading as="h3" size="lg">
              {/* TODO FUTURE: Path when describing system from infra scanning */}
              Privacy Declaration for {system.name}
            </Heading>
            <div>
              Now we’re going to declare our system’s privacy characteristics.
              Think of this as explaining who’s data the system is processing,
              what kind of data it’s processing and for what purpose it’s using
              that data and finally, how identifiable is the user with this
              data.
            </div>
            {formDeclarations.map((declaration) => (
              <Fragment key={declaration.name}>
                <PrivacyDeclarationAccordion privacyDeclaration={declaration} />
                <Divider m="0px !important" />
              </Fragment>
            ))}
            <Stack spacing={4}>
              <CustomTextInput
                name="name"
                label="Declaration name"
                tooltip="A system may have multiple privacy declarations, so each declaration should have a name to distinguish them clearly."
              />
              <CustomMultiSelect
                name="data_categories"
                label="Data categories"
                options={allDataCategories?.map((data) => ({
                  value: data.fides_key,
                  label: data.fides_key,
                }))}
                tooltip="What type of data is your system processing? This could be various types of user or system data."
              />
              <CustomSelect
                id="data_use"
                label="Data use"
                name="data_use"
                options={allDataUses.map((data) => ({
                  value: data.fides_key,
                  label: data.fides_key,
                }))}
                tooltip="What is the system using the data for. For example, is it for third party advertising or perhaps simply providing system operations."
              />
              <CustomMultiSelect
                name="data_subjects"
                label="Data subjects"
                options={allDataSubjects.map((data) => ({
                  value: data.fides_key,
                  label: data.fides_key,
                }))}
                tooltip="Whose data are you processing? This could be customers, employees or any other type of user in your system."
              />
              <CustomSelect
                id="data_qualifier"
                label="Data qualifier"
                name="data_qualifier"
                options={allDataQualifiers.map((data) => ({
                  value: data.fides_key,
                  label: data.fides_key,
                }))}
                tooltip="How identifiable is the user in the data in this system? For instance, is it anonymized data where the user is truly unknown/unidentifiable, or it is partially identifiable data?"
              />
            </Stack>
            <Box>
              <Button
                type="submit"
                colorScheme="purple"
                variant="link"
                disabled={!dirty}
                isLoading={isLoading}
                data-testid="add-btn"
              >
                Add <AddIcon boxSize={10} />
              </Button>
            </Box>
            <Box>
              <Button
                onClick={onCancel}
                mr={2}
                size="sm"
                variant="outline"
                data-testid="cancel-btn"
              >
                Cancel
              </Button>
              <Button
                colorScheme="primary"
                size="sm"
                disabled={formDeclarations.length === 0}
                isLoading={isLoading}
                data-testid="next-btn"
                onClick={handleSubmit}
              >
                Next
              </Button>
            </Box>
          </Stack>
        </Form>
      )}
    </Formik>
  );
};

export default PrivacyDeclarationForm;
