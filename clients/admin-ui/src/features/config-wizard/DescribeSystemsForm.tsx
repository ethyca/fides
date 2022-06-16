import {
  Box,
  Button,
  chakra,
  FormControl,
  FormLabel,
  Heading,
  Input,
  Stack,
  Tooltip,
} from "@fidesui/react";
import { ChakraStylesConfig, CreatableSelect } from "chakra-react-select";
import { useFormik } from "formik";
import type { NextPage } from "next";
import React, { useState } from "react";
import { QuestionIcon } from "~/features/common/Icon";
import HorizontalStepper from "../common/HorizontalStepper";
import { HORIZONTALSTEPS } from "./constants";

//   import { useCreateOrganizationMutation } from "./organization.slice";

const useDescribeSystemsForm = () =>
  // handleChangeStep: Function
  {
    // const [createOrganization] = useCreateOrganizationMutation();
    const [isLoading, setIsLoading] = useState(false);
    // const toast = useToast();
    const formik = useFormik({
      initialValues: {
        name: "",
        key: "",
        description: "",
        type: "",
        tags: [],
      },
      onSubmit: async () =>
        // values
        {
          // const systemBody = {
          //   name: values.name,
          //   key: values.key,
          //   description: values.description,
          //   type: values.type,
          //   tags: values.tags,
          // };
          setIsLoading(true);

          // @ts-ignore
          // const { error: createSystemError } =
          // await createOrganization(
          //   systemBody
          // );

          setIsLoading(false);

          // if (createSystemError) {
          //   toast({
          //     status: "error",
          //     description: "Creating system failed.",
          //   });
          // } else {
          //   handleChangeStep(...);
          //   toast.closeAll();
          // }
        },
      validate: (values) => {
        const errors: {
          name?: string;
          key?: string;
          description?: string;
          type?: string;
          tags?: string[];
        } = {};

        if (!values.name) {
          errors.name = "System name is required";
        }

        if (!values.key) {
          errors.key = "System key is equired";
        }

        if (!values.description) {
          errors.description = "System description is equired";
        }

        if (!values.type) {
          errors.type = "System type is required";
        }

        return errors;
      },
    });

    return { ...formik, isLoading };
  };

const DescribeSystemsForm: NextPage<{
  handleChangeStep: Function;
  handleCancelSetup: Function;
}> = ({ handleChangeStep, handleCancelSetup }) => {
  const {
    errors,
    handleBlur,
    handleChange,
    handleSubmit,
    isLoading,
    touched,
    values,
  } = useDescribeSystemsForm();
  //   handleChangeStep

  const chakraStyles: ChakraStylesConfig = {
    container: (provided, state) => ({
      ...provided,
      width: "65%",
      maxWidth: "65%",
    }),
    dropdownIndicator: (provided, state) => ({
      ...provided,
      background: "white",
    }),
    multiValue: (provided, state) => ({
      ...provided,
      background: "primary.400",
      color: "white",
    }),
    multiValueRemove: (provided, state) => ({
      ...provided,
      display: "none",
      visibility: "hidden",
    }),
  };

  return (
    <chakra.form onSubmit={handleSubmit} w="100%">
      <Stack ml="100px" spacing={10}>
        <HorizontalStepper activeStep={1} steps={HORIZONTALSTEPS} />
        <Heading as="h3" size="lg">
          {/* If describing system manually */}
          Describe your system
        </Heading>
        <div>
          By providing a small amount of additional context for each system we
          can make reporting and understanding our tech stack much easier for
          everyone from engineering to legal teams. So let’s do this now.
        </div>
        <Stack>
          <FormControl>
            <Stack direction="row" mb={5} justifyContent="flex-end">
              <FormLabel>System name</FormLabel>
              <Input
                type="text"
                id="name"
                name="name"
                focusBorderColor="gray.700"
                onChange={handleChange}
                onBlur={handleBlur}
                value={values.name}
                isInvalid={touched.name && Boolean(errors.name)}
                minW="65%"
                w="65%"
              />
              <Tooltip
                fontSize="md"
                label="Give the system a unique, and relevant name for reporting purposes. e.g. “Email Data Warehouse”"
                placement="right"
              >
                <QuestionIcon boxSize={5} color="gray.400" />
              </Tooltip>
            </Stack>

            {values.name ? (
              <Stack direction="row" mb={5} justifyContent="flex-end">
                <FormLabel>System key</FormLabel>
                <Input
                  type="text"
                  id="key"
                  name="key"
                  focusBorderColor="gray.700"
                  onChange={handleChange}
                  onBlur={handleBlur}
                  value={values.key}
                  isInvalid={touched.key && Boolean(errors.key)}
                  minW="65%"
                  w="65%"
                />
                <Tooltip
                  fontSize="md"
                  label="System key’s are automatically generated from the resource id and system name to provide a unique key for identifying systems in the registry."
                  placement="right"
                >
                  <QuestionIcon boxSize={5} color="gray.400" />
                </Tooltip>
              </Stack>
            ) : null}

            {values.key ? (
              <Stack direction="row" mb={5} justifyContent="flex-end">
                <FormLabel>Description</FormLabel>
                <Input
                  type="text"
                  id="description"
                  name="description"
                  focusBorderColor="gray.700"
                  onChange={handleChange}
                  onBlur={handleBlur}
                  value={values.description}
                  isInvalid={touched.description && Boolean(errors.description)}
                  minW="65%"
                  w="65%"
                />
                <Tooltip
                  fontSize="md"
                  label="If you wish you can provide a description which better explains the purpose of this system."
                  placement="right"
                >
                  <QuestionIcon boxSize={5} color="gray.400" />
                </Tooltip>
              </Stack>
            ) : null}

            {values.description ? (
              <Stack direction="row" mb={5} justifyContent="flex-end">
                <FormLabel>System type</FormLabel>
                <CreatableSelect
                  isClearable
                  id="type"
                  name="type"
                  chakraStyles={chakraStyles}
                  size="md"
                />
                <Tooltip
                  fontSize="md"
                  label="Select a system type from the pre-approved list of system types."
                  placement="right"
                >
                  <QuestionIcon boxSize={5} color="gray.400" />
                </Tooltip>
              </Stack>
            ) : null}

            {/* this seems to have changed in the designs and also values.types is nothing */}
            {/* {values.type ? ( */}
            <Stack direction="row" mb={5} justifyContent="flex-end">
              <FormLabel>System tags</FormLabel>
              <CreatableSelect
                isMulti
                isClearable
                id="tags"
                name="tags"
                noOptionsMessage={() => null}
                placeholder="Add your system tags"
                components={{
                  Menu: () => null,
                  DropdownIndicator: () => null,
                }}
                chakraStyles={chakraStyles}
                size="md"
              />
              <Tooltip
                fontSize="md"
                label="Provide one or more tags to group the system. Tags are important as they allow you to filter and group systems for reporting and later review. Tags provide tremendous value as you scale - imagine you have thousands of systems, you’re going to thank us later for tagging!"
                placement="right"
              >
                <QuestionIcon boxSize={5} color="gray.400" />
              </Tooltip>
            </Stack>
            {/* ) : null} */}
          </FormControl>
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
            disabled={
              !values.name || !values.description || !values.key
              // !values.type ||
              // !values.tags
            }
            isLoading={isLoading}
          >
            Confirm and Continue
          </Button>
        </Box>
      </Stack>
    </chakra.form>
  );
};
export default DescribeSystemsForm;
