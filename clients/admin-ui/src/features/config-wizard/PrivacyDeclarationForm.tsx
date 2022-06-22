import {
  Accordion,
  AccordionButton,
  AccordionIcon,
  AccordionItem,
  AccordionPanel,
  Box,
  Button,
  Divider,
  Heading,
  HStack,
  Input,
  Stack,
  Tag,
  Text,
  Tooltip,
  useToast,
} from "@fidesui/react";
import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/dist/query/fetchBaseQuery";
import { Form, Formik } from "formik";
import type { NextPage } from "next";
import React, { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";

import { AddIcon, QuestionIcon } from "~/features/common/Icon";
import {
  selectDataQualifier,
  setDataQualifier,
  useGetDataQualifierQuery,
} from "~/features/data-qualifier/data-qualifier.slice";
import {
  selectDataSubjects,
  setDataSubjects,
  useGetAllDataSubjectsQuery,
} from "~/features/data-subjects/data-subject.slice";
import {
  selectDataUse,
  setDataUse,
  useGetDataUseQuery,
} from "~/features/data-use/data-use.slice";
import { PrivacyDeclaration } from "~/features/system/types";
import {
  selectDataCategories,
  setDataCategories,
  useGetAllDataCategoriesQuery,
} from "~/features/taxonomy/data-categories.slice";

import {
  CustomMultiSelect,
  CustomSelect,
  CustomTextInput,
} from "../common/form/inputs";
import { isErrorWithDetail, isErrorWithDetailArray } from "../common/helpers";
import {
  useGetSystemByFidesKeyQuery,
  useUpdateSystemMutation,
} from "../system/system.slice";

type FormValues = Partial<PrivacyDeclaration>;

const PrivacyDeclarationForm: NextPage<{
  handleChangeReviewStep: Function;
  handleCancelSetup: Function;
  systemFidesKey: string;
}> = ({ handleCancelSetup, handleChangeReviewStep, systemFidesKey }) => {
  const { data: existingSystem } = useGetSystemByFidesKeyQuery(systemFidesKey);
  const dispatch = useDispatch();
  const toast = useToast();
  const [formDeclarations, setFormDeclarations] = useState<any>(
    existingSystem && existingSystem?.privacy_declarations
      ? [...existingSystem.privacy_declarations]
      : []
  );
  const [updateSystem] = useUpdateSystemMutation();
  const [isLoading, setIsLoading] = useState(false);

  const { data: dataCategories } = useGetAllDataCategoriesQuery();
  const { data: dataSubjects } = useGetAllDataSubjectsQuery();
  const { data: dataQualifier } = useGetDataQualifierQuery();
  const { data: dataUse } = useGetDataUseQuery();

  const allDataCategories = useSelector(selectDataCategories);
  const allDataSubjects = useSelector(selectDataSubjects);
  const allDataUses = useSelector(selectDataUse);
  const allDataQualifiers = useSelector(selectDataQualifier);

  useEffect(() => {
    dispatch(setDataCategories(dataCategories ?? []));
    dispatch(setDataSubjects(dataSubjects ?? []));
    dispatch(setDataUse(dataUse ?? []));
    dispatch(setDataQualifier(dataQualifier ?? []));
  }, [dispatch, dataCategories, dataSubjects, dataUse, dataQualifier]);

  useEffect(() => {}, [formDeclarations]);

  const initialValues = {
    data_categories: [],
    data_subjects: [],
    data_use: "",
    data_qualifier: "",
  };

  let privacyDeclarations: any;

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
      fides_key: existingSystem?.fides_key ?? "default_organization",
      name: existingSystem?.name,
      privacy_declarations: Array.from(new Set([...privacyDeclarations])),
      system_type: existingSystem?.system_type,
      system_dependencies: existingSystem?.system_dependencies,
    };

    const handleResult = (
      result: { data: {} } | { error: FetchBaseQueryError | SerializedError }
    ) => {
      if ("error" in result) {
        let errorMsg =
          "An unexpected error occurred while creating system. Please try again.";
        if (isErrorWithDetail(result.error)) {
          errorMsg = result.error.data.detail;
        } else if (isErrorWithDetailArray(result.error)) {
          const { error } = result;
          errorMsg = error.data.detail[0].msg;
        }
        toast({
          status: "error",
          description: errorMsg,
        });
      } else {
        toast.closeAll();
        handleChangeReviewStep(2);
      }
    };

    setIsLoading(true);

    const updateSystemResult = await updateSystem(systemBodyWithDeclaration);

    handleResult(updateSystemResult);
    setIsLoading(false);
  };

  const addAnotherDeclaration = (values: any) => {
    if (
      values.name === "" ||
      formDeclarations.filter((d: any) => d.name === values.name).length > 0 ||
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
    >
      {({ resetForm, values }) => (
        <Form>
          <Stack ml="100px" spacing={10}>
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
              ? formDeclarations.map((declaration: any) => (
                  <>
                    <Accordion
                      allowToggle
                      border="transparent"
                      key={declaration.name}
                      m="5px !important"
                      maxW="500px"
                      minW="500px"
                      width="500px"
                    >
                      <AccordionItem>
                        <>
                          <AccordionButton pr="0px" pl="0px">
                            <Box flex="1" textAlign="left">
                              {declaration.name}
                            </Box>
                            <AccordionIcon />
                          </AccordionButton>
                          <AccordionPanel padding="0px" mt="20px">
                            <HStack mb="20px">
                              <Text color="gray.600">
                                Declaration categories
                              </Text>
                              {declaration.data_categories.map(
                                (category: any) => (
                                  <Tag
                                    background="primary.400"
                                    color="white"
                                    key={category}
                                    width="fit-content"
                                  >
                                    {category}
                                  </Tag>
                                )
                              )}
                            </HStack>
                            <HStack mb="20px">
                              <Text color="gray.600">Data use</Text>
                              <Input disabled value={declaration.data_use} />
                            </HStack>
                            <HStack mb="20px">
                              <Text color="gray.600">Data subjects</Text>
                              {declaration.data_subjects.map((subject: any) => (
                                <Tag
                                  background="primary.400"
                                  color="white"
                                  key={subject}
                                  width="fit-content"
                                >
                                  {subject}
                                </Tag>
                              ))}
                            </HStack>
                            <HStack mb="20px">
                              <Text color="gray.600">Data qualifier</Text>
                              <Input
                                disabled
                                value={declaration.data_qualifier}
                              />
                            </HStack>
                          </AccordionPanel>
                        </>
                      </AccordionItem>
                    </Accordion>
                    <Divider m="0px !important" />
                  </>
                ))
              : null}
            <Stack>
              <Stack direction="row" mb={5}>
                <CustomTextInput name="name" label="Declaration name" />
                <Tooltip
                  fontSize="md"
                  label="A system may have multiple privacy declarations, so each declaration should have a name to distinguish them clearly."
                  placement="right"
                >
                  <QuestionIcon boxSize={5} color="gray.400" />
                </Tooltip>
              </Stack>

              <Stack direction="row" mb={5}>
                <CustomMultiSelect
                  isClearable
                  name="data_categories"
                  label="Data categories"
                  options={allDataCategories?.map((data) => ({
                    value: data.fides_key,
                    label: data.fides_key,
                  }))}
                  size="md"
                />
                <Tooltip
                  fontSize="md"
                  label="What type of data is your system processing? This could be various types of user or system data."
                  placement="right"
                >
                  <QuestionIcon boxSize={5} color="gray.400" />
                </Tooltip>
              </Stack>
            </Stack>

            <Stack direction="row" mb={5}>
              <CustomSelect
                id="data_use"
                label="Data use"
                name="data_use"
                size="md"
                options={allDataUses?.map((data: any) => ({
                  value: data.fides_key,
                  label: data.fides_key,
                }))}
              />
              <Tooltip
                fontSize="md"
                label="What is the system using the data for. For example, is it for third party advertising or perhaps simply providing system operations."
                placement="right"
              >
                <QuestionIcon boxSize={5} color="gray.400" />
              </Tooltip>
            </Stack>

            <Stack direction="row" mb={5}>
              <CustomMultiSelect
                isClearable
                name="data_subjects"
                label="Data subjects"
                size="md"
                options={allDataSubjects?.map((data: any) => ({
                  value: data.fides_key,
                  label: data.fides_key,
                }))}
              />
              <Tooltip
                fontSize="md"
                label="Who’s data are you processing? This could be customers, employees or any other type of user in your system."
                placement="right"
              >
                <QuestionIcon boxSize={5} color="gray.400" />
              </Tooltip>
            </Stack>

            <Stack direction="row">
              <CustomSelect
                id="data_qualifier"
                label="Data qualifier"
                name="data_qualifier"
                size="md"
                options={allDataQualifiers?.map((data: any) => ({
                  value: data.fides_key,
                  label: data.fides_key,
                }))}
              />
              <Tooltip
                fontSize="md"
                label="How identifiable is the user in the data in this system? For instance, is it anonymized data where the user is truly unknown/unidentifiable, or it is partially identifiable data?"
                placement="right"
              >
                <QuestionIcon boxSize={5} color="gray.400" />
              </Tooltip>
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
                onClick={() => handleCancelSetup()}
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
                disabled={
                  (!values.data_use ||
                    !values.data_qualifier ||
                    !values.data_subjects ||
                    !values.data_categories) &&
                  formDeclarations.length === 0
                }
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
