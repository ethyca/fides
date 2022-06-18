import { Box, Button, Heading, Stack, Tooltip, useToast } from "@fidesui/react";
import { Form, Formik } from "formik";
import type { NextPage } from "next";
import React, { useState } from "react";

import { QuestionIcon } from "~/features/common/Icon";

import {
  CustomCreatableMultiSelect,
  CustomCreatableSingleSelect,
  CustomTextInput,
} from "../common/form/inputs";
import HorizontalStepper from "../common/HorizontalStepper";
import {
  useCreateSystemMutation,
  useGetSystemByFidesKeyQuery,
  useUpdateSystemMutation,
} from "../system/system.slice";
import { System } from "../system/types";
import { HORIZONTAL_STEPS } from "./constants";

type FormValues = Partial<System>;

const DescribeSystemsForm: NextPage<{
  handleChangeStep: Function;
  handleCancelSetup: Function;
}> = ({ handleCancelSetup, handleChangeStep }) => {
  const [updateSystem] = useUpdateSystemMutation();
  const [createSystem] = useCreateSystemMutation();
  const [isLoading, setIsLoading] = useState(false);
  // TODO FUTURE: Need a way to check for an existing fides key from the start of the wizard
  // not just use this default
  const { data: existingSystem } = useGetSystemByFidesKeyQuery(
    "default_organization"
  );

  const toast = useToast();

  // TODO FUTURE: is key stored? If so, where does it exist in the system API?
  const initialValues = {
    name: existingSystem?.name ?? "",
    description: existingSystem?.description ?? "",
    system_dependencies: existingSystem?.system_dependencies ?? [],
    system_type: existingSystem?.system_type ?? "",
  };

  const handleSubmit = async (values: FormValues) => {
    const systemBody = {
      fides_key: existingSystem?.fides_key ?? "default_organization",
      name: values.name ?? existingSystem?.name,
      description: values.description ?? existingSystem?.description,
      privacy_declarations: existingSystem?.privacy_declarations ?? [
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
      system_type: values.system_type ?? existingSystem?.system_type,
      system_dependencies:
        values.system_dependencies ?? existingSystem?.system_dependencies,
      // TODO: tags = system_dependencies?
    };

    setIsLoading(true);

    if (!existingSystem) {
      // @ts-ignore
      const { error: createSystemError } = await createSystem(systemBody);

      if (createSystemError) {
        toast({
          status: "error",
          description: "Creating system failed.",
        });
      } else {
        toast.closeAll();
        handleChangeStep(5);
      }
    } else {
      // @ts-ignore
      const { error: updateSystemError } = await updateSystem(systemBody);

      if (updateSystemError) {
        toast({
          status: "error",
          description: "Updating system failed.",
        });
      } else {
        toast.closeAll();
        handleChangeStep(5);
      }
    }

    setIsLoading(false);
  };

  return (
    <Formik
      initialValues={initialValues}
      enableReinitialize
      onSubmit={handleSubmit}
    >
      <Form>
        <Stack ml="100px" spacing={10}>
          <HorizontalStepper activeStep={1} steps={HORIZONTAL_STEPS} />
          <Heading as="h3" size="lg">
            {/* TODO FUTURE: Path when describing system from infra scanning */}
            Describe your system
          </Heading>
          <div>
            By providing a small amount of additional context for each system we
            can make reporting and understanding our tech stack much easier for
            everyone from engineering to legal teams. So let’s do this now.
          </div>
          <Stack>
            <Stack direction="row">
              <CustomTextInput name="name" label="System name" />
              <Tooltip
                fontSize="md"
                label="Give the system a unique, and relevant name for reporting purposes. e.g. “Email Data Warehouse”"
                placement="right"
              >
                <QuestionIcon boxSize={5} color="gray.400" />
              </Tooltip>
            </Stack>

            <Stack direction="row" mb={5}>
              <CustomTextInput name="key" label="System key" />
              <Tooltip
                fontSize="md"
                label="System key’s are automatically generated from the resource id and system name to provide a unique key for identifying systems in the registry."
                placement="right"
              >
                <QuestionIcon boxSize={5} color="gray.400" />
              </Tooltip>
            </Stack>

            <Stack direction="row" mb={5}>
              <CustomTextInput name="description" label="System description" />
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
                isClearable
                id="system_type"
                label="System Type"
                name="system_type"
                options={[
                  { label: "system_type", value: initialValues.system_type },
                ]}
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
                name="system_dependencies"
                label="System Tags"
                options={initialValues.system_dependencies}
                isMulti
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
export default DescribeSystemsForm;
