import { Box, Button, Heading, Stack, Tooltip, useToast } from "@fidesui/react";
import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/dist/query/fetchBaseQuery";
import { Form, Formik } from "formik";
import React, { useState } from "react";

import { useAppDispatch } from "~/app/hooks";
import { QuestionIcon } from "~/features/common/Icon";
import { DEFAULT_ORGANIZATION_FIDES_KEY } from "~/features/organization";
import { System } from "~/types/api";

import {
  CustomCreatableMultiSelect,
  CustomCreatableSingleSelect,
  CustomTextInput,
} from "../common/form/inputs";
import { isErrorWithDetail, isErrorWithDetailArray } from "../common/helpers";
import { useCreateSystemMutation } from "../system/system.slice";
import { changeReviewStep, setSystemFidesKey } from "./config-wizard.slice";

type FormValues = Partial<System>;

const DescribeSystemsForm = ({
  handleCancelSetup,
}: {
  handleCancelSetup: () => void;
}) => {
  const dispatch = useAppDispatch();

  const [createSystem] = useCreateSystemMutation();
  const [isLoading, setIsLoading] = useState(false);

  const toast = useToast();

  const initialValues = {
    description: "",
    fides_key: "",
    name: "",
    organization_fides_key: DEFAULT_ORGANIZATION_FIDES_KEY,
    tags: [],
    system_type: "",
  };

  const handleSubmit = async (values: FormValues) => {
    const systemBody = {
      description: values.description,
      fides_key: values.fides_key,
      name: values.name,
      organization_fides_key: DEFAULT_ORGANIZATION_FIDES_KEY,
      privacy_declarations: [
        {
          name: "string",
          data_categories: ["string"],
          data_use: "string",
          data_qualifier:
            "aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified",
          data_subjects: ["string"],
          dataset_references: ["string"],
        },
      ],
      system_type: values.system_type,
      // QUESTION(allisonking): should this be using the system tags now in fideslang 1.1.0?
      meta: { tags: values.tags?.toString() ?? "" },
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
        dispatch(setSystemFidesKey(values.fides_key ?? ""));
        dispatch(changeReviewStep());
      }
    };

    setIsLoading(true);

    const createSystemResult = await createSystem(systemBody);
    handleResult(createSystemResult);

    setIsLoading(false);
  };

  return (
    <Formik
      initialValues={initialValues}
      enableReinitialize
      onSubmit={handleSubmit}
    >
      {({ values }) => (
        <Form>
          <Stack spacing={10}>
            <Heading as="h3" size="lg">
              {/* TODO FUTURE: Path when describing system from infra scanning */}
              Describe your system
            </Heading>
            <div>
              By providing a small amount of additional context for each system
              we can make reporting and understanding our tech stack much easier
              for everyone from engineering to legal teams. So let’s do this
              now.
            </div>
            <Stack>
              <Stack direction="row">
                <CustomTextInput id="name" name="name" label="System name" />
                <Tooltip
                  fontSize="md"
                  label="Give the system a unique, and relevant name for reporting purposes. e.g. “Email Data Warehouse”"
                  placement="right"
                >
                  <QuestionIcon boxSize={5} color="gray.400" />
                </Tooltip>
              </Stack>

              <Stack direction="row" mb={5}>
                <CustomTextInput
                  id="fides_key"
                  name="fides_key"
                  label="System key"
                />
                <Tooltip
                  fontSize="md"
                  // TODO FUTURE: This tooltip text is misleading since at the moment for MVP we are manually creating a fides key for this resource
                  label="System key’s are automatically generated from the resource id and system name to provide a unique key for identifying systems in the registry."
                  placement="right"
                >
                  <QuestionIcon boxSize={5} color="gray.400" />
                </Tooltip>
              </Stack>

              <Stack direction="row" mb={5}>
                <CustomTextInput
                  id="description"
                  name="description"
                  label="System description"
                />
                <Tooltip
                  fontSize="md"
                  label="If you wish you can provide a description which better explains the purpose of this system."
                  placement="right"
                >
                  <QuestionIcon boxSize={5} color="gray.400" />
                </Tooltip>
              </Stack>

              <Stack direction="row" mb={5}>
                <CustomCreatableSingleSelect
                  id="system_type"
                  label="System Type"
                  name="system_type"
                  options={
                    initialValues.system_type
                      ? [
                          {
                            label: initialValues.system_type,
                            value: initialValues.system_type,
                          },
                        ]
                      : []
                  }
                />
                <Tooltip
                  fontSize="md"
                  label="Select a system type from the pre-approved list of system types."
                  placement="right"
                >
                  <QuestionIcon boxSize={5} color="gray.400" />
                </Tooltip>
              </Stack>

              <Stack direction="row" mb={5}>
                <CustomCreatableMultiSelect
                  id="tags"
                  name="tags"
                  label="System Tags"
                  options={initialValues.tags.map((s: any) => ({
                    value: s,
                    label: s,
                  }))}
                />
                <Tooltip
                  fontSize="md"
                  label="Provide one or more tags to group the system. Tags are important as they allow you to filter and group systems for reporting and later review. Tags provide tremendous value as you scale - imagine you have thousands of systems, you’re going to thank us later for tagging!"
                  placement="right"
                >
                  <QuestionIcon boxSize={5} color="gray.400" />
                </Tooltip>
              </Stack>
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
                variant="primary"
                size="sm"
                isDisabled={
                  !values.name || !values.description || !values.system_type
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
export default DescribeSystemsForm;
