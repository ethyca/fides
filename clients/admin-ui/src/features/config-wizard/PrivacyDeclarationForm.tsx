import { Box, Button, Heading, Stack, Tooltip, useToast } from "@fidesui/react";
import { Form, Formik } from "formik";
import type { NextPage } from "next";
import React, { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { QuestionIcon } from "~/features/common/Icon";
import {
  selectDataQualifier,
  setDataQualifier,
  useGetDataQualifierQuery,
} from "~/features/data-qualifier/data-qualifier.slice";
import {
  selectDataSubjects,
  setDataSubjects,
  useGetAllDataSubjectsQuery,
} from "~/features/data-subjects/data-subjects.slice";
import {
  selectDataUse,
  setDataUse,
  useGetDataUseQuery,
} from "~/features/data-use/data-use.slice";
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
import {
  useGetSystemByFidesKeyQuery,
  useUpdateSystemMutation,
} from "../system/system.slice";
import { System } from "../system/types";

type FormValues = Partial<System>;

const PrivacyDeclarationForm: NextPage<{
  handleChangeStep: Function;
  handleChangeReviewStep: Function;
  handleCancelSetup: Function;
}> = ({ handleCancelSetup, handleChangeStep, handleChangeReviewStep }) => {
  const [updateSystem] = useUpdateSystemMutation();
  const [isLoading, setIsLoading] = useState(false);
  // TODO FUTURE: Need a way to check for an existing fides key from the start of the wizard
  // not just use this default
  const { data: existingSystem } = useGetSystemByFidesKeyQuery(
    "default_organization"
  );
  const { data: dataCategories } = useGetAllDataCategoriesQuery();
  const { data: dataSubjects } = useGetAllDataSubjectsQuery();
  const { data: dataQualifier } = useGetDataQualifierQuery();
  const { data: dataUse } = useGetDataUseQuery();

  const dispatch = useDispatch();
  const toast = useToast();

  useEffect(() => {
    dispatch(setDataCategories(dataCategories ?? []));
    dispatch(setDataSubjects(dataSubjects ?? []));
    dispatch(setDataUse(dataUse ?? ""));
    dispatch(setDataQualifier(dataQualifier ?? ""));
  }, [dispatch, dataCategories, dataSubjects, dataUse, dataQualifier]);

  const initialValues = {
    privacy_declarations: existingSystem?.privacy_declarations ?? [],
  };

  const handleSubmit = async (values: FormValues) => {
    const systemBody = {
      fides_key: existingSystem?.fides_key ?? "default_organization",
      //   privacy_declarations:
    };

    setIsLoading(true);

    // @ts-ignore
    const { error: updateSystemError } = await updateSystem(systemBody);

    if (updateSystemError) {
      toast({
        status: "error",
        description: "Updating system failed.",
      });
    } else {
      toast.closeAll();
      // change step or go to next horizontal step?
      // handleChangeStep(6);
      // handleChangeReviewStep(2);
    }
    setIsLoading(false);
  };

  const allDataCategories = useSelector(selectDataCategories);
  const allDataSubjects = useSelector(selectDataSubjects);
  const singleDataUse = useSelector(selectDataUse);
  const singleDataQualifier = useSelector(selectDataQualifier);

  console.log("allDataCategories", allDataCategories);
  console.log("allDataSubjects", allDataSubjects);
  console.log("singleDataUse", singleDataUse);
  console.log("singleDataQualifier", singleDataQualifier);

  return (
    <Formik initialValues={initialValues} onSubmit={handleSubmit}>
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
            that data and finally, how identifiable is the user with this data.
          </div>
          <Stack>
            <Stack direction="row">
              <CustomTextInput name="name" label="Declaration name" />
              <Tooltip fontSize="md" label="..." placement="right">
                <QuestionIcon boxSize={5} color="gray.400" />
              </Tooltip>
            </Stack>

            <Stack direction="row" mb={5}>
              <CustomMultiSelect
                name="data_categories"
                label="Data categories"
                options={allDataCategories?.map((data) => ({
                  value: data.fides_key,
                  label: data.fides_key,
                }))}
                size="md"
              />
              <Tooltip fontSize="md" label="..." placement="right">
                <QuestionIcon boxSize={5} color="gray.400" />
              </Tooltip>
            </Stack>
          </Stack>

          <Stack direction="row" mb={5}>
            <CustomSelect
              isClearable
              id="data_use"
              label="Data use"
              name="data_use"
              size="md"
              options={[]}
            />
            <Tooltip fontSize="md" label="..." placement="right">
              <QuestionIcon boxSize={5} color="gray.400" />
            </Tooltip>
          </Stack>

          <Stack direction="row" mb={5}>
            <CustomMultiSelect
              name="data_subjects"
              label="Data subjects"
              size="md"
              options={[]}
            />
            <Tooltip fontSize="md" label="..." placement="right">
              <QuestionIcon boxSize={5} color="gray.400" />
            </Tooltip>
          </Stack>

          <Stack direction="row" mb={5}>
            <CustomSelect
              isClearable
              id="data_qualifier"
              label="Data qualifier"
              name="data_qualifier"
              size="md"
              options={[]}
            />
            <Tooltip fontSize="md" label="..." placement="right">
              <QuestionIcon boxSize={5} color="gray.400" />
            </Tooltip>
          </Stack>
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
              // disabled={}
              // TODO: Disable button if fields are empty
              isLoading={isLoading}
            >
              Confirm and Continue
            </Button>
          </Box>
        </Stack>
      </Form>
    </Formik>
  );
};

export default PrivacyDeclarationForm;
