import { Box, Button, Divider, Heading, Stack, useToast } from "@fidesui/react";
import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/dist/query/fetchBaseQuery";
import { Form, Formik } from "formik";
import React, { useEffect, useState } from "react";
import * as Yup from "yup";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { AddIcon } from "~/features/common/Icon";
import {
  selectDataQualifiers,
  setDataQualifiers,
  useGetAllDataQualifiersQuery,
} from "~/features/data-qualifier/data-qualifier.slice";
import {
  selectDataSubjects,
  setDataSubjects,
  useGetAllDataSubjectsQuery,
} from "~/features/data-subjects/data-subject.slice";
import {
  selectDataUses,
  setDataUses,
  useGetAllDataUsesQuery,
} from "~/features/data-use/data-use.slice";
import {
  selectDataCategories,
  setDataCategories,
  useGetAllDataCategoriesQuery,
} from "~/features/taxonomy/taxonomy.slice";
import { PrivacyDeclaration, System } from "~/types/api";

import {
  CustomMultiSelect,
  CustomSelect,
  CustomTextInput,
} from "../common/form/inputs";
import {
  useGetSystemByFidesKeyQuery,
  useUpdateSystemMutation,
} from "../system/system.slice";
import { changeReviewStep } from "./config-wizard.slice";
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

interface Props {
  systemKey: System["fides_key"];
  onCancel: () => void;
}

const PrivacyDeclarationForm = ({ systemKey, onCancel }: Props) => {
  const { data: existingSystem } = useGetSystemByFidesKeyQuery(systemKey);
  const dispatch = useAppDispatch();
  const toast = useToast();
  const [formDeclarations, setFormDeclarations] = useState<
    PrivacyDeclaration[]
  >(
    existingSystem && existingSystem?.privacy_declarations
      ? [...existingSystem.privacy_declarations]
      : []
  );
  const [updateSystem] = useUpdateSystemMutation();
  const [isLoading, setIsLoading] = useState(false);

  const { data: dataCategories } = useGetAllDataCategoriesQuery();
  const { data: dataSubjects } = useGetAllDataSubjectsQuery();
  const { data: dataQualifiers } = useGetAllDataQualifiersQuery();
  const { data: dataUses } = useGetAllDataUsesQuery();

  const allDataCategories = useAppSelector(selectDataCategories);
  const allDataSubjects = useAppSelector(selectDataSubjects);
  const allDataUses = useAppSelector(selectDataUses);
  const allDataQualifiers = useAppSelector(selectDataQualifiers);

  useEffect(() => {
    dispatch(setDataCategories(dataCategories ?? []));
    dispatch(setDataSubjects(dataSubjects ?? []));
    dispatch(setDataUses(dataUses ?? []));
    dispatch(setDataQualifiers(dataQualifiers ?? []));
  }, [dispatch, dataCategories, dataSubjects, dataUses, dataQualifiers]);

  const initialValues = {
    name: "",
    data_categories: [],
    data_subjects: [],
    data_use: "",
    data_qualifier: "",
  };

  let privacyDeclarations: PrivacyDeclaration[];

  const handleSubmit = async (values: FormValues) => {
    const handlePrivacyDeclarations = () => {
      const filteredDeclarations =
        existingSystem && existingSystem.privacy_declarations
          ? existingSystem?.privacy_declarations.filter(
              (declaration) => declaration.name !== "string"
            )
          : [];
      // If the declaration already exists
      if (
        filteredDeclarations &&
        filteredDeclarations.filter(
          (declaration) => declaration.name === values.name
        ).length > 0
      ) {
        privacyDeclarations = [...filteredDeclarations, ...formDeclarations];
      }
      // If the declaration does not exist
      else {
        privacyDeclarations = [
          ...filteredDeclarations,
          ...formDeclarations,
          {
            name: values.name,
            data_categories: values.data_categories,
            data_use: values.data_use,
            data_qualifier: values.data_qualifier,
            data_subjects: values.data_subjects,
            dataset_references: ["string"],
          },
        ];
      }
    };

    handlePrivacyDeclarations();

    const systemBodyWithDeclaration = {
      description: existingSystem?.description,
      // QUESTION(ssangervasi): This doesn't look like the intended default. What should it be?
      fides_key: existingSystem?.fides_key ?? "default_organization",
      name: existingSystem?.name,
      privacy_declarations: Array.from(new Set([...privacyDeclarations])),
      system_type: existingSystem?.system_type,
      meta: existingSystem?.meta,
    };

    const handleResult = (
      result: { data: {} } | { error: FetchBaseQueryError | SerializedError }
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
        dispatch(changeReviewStep());
      }
    };

    setIsLoading(true);

    const updateSystemResult = await updateSystem(systemBodyWithDeclaration);

    handleResult(updateSystemResult);
    setIsLoading(false);
  };

  const addAnotherDeclaration = (values: PrivacyDeclaration) => {
    if (
      values.name === "" ||
      formDeclarations.filter((d) => d.name === values.name).length > 0 ||
      (existingSystem &&
        existingSystem?.privacy_declarations &&
        existingSystem?.privacy_declarations?.filter(
          (d) => d.name === values.name
        ).length > 0)
    ) {
      toast({
        status: "error",
        description:
          "A declaration already exists with that name in this system. Please use a different name.",
      });
    } else {
      toast.closeAll();
      const declarationToSet = { ...values, dataset_references: ["string"] };
      setFormDeclarations([...formDeclarations, declarationToSet]);
    }
  };

  return (
    <Formik
      enableReinitialize
      initialValues={initialValues}
      onSubmit={handleSubmit}
      validationSchema={ValidationSchema}
    >
      {({ resetForm, values, isValid, dirty }) => (
        <Form>
          <Stack spacing={10}>
            <Heading as="h3" size="lg">
              {/* TODO FUTURE: Path when describing system from infra scanning */}
              Privacy Declaration for {existingSystem?.name}
            </Heading>
            <div>
              Now we’re going to declare our system’s privacy characteristics.
              Think of this as explaining who’s data the system is processing,
              what kind of data it’s processing and for what purpose it’s using
              that data and finally, how identifiable is the user with this
              data.
            </div>
            {formDeclarations.length > 0
              ? formDeclarations.map((declaration) => (
                  <>
                    <PrivacyDeclarationAccordion
                      privacyDeclaration={declaration}
                    />
                    <Divider m="0px !important" />
                  </>
                ))
              : null}
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
            <Button
              colorScheme="purple"
              display="flex"
              justifyContent="flex-start"
              variant="link"
              disabled={
                !values.data_use ||
                !values.data_qualifier ||
                !values.data_subjects ||
                !values.data_categories
              }
              isLoading={isLoading}
              onClick={() => {
                addAnotherDeclaration(values);
                resetForm({
                  values: {
                    name: "",
                    data_subjects: [],
                    data_categories: [],
                    data_use: "",
                    data_qualifier: "",
                  },
                });
              }}
              width="40%"
            >
              Add another declaration <AddIcon boxSize={10} />{" "}
            </Button>
            <Box>
              <Button
                onClick={() => onCancel()}
                mr={2}
                size="sm"
                variant="outline"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                colorScheme="primary"
                size="sm"
                disabled={!(isValid && dirty)}
                isLoading={isLoading}
              >
                Confirm and Continue
              </Button>
            </Box>
          </Stack>
        </Form>
      )}
    </Formik>
  );
};

export default PrivacyDeclarationForm;
